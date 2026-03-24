import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ActionsCard from "@/components/dashboard/actions-card";
import DebugTabs from "@/components/dashboard/debug-tabs";
import EmptyState from "@/components/dashboard/analysis-empty-state";
import InfoCard from "@/components/dashboard/info-card";
import ErrorState from "@/components/dashboard/analysis-error-state";
import LoadingState from "@/components/dashboard/analysis-loading-state";
import SimilarIncidents from "@/components/dashboard/similar-incidents";
import SummaryCards from "@/components/dashboard/summary-cards";
import type { AnalysisResult, Ticket } from "@/types/ops-decision-engine";

type AnalysisWorkspaceProps = {
  ticket?: Ticket | null;
  result?: AnalysisResult | null;
  loading?: boolean;
  error?: string | null;
  debugMode?: boolean;
};

export default function AnalysisWorkspace({
  ticket,
  result,
  loading = false,
  error = null,
  debugMode = false,
}: AnalysisWorkspaceProps) {
  if (!ticket) {
    return <EmptyState />;
  }

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!result) {
    return <EmptyState />;
  }

  return (
    <section className="flex min-h-[420px] flex-col gap-4 overflow-y-auto rounded-2xl border border-zinc-800/90 bg-zinc-900/70 p-4 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md sm:gap-5 sm:p-5">
      <Card className="w-full border-zinc-800 bg-zinc-950/60 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]">
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-1.5">
              <CardTitle className="text-base font-semibold tracking-tight text-zinc-100">
                {ticket.title}
              </CardTitle>
              <p className="text-sm leading-relaxed text-zinc-400">{ticket.issue_description}</p>
            </div>
            <Badge
              variant="outline"
              className="w-fit border-zinc-700 bg-zinc-900 px-2.5 py-0.5 text-zinc-300"
            >
              {ticket.id}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <Badge
              variant="outline"
              className="border-zinc-700 bg-zinc-900/80 text-zinc-300"
            >
              {ticket.queue}
            </Badge>
            <Badge
              variant="outline"
              className="border-violet-500/40 bg-violet-500/10 text-violet-300"
            >
              {ticket.type}
            </Badge>
            <Badge
              variant="outline"
              className="border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
            >
              {ticket.category}
            </Badge>
            <span className="ml-auto text-xs text-zinc-500">
              {new Date(ticket.timestamp).toLocaleString()}
            </span>
          </div>
        </CardContent>
      </Card>

      <SummaryCards result={result} />

      <div className="grid grid-cols-1 gap-4 2xl:grid-cols-2">
        <InfoCard title="Root Cause" content={result.root_cause} />
        <InfoCard title="Priority Reasoning" content={result.priority_reasoning} />
      </div>

      <div className="grid grid-cols-1 gap-4 2xl:grid-cols-2">
        <ActionsCard title="Recommended Actions" items={result.action_plan} />
        <ActionsCard title="Diagnostic Steps" items={result.diagnostic_steps} />
      </div>

      <SimilarIncidents incidents={result.similar_incidents} />

      {debugMode ? <DebugTabs debugTrace={result.debug_trace} /> : null}
    </section>
  );
}
