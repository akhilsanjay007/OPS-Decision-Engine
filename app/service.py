from typing import Any, Dict
from src.decision.engine import run_full_pipeline_structured
from src.decision.engine import run_full_pipeline_structured_debug
from src.pipeline.predict_and_retrieve import initialize_resources


class OpsDecisionService:
    def __init__(self) -> None:
        self.ready = False
        self.init_error: str | None = None

    def startup(self) -> None:
        try:
            print("[INFO] Initializing backend resources...")
            initialize_resources()
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
        payload: Dict[str, Any] = {"status": status, "service": "ops-decision-engine"}
        if self.init_error:
            payload["init_error"] = self.init_error
        return payload

    def predict(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        if not self.ready:
            self.startup()

        return run_full_pipeline_structured(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
        )

    def predict_debug(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        if not self.ready:
            self.startup()

        return run_full_pipeline_structured_debug(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
        )


service = OpsDecisionService()