from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Any, List, Dict

import chromadb
from sentence_transformers import SentenceTransformer


# ---------------- CONFIG ---------------- #

DEFAULT_CHROMA_PATH = "artifacts/rag/chroma_db"
DEFAULT_COLLECTION_NAME = "incident_memory"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------- HELPERS ---------------- #

def load_embedder(model_name: str) -> SentenceTransformer:
    print(f"[INFO] Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)


def load_collection(chroma_path: str, collection_name: str):
    db_path = Path(chroma_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Chroma DB not found: {db_path.resolve()}")

    print(f"[INFO] Loading Chroma DB from: {db_path.resolve()}")
    client = chromadb.PersistentClient(path=str(db_path))

    collections = [c.name for c in client.list_collections()]
    if collection_name not in collections:
        raise ValueError(f"Collection '{collection_name}' not found. Available: {collections}")

    print(f"[INFO] Using collection: {collection_name}")
    return client.get_collection(name=collection_name)


def format_text(text: str, width: int = 100) -> str:
    if not text:
        return "N/A"
    return textwrap.fill(text.strip(), width=width)


# ---------------- CORE RETRIEVAL ---------------- #

def retrieve_similar_incidents(
    query: str,
    chroma_path: str,
    collection_name: str,
    model_name: str,
    top_k: int = 5,
    queue_filter: str | None = None,
    type_filter: str | None = None,
) -> List[Dict[str, Any]]:

    embedder = load_embedder(model_name)
    collection = load_collection(chroma_path, collection_name)

    print("[INFO] Encoding query...")
    query_embedding = embedder.encode(query).tolist()

    # -------- FILTERS -------- #
    where_filter = {}

    if queue_filter:
        where_filter["queue"] = queue_filter

    if type_filter:
        where_filter["type"] = type_filter

    print(f"[INFO] Retrieving top {top_k} similar incidents...")

    if where_filter:
        print(f"[INFO] Applying filters: {where_filter}")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    if not ids:
        print("[INFO] No results found.")
        return []

    retrieved = []

    for idx, (doc_id, doc, meta, dist) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        meta = meta or {}

        item = {
            "rank": idx,
            "doc_id": doc_id,
            "distance": float(dist),

            # Flattened fields (important for pipeline)
            "issue_description": meta.get("issue_description", ""),
            "resolution": meta.get("resolution", ""),
            "type": meta.get("type", ""),
            "queue": meta.get("queue", ""),
            "priority": meta.get("priority", ""),
            "tags": meta.get("tags", []),

            "retrieval_text": doc,
        }

        retrieved.append(item)

    # -------- PRINT OUTPUT -------- #
    print("\n" + "#" * 110)
    print("QUERY")
    print("#" * 110)
    print(format_text(query))
    print()

    for item in retrieved:
        print("=" * 110)
        print(f"Result #{item['rank']}")
        print(f"Doc ID     : {item['doc_id']}")
        print(f"Distance   : {item['distance']:.4f}")
        print(f"Type       : {item['type']}")
        print(f"Queue      : {item['queue']}")
        print(f"Priority   : {item['priority']}")
        print(f"Tags       : {item['tags']}")
        print("-" * 110)
        print("Issue Description:")
        print(format_text(item["issue_description"]))
        print("-" * 110)
        print("Resolution:")
        print(format_text(item["resolution"]))
        print("=" * 110)
        print()

    return retrieved


# ---------------- CLI ---------------- #

def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve similar incidents from Chroma")

    parser.add_argument("--query", type=str, required=True, help="Issue description")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results")

    parser.add_argument("--queue", type=str, default=None, help="Filter by queue")
    parser.add_argument("--type", type=str, default=None, help="Filter by type")

    parser.add_argument("--chroma_path", type=str, default=DEFAULT_CHROMA_PATH)
    parser.add_argument("--collection_name", type=str, default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--model_name", type=str, default=DEFAULT_EMBEDDING_MODEL)

    return parser.parse_args()


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    args = parse_args()

    retrieve_similar_incidents(
        query=args.query,
        chroma_path=args.chroma_path,
        collection_name=args.collection_name,
        model_name=args.model_name,
        top_k=args.top_k,
        queue_filter=args.queue,
        type_filter=args.type,
    )