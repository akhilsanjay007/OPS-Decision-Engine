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

/** Values are JSON-stringified in DebugTabs; use `unknown` for strings or structured lists. */
export interface DebugTrace {
  rawRetrieval: unknown;
  rerankedResults: unknown;
  deduplicatedResults: unknown;
  prompt: string;
  rawLlmOutput: string;
}

export const EMPTY_DEBUG_TRACE: DebugTrace = {
  rawRetrieval: [],
  rerankedResults: [],
  deduplicatedResults: [],
  prompt: "",
  rawLlmOutput: "",
};

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
