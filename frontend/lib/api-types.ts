/**
 * Types matching FastAPI `PredictRequest` JSON (wire format).
 * The UI stores free-form copy in `ticket.issue_description`; the API field name is `issue`.
 */
export interface PredictRequestBody {
  issue: string;
  type: "INCIDENT" | "PROBLEM";
  queue: string;
}

export interface EscalationRecommendationDto {
  decision: string;
  team: string;
  reason: string;
  raw: string;
}

export interface EvidenceIncidentDto {
  doc_id?: string | null;
  type?: string | null;
  queue?: string | null;
  priority?: string | null;
  distance?: number | null;
  adjusted_score?: number | null;
  tags?: string[];
  issue_description?: string | null;
  resolution?: string | null;
}

/** Response body from POST /predict */
export interface PredictResponseDto {
  input_issue: string;
  input_type: string;
  input_queue: string;
  recommended_priority: string;
  ml_predicted_priority: string;
  rag_signal_priority: string;
  confidence_score: number;
  confidence_level: string;
  root_cause: string;
  action_plan: string[];
  next_diagnostics: string[];
  escalation_recommendation: EscalationRecommendationDto;
  evidence_from_similar_incidents: string[];
  evidence: EvidenceIncidentDto[];
  assessment_summary: string;
  raw_decision: string;
}

/** Response body from POST /predict/debug */
export interface PredictDebugResponseDto extends PredictResponseDto {
  raw_retrieved_incidents: EvidenceIncidentDto[];
  reranked_incidents: EvidenceIncidentDto[];
  deduplicated_incidents: EvidenceIncidentDto[];
  evidence_summary: string;
  prompt: string;
}
