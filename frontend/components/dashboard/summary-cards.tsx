import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalysisResult } from "@/types/ops-decision-engine";

type SummaryCardsProps = {
  result: AnalysisResult;
};

type PriorityLevel = "HIGH" | "MEDIUM" | "LOW";

function toPriorityLevel(value: string): PriorityLevel {
  const normalized = value.trim().toUpperCase();

  if (["P0", "P1", "HIGH", "CRITICAL", "SEVERE"].includes(normalized)) {
    return "HIGH";
  }
  if (["P2", "MEDIUM", "MODERATE"].includes(normalized)) {
    return "MEDIUM";
  }
  return "LOW";
}

function priorityTone(level: PriorityLevel): string {
  if (level === "HIGH") {
    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  }
  if (level === "MEDIUM") {
    return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  }
  return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
}

function escalationTone(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized.includes("declare") || normalized.includes("immediate")) {
    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  }
  if (normalized.includes("escalate")) {
    return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  }
  return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
}

export default function SummaryCards({ result }: SummaryCardsProps) {
  const recommendedLevel = toPriorityLevel(result.recommended_priority);
  const mlLevel = toPriorityLevel(result.ml_priority);
  const confidencePercent = `${Math.round(result.confidence_score * 100)}%`;

  return (
    <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 2xl:grid-cols-4">
      <Card className="flex min-h-[136px] flex-col border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Recommended Priority
          </CardTitle>
        </CardHeader>
        <CardContent className="mt-auto space-y-2 pt-0">
          <Badge variant="outline" className={priorityTone(recommendedLevel)}>
            {recommendedLevel}
          </Badge>
          <p className="text-sm font-medium text-zinc-200">{result.recommended_priority}</p>
        </CardContent>
      </Card>

      <Card className="flex min-h-[136px] flex-col border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            ML Predicted Priority
          </CardTitle>
        </CardHeader>
        <CardContent className="mt-auto space-y-2 pt-0">
          <Badge variant="outline" className={priorityTone(mlLevel)}>
            {mlLevel}
          </Badge>
          <p className="text-sm font-medium text-zinc-200">{result.ml_priority}</p>
        </CardContent>
      </Card>

      <Card className="flex min-h-[136px] flex-col border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Confidence Score
          </CardTitle>
        </CardHeader>
        <CardContent className="mt-auto space-y-2 pt-0">
          <p className="text-2xl font-semibold tracking-tight text-zinc-100">{confidencePercent}</p>
          <Badge variant="outline" className="border-cyan-500/40 bg-cyan-500/10 text-cyan-300">
            {result.confidence_label}
          </Badge>
        </CardContent>
      </Card>

      <Card className="flex min-h-[136px] flex-col border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Escalation Decision
          </CardTitle>
        </CardHeader>
        <CardContent className="mt-auto space-y-2 pt-0">
          <Badge variant="outline" className={escalationTone(result.escalation_decision)}>
            Operational Guidance
          </Badge>
          <p className="line-clamp-2 text-sm leading-relaxed text-zinc-300">
            {result.escalation_decision}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
