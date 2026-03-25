from __future__ import annotations

import os
from pathlib import Path

# Container-safe defaults. The Dockerfile sets `APP_HOME=/app`, and we assume
# runtime assets are copied into:
# - /app/models/
# - /app/data/chroma/
# - /app/data/processed/
#
# Users can override any of these via environment variables.
_APP_HOME = os.getenv("APP_HOME", "/app")


def _resolve_app_path(raw_path: str) -> Path:
    """
    Resolve `raw_path` into an absolute path.

    If `raw_path` is relative, it is interpreted relative to `APP_HOME`.
    """
    p = Path(raw_path.strip())
    if p.is_absolute():
        return p.resolve()
    return (Path(_APP_HOME) / p).resolve()


# Path to the serialized priority prediction model (joblib pipeline).
MODEL_PATH: Path = _resolve_app_path(
    os.getenv("MODEL_PATH", "models/priority_stage5_svm_pipeline.joblib")
)


# Directory for persisted Chroma vector store.
# Backwards-compat: older code/env used `CHROMA_DB_DIR`.
_CHROMA_RAW = os.getenv("CHROMA_DIR") or os.getenv("CHROMA_DB_DIR") or "data/chroma"
CHROMA_DIR: Path = _resolve_app_path(_CHROMA_RAW)


# JSONL knowledge base used to (re)build the vector index.
KB_PATH: Path = _resolve_app_path(
    os.getenv("KB_PATH", "data/processed/rag_knowledge_base.jsonl")
)


def get_openai_api_key() -> str | None:
    """Return trimmed API key, or None if unset / empty."""
    raw = os.getenv("OPENAI_API_KEY", "")
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped if stripped else None


def get_openai_model() -> str:
    """Chat model name for OpenAI completions (default matches prior hardcoded value)."""
    raw = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    stripped = (raw or "").strip()
    return stripped if stripped else "gpt-4o-mini"


def is_openai_configured() -> bool:
    return get_openai_api_key() is not None

