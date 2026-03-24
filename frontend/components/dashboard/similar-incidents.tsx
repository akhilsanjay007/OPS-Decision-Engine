import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SimilarIncident } from "@/types/ops-decision-engine";

type SimilarIncidentsProps = {
  incidents: SimilarIncident[];
};

function priorityTone(priority: string): string {
  const normalized = priority.toUpperCase();
  if (["P0", "P1", "HIGH", "CRITICAL"].includes(normalized)) {
    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  }
  if (["P2", "MEDIUM", "MODERATE"].includes(normalized)) {
    return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  }
  return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
}

export default function SimilarIncidents({ incidents }: SimilarIncidentsProps) {
  return (
    <Card className="border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-zinc-100">
          Similar Past Incidents
        </CardTitle>
        <p className="text-xs text-zinc-400">
          Evidence retrieved from related historical cases
        </p>
      </CardHeader>

      <CardContent className="pt-0">
        {incidents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-950/50 px-4 py-6 text-center">
            <p className="text-sm text-zinc-400">No similar incidents were retrieved.</p>
          </div>
        ) : (
          <Accordion type="single" collapsible className="w-full space-y-2">
            {incidents.map((incident) => (
              <AccordionItem
                key={incident.id}
                value={incident.id}
                className="rounded-xl border border-zinc-800 bg-zinc-950/40 px-3"
              >
                <AccordionTrigger className="py-3 hover:no-underline">
                  <div className="flex w-full flex-col items-start gap-2 text-left sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-zinc-100">{incident.id}</p>
                      <p className="text-xs text-zinc-400">{incident.queue}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className={priorityTone(incident.priority)}>
                        {incident.priority}
                      </Badge>
                      <Badge
                        variant="outline"
                        className="border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
                      >
                        Similarity {Math.round(incident.similarity_score * 100)}%
                      </Badge>
                    </div>
                  </div>
                </AccordionTrigger>

                <AccordionContent className="space-y-3 pb-3 pt-1">
                  <div className="space-y-1">
                    <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                      Issue Description
                    </p>
                    <p className="text-sm leading-relaxed text-zinc-200">
                      {incident.issue_description}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                      Resolution
                    </p>
                    <p className="text-sm leading-relaxed text-zinc-200">{incident.resolution}</p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
}
