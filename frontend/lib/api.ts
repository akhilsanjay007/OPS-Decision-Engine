import { getApiBaseUrl } from "@/lib/config";
import type {
  EvidenceIncidentDto,
  PredictDebugResponseDto,
  PredictRequestBody,
  PredictResponseDto,
} from "@/lib/api-types";
import type { AnalysisResult, DebugTrace, SimilarIncident, Ticket } from "@/types/ops-decision-engine";
import { EMPTY_DEBUG_TRACE } from "@/types/ops-decision-engine";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function mapTicketTypeToApi(ticketType: string): "INCIDENT" | "PROBLEM" {
  const normalized = ticketType.trim().toLowerCase();
  if (normalized === "problem") {
    return "PROBLEM";
  }
  return "INCIDENT";
}

export function buildPredictRequestBody(ticket: Ticket): PredictRequestBody {
  return {
    issue: ticket.issue_description,
    type: mapTicketTypeToApi(ticket.type),
    queue: ticket.queue,
  };
}

export function confidenceScoreToLabel(score: number): AnalysisResult["confidence_label"] {
  if (score >= 0.75) {
    return "High";
  }
  if (score >= 0.45) {
    return "Medium";
  }
  return "Low";
}

function similarityFromEvidence(dto: EvidenceIncidentDto): number {
  const d = dto.distance;
  if (d != null && !Number.isNaN(d)) {
    return Math.max(0, Math.min(1, 1 / (1 + d)));
  }
  const a = dto.adjusted_score;
  if (a != null && !Number.isNaN(a)) {
    return Math.max(0, Math.min(1, 1 / (1 + Math.abs(a))));
  }
  return 0;
}

function mapEvidenceToSimilarIncident(dto: EvidenceIncidentDto, index: number): SimilarIncident {
  const id = dto.doc_id?.trim() || `evidence-${index + 1}`;
  const similarity_score = similarityFromEvidence(dto);

  return {
    id,
    queue: dto.queue ?? "—",
    priority: dto.priority ?? "—",
    similarity_score,
    issue_description: dto.issue_description ?? "",
    resolution: dto.resolution ?? "",
  };
}

function mapEscalationDecision(dto: PredictResponseDto["escalation_recommendation"]): string {
  const raw = dto.raw?.trim();
  if (raw) {
    return raw;
  }
  const parts = [dto.decision, dto.team, dto.reason].filter((p) => p && p.trim());
  return parts.join(" — ");
}

function isPredictResponseDto(value: unknown): value is PredictResponseDto {
  if (!value || typeof value !== "object") {
    return false;
  }
  const v = value as Record<string, unknown>;
  return (
    typeof v.recommended_priority === "string" &&
    typeof v.ml_predicted_priority === "string" &&
    typeof v.confidence_score === "number"
  );
}

function isPredictDebugResponseDto(value: unknown): value is PredictDebugResponseDto {
  if (!isPredictResponseDto(value)) {
    return false;
  }
  const v = value as unknown as Record<string, unknown>;
  return Array.isArray(v.raw_retrieved_incidents);
}

async function parseJsonResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text.trim()) {
    throw new ApiError("The server returned an empty response.", response.status);
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new ApiError("The server response was not valid JSON.", response.status, text.slice(0, 240));
  }
}

function extractErrorDetail(parsed: unknown): string | undefined {
  if (!parsed || typeof parsed !== "object") {
    return undefined;
  }
  const detail = (parsed as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "object" && item && "msg" in item ? String((item as { msg: unknown }).msg) : String(item)
      )
      .join("; ");
  }
  return undefined;
}

export function mapPredictResponseToAnalysisResult(
  dto: PredictResponseDto,
  debug: PredictDebugResponseDto | null
): AnalysisResult {
  const confidence_score =
    dto.confidence_score > 1 ? Math.min(1, dto.confidence_score / 100) : dto.confidence_score;

  const debugTrace: DebugTrace = debug
    ? {
        rawRetrieval: debug.raw_retrieved_incidents ?? [],
        rerankedResults: debug.reranked_incidents ?? [],
        deduplicatedResults: debug.deduplicated_incidents ?? [],
        prompt: debug.prompt ?? "",
        rawLlmOutput: dto.raw_decision ?? "",
      }
    : { ...EMPTY_DEBUG_TRACE };

  return {
    ml_priority: dto.ml_predicted_priority,
    recommended_priority: dto.recommended_priority,
    confidence_score: Number.isFinite(confidence_score) ? confidence_score : 0,
    confidence_label: confidenceScoreToLabel(Number.isFinite(confidence_score) ? confidence_score : 0),
    escalation_decision: mapEscalationDecision(dto.escalation_recommendation),
    root_cause: dto.root_cause ?? "",
    priority_reasoning: dto.assessment_summary ?? "",
    action_plan: Array.isArray(dto.action_plan) ? dto.action_plan : [],
    diagnostic_steps: Array.isArray(dto.next_diagnostics) ? dto.next_diagnostics : [],
    similar_incidents: Array.isArray(dto.evidence) ? dto.evidence.map(mapEvidenceToSimilarIncident) : [],
    debug_trace: debugTrace,
  };
}

function assertDebugPayload(body: unknown, debugMode: boolean): PredictDebugResponseDto | null {
  if (!debugMode) {
    return null;
  }
  if (!isPredictDebugResponseDto(body)) {
    throw new ApiError("Unexpected debug response shape from /predict/debug.");
  }
  return body;
}

export async function analyzeTicket(ticket: Ticket, debugMode: boolean): Promise<AnalysisResult> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new ApiError("API base URL is missing. Set NEXT_PUBLIC_API_URL in frontend/.env.local.");
  }

  const path = debugMode ? "/predict/debug" : "/predict";
  const url = `${baseUrl}${path}`;
  const payload = buildPredictRequestBody(ticket);

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(
      "Network error: could not reach the Ops Decision Engine API. Is the backend running?"
    );
  }

  const parsed = await parseJsonResponse(response);

  if (!response.ok) {
    const detail = extractErrorDetail(parsed);
    const message =
      detail ||
      (response.status >= 500
        ? "The analysis service failed. Try again or check backend logs."
        : `Request failed with status ${response.status}.`);
    throw new ApiError(message, response.status, detail);
  }

  if (!isPredictResponseDto(parsed)) {
    throw new ApiError("Unexpected response shape from analysis API.");
  }

  const debugDto = assertDebugPayload(parsed, debugMode);
  return mapPredictResponseToAnalysisResult(parsed, debugDto);
}

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}
