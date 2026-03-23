from typing import Any, Dict
from src.decision.engine import run_full_pipeline_structured


class OpsDecisionService:
    def __init__(self) -> None:
        self.ready = True

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "service": "ops-decision-engine"}

    def predict(self, issue: str, ticket_type: str, queue: str) -> Dict[str, Any]:
        return run_full_pipeline_structured(
            issue_description=issue,
            ticket_type=ticket_type,
            queue=queue,
            top_k=3,
        )


service = OpsDecisionService()