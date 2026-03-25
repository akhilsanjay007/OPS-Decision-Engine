"""
Resolved paths for runtime assets (model, Chroma DB, RAG knowledge base).

This module keeps the existing public API:
- `get_model_path()`
- `get_chroma_db_dir()`
- `get_kb_path()`

Internally, it delegates to `src.core.config` so defaults are container-safe
(`APP_HOME=/app`) and can be overridden via environment variables.
"""

from __future__ import annotations

from pathlib import Path

from src.core.config import CHROMA_DIR, KB_PATH, MODEL_PATH


def get_model_path() -> Path:
    """Priority ML model (joblib pipeline)."""
    return MODEL_PATH


def get_chroma_db_dir() -> Path:
    """Directory for persisted Chroma vector store."""
    return CHROMA_DIR


def get_kb_path() -> Path:
    """JSONL knowledge base used to build / refresh the vector index."""
    return KB_PATH
