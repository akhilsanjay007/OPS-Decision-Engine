import { Badge } from "@/components/ui/badge";

const STATUS_ITEMS = [
  { label: "ML Active", tone: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  { label: "RAG Active", tone: "bg-cyan-500/10 text-cyan-300 border-cyan-500/30" },
  { label: "LLM Active", tone: "bg-violet-500/10 text-violet-300 border-violet-500/30" },
  { label: "System Online", tone: "bg-lime-500/10 text-lime-300 border-lime-500/30" },
] as const;

export default function Header() {
  return (
    <header className="rounded-2xl border border-zinc-800/90 bg-zinc-900/70 px-5 py-4 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md sm:px-6 sm:py-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-1.5">
          <h1 className="text-xl font-semibold tracking-tight text-zinc-50 sm:text-2xl">
            Ops Decision Engine
          </h1>
          <p className="max-w-3xl text-sm leading-relaxed text-zinc-400 sm:text-[15px]">
            AI-powered incident prioritization, root-cause analysis, and action guidance
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {STATUS_ITEMS.map((status) => (
            <Badge
              key={status.label}
              variant="outline"
              className={`border px-2.5 py-1 text-[11px] font-medium tracking-wide shadow-sm ${status.tone}`}
            >
              {status.label}
            </Badge>
          ))}
        </div>
      </div>
    </header>
  );
}
