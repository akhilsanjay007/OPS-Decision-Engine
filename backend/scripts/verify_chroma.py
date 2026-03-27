from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path

import chromadb


EXPECTED_CHROMADB_VERSION = "1.0.20"
DEFAULT_COLLECTION = "incident_memory"


def verify(chroma_dir: Path, collection_name: str) -> None:
    installed = importlib.metadata.version("chromadb")
    print(f"[INFO] chromadb installed={installed}, expected={EXPECTED_CHROMADB_VERSION}")
    if installed != EXPECTED_CHROMADB_VERSION:
        raise RuntimeError(
            f"Version mismatch: expected {EXPECTED_CHROMADB_VERSION}, found {installed}"
        )

    if not chroma_dir.exists():
        raise FileNotFoundError(f"Chroma dir not found: {chroma_dir}")

    entries = sorted([p.name for p in chroma_dir.iterdir()])
    print(f"[INFO] Chroma top-level entries: {entries}")
    print(f"[INFO] chroma.sqlite3 exists: {(chroma_dir / 'chroma.sqlite3').exists()}")

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collections = [c.name for c in client.list_collections()]
    print(f"[INFO] Collections: {collections}")
    if collection_name not in collections:
        raise RuntimeError(f"Collection '{collection_name}' not found")

    collection = client.get_collection(name=collection_name)
    count = collection.count()
    print(f"[INFO] Collection '{collection_name}' count={count}")

    probe = collection.query(query_texts=["database verification probe"], n_results=1)
    ids = probe.get("ids", [[]])[0]
    print(f"[INFO] Query probe returned {len(ids)} result(s)")
    if not ids:
        raise RuntimeError("Query probe returned no results")

    print("[INFO] Chroma verification passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify persisted Chroma DB is queryable.")
    parser.add_argument("--chroma-dir", type=Path, default=Path("backend/data/chroma"))
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    verify(args.chroma_dir, args.collection)
