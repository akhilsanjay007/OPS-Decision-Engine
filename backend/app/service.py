from __future__ import annotations

import os
import subprocess
import sys
import traceback
from threading import Lock, Thread
from typing import Any, Dict

from src.core.config import (
    CHROMA_DIR,
    KB_PATH,
    MODEL_PATH,
    get_openai_model,
    is_openai_configured,
)
from src.decision.engine import run_full_pipeline_structured
from src.decision.engine import run_full_pipeline_structured_debug
from src.pipeline.predict_and_retrieve import (
    COLLECTION_NAME,
    EMBED_MODEL,
    load_ml_model,
)
from src.rag.retrieve import load_collection, load_embedder


class ResourcesNotReadyError(RuntimeError):
    """Raised when prediction is requested before shared resources are ready."""


class OpsDecisionService:
    def __init__(self) -> None:
        self.ready = False
        self.init_error: str | None = None
        self._init_lock = Lock()
        self.init_started = False
        self._init_thread: Thread | None = None
        self.init_in_progress = False
        self.init_completed = False
        self.ml_model_loaded = False
        self.embedding_model_loaded = False
        self.chroma_loaded = False
        self.kb_loaded = False
        self.ml_model: Any | None = None
        self.embedding_model: Any | None = None
        self.chroma_collection: Any | None = None
        self.chroma_rebuild_in_progress = False
        self.chroma_rebuild_attempted = False

    def _bool_env(self, name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def _attempt_chroma_rebuild_and_reload(self) -> None:
        if self.chroma_rebuild_in_progress or self.chroma_rebuild_attempted:
            return
        if not KB_PATH.exists():
            print("[WARN] Skipping Chroma rebuild: KB_PATH does not exist.")
            return

        self.chroma_rebuild_in_progress = True
        self.chroma_rebuild_attempted = True
        try:
            build_batch_size = os.getenv("CHROMA_BUILD_BATCH_SIZE", "500")
            embed_batch_size = os.getenv("CHROMA_EMBED_BATCH_SIZE", "32")
            scripts_dir = os.getenv("APP_HOME", "/app")
            rebuild_script = f"{scripts_dir}/scripts/rebuild_chroma.py"
            verify_script = f"{scripts_dir}/scripts/verify_chroma.py"

            print(
                "[INFO] Starting background Chroma rebuild attempt "
                f"(batch={build_batch_size}, embed_batch={embed_batch_size})"
            )
            subprocess.run(
                [
                    sys.executable,
                    rebuild_script,
                    "--kb-path",
                    str(KB_PATH),
                    "--chroma-dir",
                    str(CHROMA_DIR),
                    "--batch-size",
                    str(build_batch_size),
                    "--embed-batch-size",
                    str(embed_batch_size),
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    verify_script,
                    "--chroma-dir",
                    str(CHROMA_DIR),
                    "--collection",
                    COLLECTION_NAME,
                ],
                check=True,
            )

            self.chroma_collection = load_collection(str(CHROMA_DIR), COLLECTION_NAME)
            self.chroma_loaded = True
            self.embedding_model = load_embedder(EMBED_MODEL)
            self.embedding_model_loaded = True
            print("[INFO] Background Chroma rebuild succeeded; retrieval enabled.")
        except Exception as rebuild_exc:
            self.embedding_model = None
            self.embedding_model_loaded = False
            self.chroma_collection = None
            self.chroma_loaded = False
            print(
                "[WARN] Background Chroma rebuild failed; staying in fallback mode: "
                f"{type(rebuild_exc).__name__}: {rebuild_exc}"
            )
        finally:
            self.chroma_rebuild_in_progress = False

    def _initialize_resources_once(self) -> None:
        try:
            print("[INFO] Background resource initialization started.")
            print(
                f"[INFO] OPENAI_API_KEY: {'set' if is_openai_configured() else 'not set'} "
                f"(OPENAI_MODEL={get_openai_model()!r})"
            )
            print(f"[INFO] MODEL_PATH: {MODEL_PATH}")
            print(f"[INFO] CHROMA_DIR: {CHROMA_DIR}")
            print(f"[INFO] KB_PATH: {KB_PATH}")

            self.ml_model = load_ml_model()
            self.ml_model_loaded = True
            print("[INFO] init ml loaded")

            try:
                self.chroma_collection = load_collection(str(CHROMA_DIR), COLLECTION_NAME)
                self.chroma_loaded = True
                print("[INFO] init chroma loaded")

                self.embedding_model = load_embedder(EMBED_MODEL)
                self.embedding_model_loaded = True
                print("[INFO] init embedding loaded")
            except Exception as chroma_exc:
                self.embedding_model = None
                self.embedding_model_loaded = False
                self.chroma_collection = None
                self.chroma_loaded = False
                print(
                    "[WARN] chroma skipped due to memory or initialization failure: "
                    f"{type(chroma_exc).__name__}: {chroma_exc}"
                )
                print("[WARN] fallback mode activated: ML + LLM without retrieval evidence.")
                if self._bool_env("CHROMA_AUTO_REBUILD_IF_MISSING", True):
                    print("[INFO] Scheduling one-time background Chroma rebuild attempt.")
                    Thread(
                        target=self._attempt_chroma_rebuild_and_reload,
                        name="ops-chroma-rebuild",
                        daemon=True,
                    ).start()
                else:
                    print("[INFO] CHROMA_AUTO_REBUILD_IF_MISSING disabled; skipping rebuild.")

            self.kb_loaded = KB_PATH.exists()
            if self.kb_loaded:
                print("[INFO] init kb loaded")
            else:
                print("[WARN] KB file not found; continuing without kb preload.")

            self.ready = True
            self.init_completed = True
            self.init_error = None
            print("[INFO] init completed")
        except Exception as exc:
            self.ready = False
            self.init_completed = False
            self.init_error = str(exc)
            print(f"[ERROR] Background initialization failed: {type(exc).__name__}: {exc}")
            print(traceback.format_exc())
        finally:
            self.init_in_progress = False

    def start_background_initialization(self) -> None:
        with self._init_lock:
            if self.init_started:
                print("[INFO] Background initialization already started; skipping duplicate launch.")
                return

            self.init_started = True
            self.init_in_progress = True
            print("[INFO] init started")
            self._init_thread = Thread(
                target=self._initialize_resources_once,
                name="ops-resource-init",
                daemon=True,
            )
            self._init_thread.start()
            print("[INFO] Background initialization thread launched.")

    def health(self) -> Dict[str, Any]:
        status = "ok" if self.ready else "degraded"
        payload: Dict[str, Any] = {
            "status": status,
            "service": "ops-decision-engine",
            "openai_configured": is_openai_configured(),
            "openai_model": get_openai_model(),
            "ml_model_loaded": self.ml_model_loaded,
            "embedding_model_loaded": self.embedding_model_loaded,
            "chroma_loaded": self.chroma_loaded,
            "kb_loaded": self.kb_loaded,
            "chroma_rebuild_in_progress": self.chroma_rebuild_in_progress,
            "chroma_rebuild_attempted": self.chroma_rebuild_attempted,
            "init_started": self.init_started,
            "init_in_progress": self.init_in_progress,
            "init_completed": self.init_completed,
        }
        if self.init_error:
            payload["init_error"] = self.init_error
        return payload

    def predict(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        if (
            self.ml_model is None
            or not self.init_completed
        ):
            raise ResourcesNotReadyError(
                "Service warming up: resources are still initializing. "
                "Retry in a few seconds and check /health for readiness flags."
            )

        retrieval_enabled = (
            self.embedding_model_loaded
            and self.chroma_loaded
            and self.embedding_model is not None
            and self.chroma_collection is not None
        )
        if not retrieval_enabled:
            print("[WARN] fallback mode activated: retrieval disabled (chroma not loaded).")

        return run_full_pipeline_structured(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
            retrieval_enabled=retrieval_enabled,
            resources={
                "model": self.ml_model,
                "embedder": self.embedding_model,
                "collection": self.chroma_collection,
            },
        )

    def predict_debug(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        if (
            self.ml_model is None
            or not self.init_completed
        ):
            raise ResourcesNotReadyError(
                "Service warming up: resources are still initializing. "
                "Retry in a few seconds and check /health for readiness flags."
            )

        retrieval_enabled = (
            self.embedding_model_loaded
            and self.chroma_loaded
            and self.embedding_model is not None
            and self.chroma_collection is not None
        )
        if not retrieval_enabled:
            print("[WARN] fallback mode activated: retrieval disabled (chroma not loaded).")

        return run_full_pipeline_structured_debug(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
            retrieval_enabled=retrieval_enabled,
            resources={
                "model": self.ml_model,
                "embedder": self.embedding_model,
                "collection": self.chroma_collection,
            },
        )