"""
Resolved paths for runtime assets (model, Chroma DB, RAG knowledge base).

Set MODEL_PATH, CHROMA_DB_DIR, and KB_PATH to override defaults.
Relative values are resolved against the backend package root (parent of `src/`).
"""

from __future__ import annotations

import os
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _resolve_env_path(env_var: str, default_relative: str) -> Path:
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return (_BACKEND_ROOT / default_relative).resolve()
    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    return (_BACKEND_ROOT / p).resolve()


def get_model_path() -> Path:
    """Priority ML model (joblib pipeline)."""
    return _resolve_env_path("MODEL_PATH", "models/priority_stage5_svm_pipeline.joblib")


def get_chroma_db_dir() -> Path:
    """Directory for persisted Chroma vector store."""
    return _resolve_env_path("CHROMA_DB_DIR", "data/chroma")


def get_kb_path() -> Path:
    """JSONL knowledge base used to build / refresh the vector index."""
    return _resolve_env_path("KB_PATH", "data/processed/rag_knowledge_base.jsonl")
