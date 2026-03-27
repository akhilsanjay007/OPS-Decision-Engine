from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


EXPECTED_CHROMADB_VERSION = "1.5.5"
DEFAULT_COLLECTION = "incident_memory"
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _assert_chromadb_version(expected: str) -> None:
    installed = importlib.metadata.version("chromadb")
    print(f"[INFO] chromadb installed={installed}, expected={expected}")
    if installed != expected:
        raise RuntimeError(
            "chromadb version mismatch. "
            f"Expected {expected}, found {installed}. "
            "Install exact requirements before rebuilding."
        )


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _chunk(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def rebuild(
    kb_path: Path,
    chroma_dir: Path,
    collection_name: str,
    embedding_model: str,
    batch_size: int,
    embed_batch_size: int,
) -> None:
    _assert_chromadb_version(EXPECTED_CHROMADB_VERSION)

    if not kb_path.exists():
        raise FileNotFoundError(f"KB JSONL not found: {kb_path}")

    records = _load_jsonl(kb_path)
    if not records:
        raise ValueError("KB JSONL is empty; cannot rebuild Chroma DB.")

    print(f"[INFO] Loaded KB records: {len(records)} from {kb_path}")
    print(f"[INFO] Loading embedder: {embedding_model}")
    model = SentenceTransformer(embedding_model)

    if chroma_dir.exists():
        print(f"[INFO] Removing existing Chroma directory: {chroma_dir}")
        shutil.rmtree(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.create_collection(name=collection_name)
    print(f"[INFO] Created collection: {collection_name}")

    total_docs = len(records)
    print(
        f"[INFO] Streaming build with add_batch_size={batch_size}, "
        f"embed_batch_size={embed_batch_size}, total_docs={total_docs}"
    )
    print("[INFO] Encoding and writing in chunks to reduce memory usage...")
    offset = 0
    while offset < total_docs:
        end = min(offset + batch_size, total_docs)
        chunk = records[offset:end]

        ids = [str(r["doc_id"]) for r in chunk]
        docs = [r["retrieval_text"] for r in chunk]
        metas = []
        for r in chunk:
            metas.append(
                {
                    "source": r.get("source", ""),
                    "issue_description": r.get("issue_description", ""),
                    "resolution": r.get("resolution", ""),
                    "type": r.get("type", ""),
                    "queue": r.get("queue", ""),
                    "priority": r.get("priority", ""),
                    "tags": ", ".join(r.get("tags", []))
                    if isinstance(r.get("tags", []), list)
                    else str(r.get("tags", "")),
                }
            )

        embeddings = model.encode(
            docs,
            batch_size=embed_batch_size,
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids=ids,
            documents=docs,
            embeddings=embeddings,
            metadatas=metas,
        )
        print(f"[INFO] Added batch {offset}..{end - 1}")
        offset = end

    print(f"[INFO] Rebuild complete at: {chroma_dir}")
    print("[INFO] Run backend/scripts/verify_chroma.py before deploy.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild persisted Chroma DB from KB JSONL.")
    parser.add_argument(
        "--kb-path",
        type=Path,
        default=Path("backend/data/processed/rag_knowledge_base.jsonl"),
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        default=Path("backend/data/chroma"),
    )
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION)
    parser.add_argument("--embed-model", type=str, default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--embed-batch-size", type=int, default=32)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rebuild(
        kb_path=args.kb_path,
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        embedding_model=args.embed_model,
        batch_size=args.batch_size,
        embed_batch_size=args.embed_batch_size,
    )
