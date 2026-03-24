import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ANALYSIS_STEPS = [
  "Predicting priority",
  "Retrieving similar incidents",
  "Generating decision guidance",
] as const;

export default function LoadingState() {
  return (
    <Card className="h-full min-h-[420px] border-zinc-800/90 bg-zinc-900/70 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md">
      <CardHeader className="border-b border-zinc-800/90 pb-4">
        <CardTitle className="text-sm font-semibold uppercase tracking-wide text-zinc-100">
          Analysis In Progress
        </CardTitle>
        <p className="text-xs leading-relaxed text-zinc-400">
          Running the Ops Decision Engine pipeline for the selected incident.
        </p>
      </CardHeader>

      <CardContent className="space-y-4 p-4 sm:p-5">
        {ANALYSIS_STEPS.map((step, index) => (
          <div
            key={step}
            className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]"
          >
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="flex h-5 w-5 items-center justify-center rounded-full border border-cyan-500/40 bg-cyan-500/10 text-[11px] font-semibold text-cyan-300">
                  {index + 1}
                </span>
                <p className="text-sm font-medium text-zinc-200">{step}</p>
              </div>
              <span className="text-[11px] uppercase tracking-wide text-zinc-500">
                Processing
              </span>
            </div>

            <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full w-2/3 rounded-full bg-gradient-to-r from-cyan-500/60 to-blue-500/60 animate-pulse"
                aria-hidden
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
