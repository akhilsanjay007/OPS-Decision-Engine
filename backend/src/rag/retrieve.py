from __future__ import annotations

import argparse
import importlib.metadata
import os
import shutil
import textwrap
from pathlib import Path
from typing import Any, List, Dict

from src.runtime_paths import get_chroma_db_dir


# ---------------- CONFIG ---------------- #

DEFAULT_CHROMA_PATH = str(get_chroma_db_dir())
DEFAULT_COLLECTION_NAME = "incident_memory"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------- HELPERS ---------------- #

def load_embedder(model_name: str):
    print(f"[INFO] Loading embedding model: {model_name}")
    # Lazy import avoids heavy ML initialization during app module import.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _safe_chromadb_version() -> str:
    try:
        return importlib.metadata.version("chromadb")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _prepare_runtime_chroma_dir(source_path: Path) -> Path:
    """
    Use an isolated runtime copy so routine retrieval does not mutate canonical persisted files.
    """
    use_runtime_copy = _bool_env("CHROMA_USE_RUNTIME_COPY", True)
    if not use_runtime_copy:
        print("[INFO] CHROMA_USE_RUNTIME_COPY disabled; using canonical Chroma directory directly.")
        return source_path

    runtime_raw = os.getenv("CHROMA_RUNTIME_DIR", str(source_path.parent / "chroma_runtime"))
    runtime_path = Path(runtime_raw).expanduser().resolve()
    refresh_copy = _bool_env("CHROMA_RUNTIME_COPY_REFRESH", True)

    if runtime_path.exists() and refresh_copy:
        shutil.rmtree(runtime_path)

    if not runtime_path.exists():
        shutil.copytree(source_path, runtime_path)
        print(f"[INFO] Created isolated runtime Chroma copy at: {runtime_path}")
    else:
        print(f"[INFO] Reusing existing runtime Chroma copy at: {runtime_path}")

    return runtime_path


def log_chroma_diagnostics(chroma_path: str) -> None:
    """
    Emit startup diagnostics to help debug persisted Chroma compatibility issues.
    """
    db_path = Path(chroma_path)
    sqlite_path = db_path / "chroma.sqlite3"
    top_level_entries = sorted([p.name for p in db_path.iterdir()]) if db_path.exists() else []
    segment_dirs = [p for p in db_path.iterdir() if p.is_dir()] if db_path.exists() else []
    segment_index_files = any((d / "index_metadata.pickle").exists() for d in segment_dirs)

    chroma_version = _safe_chromadb_version()
    expected_layout = "chroma.sqlite3 + segment directory with index files"
    print(f"[DIAG] chromadb_version={chroma_version}")
    print(f"[DIAG] chroma_expected_layout={expected_layout}")
    print(f"[DIAG] chroma_dir={db_path.resolve()}")
    print(f"[DIAG] chroma_top_level_files={top_level_entries}")
    print(f"[DIAG] chroma_expected_sqlite_exists={sqlite_path.exists()}")
    print(f"[DIAG] chroma_expected_segment_index_exists={segment_index_files}")


def verify_persisted_collection(chroma_path: str, collection_name: str) -> tuple[bool, str]:
    """
    Verify persisted Chroma directory can be opened and queried.
    """
    db_path = Path(chroma_path)
    if not db_path.exists():
        return False, f"Chroma DB directory not found: {db_path.resolve()}"

    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(db_path))
        collections = [c.name for c in client.list_collections()]
        if collection_name not in collections:
            return False, (
                f"Collection '{collection_name}' not found. Available collections: {collections}"
            )

        collection = client.get_collection(name=collection_name)
        # lightweight runtime validity probe
        collection.query(query_texts=["startup health probe"], n_results=1)
        return True, "Persisted Chroma directory is readable and queryable."
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def load_collection(chroma_path: str, collection_name: str):
    source_db_path = Path(chroma_path)
    log_chroma_diagnostics(str(source_db_path))

    if not source_db_path.exists():
        raise FileNotFoundError(f"Chroma DB not found: {source_db_path.resolve()}")

    db_path = _prepare_runtime_chroma_dir(source_db_path)
    if db_path != source_db_path:
        log_chroma_diagnostics(str(db_path))

    ok, reason = verify_persisted_collection(str(db_path), collection_name)
    if not ok:
        raise RuntimeError(
            "Chroma persistence validation failed. "
            f"Reason: {reason}. Rebuild the DB with backend/scripts/rebuild_chroma.py"
        )

    print(f"[INFO] Loading Chroma DB from: {db_path.resolve()}")
    import chromadb

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
    embedder=None,
    collection=None,
) -> List[Dict[str, Any]]:
    if embedder is None:
        embedder = load_embedder(model_name)
    else:
        print("[INFO] Reusing cached embedding model")

    if collection is None:
        collection = load_collection(chroma_path, collection_name)
    else:
        print("[INFO] Reusing cached Chroma collection")

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