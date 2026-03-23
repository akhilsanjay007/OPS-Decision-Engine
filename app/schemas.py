from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    issue: str = Field(..., min_length=5)
    type: Literal["INCIDENT", "PROBLEM"]
    queue: str = Field(..., min_length=2)


class EscalationRecommendation(BaseModel):
    decision: str
    team: str
    reason: str
    raw: str


class EvidenceIncident(BaseModel):
    doc_id: Optional[str] = None
    type: Optional[str] = None
    queue: Optional[str] = None
    priority: Optional[str] = None
    distance: Optional[float] = None
    adjusted_score: Optional[float] = None
    tags: List[str] = []
    issue_description: Optional[str] = None
    resolution: Optional[str] = None


class PredictResponse(BaseModel):
    input_issue: str
    input_type: str
    input_queue: str
    recommended_priority: str
    ml_predicted_priority: str
    rag_signal_priority: str
    confidence_score: float
    confidence_level: str
    root_cause: str
    action_plan: List[str]
    next_diagnostics: List[str]
    escalation_recommendation: EscalationRecommendation
    evidence_from_similar_incidents: List[str]
    evidence: List[EvidenceIncident]
    assessment_summary: str
    raw_decision: str