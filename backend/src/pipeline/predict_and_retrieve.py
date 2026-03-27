from __future__ import annotations

import argparse
import joblib
import re
import time
from threading import Lock
from typing import Dict, Any, List

import pandas as pd

from src.rag.retrieve import retrieve_similar_incidents
from src.rag.retrieve import load_embedder, load_collection
from src.runtime_paths import get_chroma_db_dir, get_model_path


# ---------------- CONFIG ---------------- #

COLLECTION_NAME = "incident_memory"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------- RESOURCE CACHE ---------------- #

_CACHED_ML_MODEL = None
_CACHED_EMBEDDER = None
_CACHED_COLLECTION = None
_RESOURCE_LOCK = Lock()


# ---------------- LOAD ML MODEL ---------------- #

def load_ml_model():
    path = get_model_path()
    print(f"[INFO] Loading ML model from: {path}")
    return joblib.load(path)


def initialize_resources() -> None:
    global _CACHED_ML_MODEL, _CACHED_EMBEDDER, _CACHED_COLLECTION
    with _RESOURCE_LOCK:
        if _CACHED_ML_MODEL is None:
            _CACHED_ML_MODEL = load_ml_model()

        if _CACHED_EMBEDDER is None:
            _CACHED_EMBEDDER = load_embedder(EMBED_MODEL)

        if _CACHED_COLLECTION is None:
            _CACHED_COLLECTION = load_collection(str(get_chroma_db_dir()), COLLECTION_NAME)


def get_cached_resources():
    initialize_resources()
    return _CACHED_ML_MODEL, _CACHED_EMBEDDER, _CACHED_COLLECTION


# ---------------- PREDICT PRIORITY ---------------- #

def predict_priority(
    model,
    issue_description: str,
    ticket_type: str,
    queue: str,
) -> str:
    input_df = pd.DataFrame([{
        "issue_description": issue_description,
        "type": ticket_type,
        "queue": queue,
    }])

    prediction = model.predict(input_df)[0]
    return prediction


# ---------------- QUERY ENRICHMENT ---------------- #

def normalize_issue_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def extract_issue_signals(issue_description: str) -> List[str]:
    """
    Lightweight rule-based signal extraction for better retrieval.
    Simple, production-minded, no heavy NLP.
    """
    text = normalize_issue_text(issue_description)
    signals: List[str] = []

    # Authentication / login / lockout
    if any(term in text for term in ["login", "log in", "password", "auth", "authentication", "signin", "sign in"]):
        signals.extend(["login issue", "authentication issue"])

    if any(term in text for term in ["locked", "lockout", "failed login", "failed attempts"]):
        signals.extend(["account lockout", "failed login attempts", "authentication policy"])

    # Payment / billing
    if any(term in text for term in ["payment", "billing", "transaction", "gateway", "subscription"]):
        signals.extend(["payment processing", "billing issue", "payment gateway"])

    # Timeout / latency / performance
    if any(term in text for term in ["timeout", "timed out", "latency", "slow", "delay", "response time"]):
        signals.extend(["performance issue", "timeout", "response delay"])

    if "api" in text:
        signals.extend(["api issue", "api performance"])

    # Database
    if any(term in text for term in ["database", "db", "sql", "query", "connection pool"]):
        signals.extend(["database issue", "database load", "connection issue"])

    # Deployment / release / config
    if any(term in text for term in ["deployment", "deploy", "release", "update", "code change", "recent change"]):
        signals.extend(["deployment regression", "recent change impact", "configuration change"])

    # Crash / outage
    if any(term in text for term in ["crash", "down", "outage", "unavailable", "service interruption"]):
        signals.extend(["service outage", "application failure"])

    # Remove duplicates, preserve order
    deduped = []
    seen = set()
    for s in signals:
        if s not in seen:
            deduped.append(s)
            seen.add(s)

    return deduped


def build_query(issue_description: str, ticket_type: str, queue: str) -> str:
    """
    Build richer retrieval query using structured fields + extracted issue signals.
    """
    signals = extract_issue_signals(issue_description)
    signal_text = ", ".join(signals) if signals else "none"

    return f"""Issue: {issue_description}
Type: {ticket_type}
Queue: {queue}
Signals: {signal_text}"""


# ---------------- MAIN PIPELINE ---------------- #

def run_pipeline(
    issue_description: str,
    ticket_type: str,
    queue: str,
    top_k: int = 3,
    retrieval_enabled: bool = True,
    model=None,
    embedder=None,
    collection=None,
) -> Dict[str, Any]:

    print("\n" + "=" * 120)
    print("OPS DECISION ENGINE - PREDICT + RETRIEVE")
    print("=" * 120)

    # 1) Require preloaded ML model (provided by app resource manager)
    if model is None:
        raise RuntimeError("ML model is not loaded.")

    if retrieval_enabled and (embedder is None or collection is None):
        print("[WARN] Retrieval disabled because embedder/chroma collection is unavailable.")
        retrieval_enabled = False

    # 2) Predict priority
    ml_start = time.perf_counter()
    predicted_priority = predict_priority(
        model,
        issue_description,
        ticket_type,
        queue,
    )
    ml_elapsed_ms = (time.perf_counter() - ml_start) * 1000

    print(f"\n[RESULT] Predicted Priority: {predicted_priority}")

    query = ""
    retrieved: List[Dict[str, Any]] = []
    retrieval_elapsed_ms = 0.0
    if retrieval_enabled:
        # 3) Build enriched retrieval query
        query = build_query(issue_description, ticket_type, queue)
        print(f"[INFO] Retrieval Query:\n{query}\n")

        # 4) Retrieve incidents
        retrieval_start = time.perf_counter()
        retrieved = retrieve_similar_incidents(
            query=query,
            chroma_path=str(get_chroma_db_dir()),
            collection_name=COLLECTION_NAME,
            model_name=EMBED_MODEL,
            top_k=top_k,
            queue_filter=None,
            type_filter=None,
            embedder=embedder,
            collection=collection,
        )
        retrieval_elapsed_ms = (time.perf_counter() - retrieval_start) * 1000
    else:
        print("[WARN] Chroma retrieval skipped; running in fallback mode (ML + LLM).")

    return {
        "issue_description": issue_description,
        "type": ticket_type,
        "queue": queue,
        "predicted_priority": predicted_priority,
        "retrieved_incidents": retrieved,
        "retrieval_query": query,
        "timings_ms": {
            "ml_prediction": round(ml_elapsed_ms, 2),
            "retrieval_chroma": round(retrieval_elapsed_ms, 2),
        },
    }


# ---------------- CLI ---------------- #

def parse_args():
    parser = argparse.ArgumentParser(description="Predict priority + retrieve incidents")

    parser.add_argument("--issue", type=str, required=True)
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--queue", type=str, required=True)
    parser.add_argument("--top_k", type=int, default=3)

    return parser.parse_args()


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    args = parse_args()

    run_pipeline(
        issue_description=args.issue,
        ticket_type=args.type,
        queue=args.queue,
        top_k=args.top_k,
    )