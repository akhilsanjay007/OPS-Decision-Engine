export interface Ticket {
  id: string;
  title: string;
  issue_description: string;
  type: string;
  queue: string;
  timestamp: string;
  status: string;
  category: string;
}

export interface SimilarIncident {
  id: string;
  queue: string;
  priority: string;
  similarity_score: number;
  issue_description: string;
  resolution: string;
}

export interface DebugTrace {
  rawRetrieval: string[];
  rerankedResults: string[];
  deduplicatedResults: string[];
  prompt: string;
  rawLlmOutput: string;
}

export interface AnalysisResult {
  ml_priority: string;
  recommended_priority: string;
  confidence_score: number;
  confidence_label: "Low" | "Medium" | "High";
  escalation_decision: string;
  root_cause: string;
  priority_reasoning: string;
  action_plan: string[];
  diagnostic_steps: string[];
  similar_incidents: SimilarIncident[];
  debug_trace: DebugTrace;
}
