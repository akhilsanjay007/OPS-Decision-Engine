from typing import Any, Dict
from threading import Lock

from src.core.config import (
    CHROMA_DIR,
    KB_PATH,
    MODEL_PATH,
    get_openai_model,
    is_openai_configured,
)
from src.decision.engine import run_full_pipeline_structured
from src.decision.engine import run_full_pipeline_structured_debug
from src.pipeline.predict_and_retrieve import initialize_resources, get_cached_resources


class OpsDecisionService:
    def __init__(self) -> None:
        self.ready = False
        self.init_error: str | None = None
        self._startup_lock = Lock()
        self._resources: Dict[str, Any] | None = None

    def startup(self) -> None:
        with self._startup_lock:
            if self.ready and self._resources is not None:
                return

            try:
                print("[INFO] Initializing backend resources...")
                print(
                    f"[INFO] OPENAI_API_KEY: {'set' if is_openai_configured() else 'not set'} "
                    f"(OPENAI_MODEL={get_openai_model()!r})"
                )
                print(f"[INFO] MODEL_PATH: {MODEL_PATH}")
                print(f"[INFO] CHROMA_DIR: {CHROMA_DIR}")
                print(f"[INFO] KB_PATH: {KB_PATH}")
                initialize_resources()
                model, embedder, collection = get_cached_resources()
                self._resources = {
                    "model": model,
                    "embedder": embedder,
                    "collection": collection,
                }
                self.ready = True
                self.init_error = None
                print("[INFO] Backend resources initialized.")
            except Exception as exc:
                self.ready = False
                self.init_error = str(exc)
                print(f"[ERROR] Resource initialization failed: {exc}")
                raise

    def health(self) -> Dict[str, Any]:
        status = "ok" if self.ready else "degraded"
        payload: Dict[str, Any] = {
            "status": status,
            "service": "ops-decision-engine",
            "openai_configured": is_openai_configured(),
            "openai_model": get_openai_model(),
        }
        if self.init_error:
            payload["init_error"] = self.init_error
        return payload

    def predict(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        if not self.ready:
            self.startup()
        if self._resources is None:
            raise RuntimeError("Backend resources are not initialized.")

        return run_full_pipeline_structured(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
            resources=self._resources,
        )

    def predict_debug(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        if not self.ready:
            self.startup()
        if self._resources is None:
            raise RuntimeError("Backend resources are not initialized.")

        return run_full_pipeline_structured_debug(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
            resources=self._resources,
        )


service = OpsDecisionService()