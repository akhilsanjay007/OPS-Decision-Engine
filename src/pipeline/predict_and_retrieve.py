from __future__ import annotations

import argparse
import joblib
import pandas as pd
from typing import Dict, Any

from src.rag.retrieve import retrieve_similar_incidents


# ---------------- CONFIG ---------------- #

ML_MODEL_PATH = "artifacts/ml/priority_stage5_svm_pipeline.joblib"

CHROMA_PATH = "artifacts/rag/chroma_db"
COLLECTION_NAME = "incident_memory"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------- LOAD ML MODEL ---------------- #

def load_ml_model():
    print(f"[INFO] Loading ML model from: {ML_MODEL_PATH}")
    return joblib.load(ML_MODEL_PATH)


# ---------------- PREDICT PRIORITY ---------------- #

def predict_priority(
    model,
    issue_description: str,
    ticket_type: str,
    queue: str,
) -> str:
    """
    Predict priority using trained sklearn pipeline.
    MUST match training format (DataFrame with same columns).
    """

    input_df = pd.DataFrame([{
        "issue_description": issue_description,
        "type": ticket_type,
        "queue": queue,
    }])

    prediction = model.predict(input_df)[0]

    return prediction


# ---------------- BUILD QUERY ---------------- #

def build_query(issue_description: str, ticket_type: str, queue: str) -> str:
    """
    Build richer query for retrieval (adds structured context).
    """
    return f"""
Issue: {issue_description}
Type: {ticket_type}
Queue: {queue}
"""


# ---------------- MAIN PIPELINE ---------------- #

def run_pipeline(
    issue_description: str,
    ticket_type: str,
    queue: str,
    top_k: int = 3,
) -> Dict[str, Any]:

    print("\n" + "=" * 120)
    print("OPS DECISION ENGINE - PREDICT + RETRIEVE")
    print("=" * 120)

    # 1️⃣ Load ML model
    model = load_ml_model()

    # 2️⃣ Predict priority
    predicted_priority = predict_priority(
        model,
        issue_description,
        ticket_type,
        queue,
    )

    print(f"\n[RESULT] Predicted Priority: {predicted_priority}")

    # 3️⃣ Build query
    query = build_query(issue_description, ticket_type, queue)

    # 4️⃣ Retrieve incidents
    retrieved = retrieve_similar_incidents(
        query=query,
        chroma_path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
        model_name=EMBED_MODEL,
        top_k=top_k,
        queue_filter=None,   # can enable later
        type_filter=None,
    )

    # 5️⃣ Return structured result (for future LLM)
    return {
        "issue_description": issue_description,
        "type": ticket_type,
        "queue": queue,
        "predicted_priority": predicted_priority,
        "retrieved_incidents": retrieved,
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