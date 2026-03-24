import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { Ticket } from "@/types/ops-decision-engine";

type TicketCardProps = {
  ticket: Ticket;
  selected?: boolean;
  onClick?: () => void;
};

function getStatusTone(status: string): string {
  const normalized = status.toLowerCase();

  if (normalized.includes("escalated")) {
    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  }
  if (normalized.includes("investigating")) {
    return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  }
  if (normalized.includes("mitigating")) {
    return "border-cyan-500/40 bg-cyan-500/10 text-cyan-300";
  }
  if (normalized.includes("open")) {
    return "border-blue-500/40 bg-blue-500/10 text-blue-300";
  }

  return "border-zinc-700 bg-zinc-800/80 text-zinc-300";
}

export default function TicketCard({
  ticket,
  selected = false,
  onClick,
}: TicketCardProps) {
  return (
    <Card
      onClick={onClick}
      className={[
        "group border bg-zinc-900/70 transition-all duration-200",
        "hover:-translate-y-0.5 hover:border-zinc-600 hover:bg-zinc-900/90 hover:shadow-[0_12px_24px_-18px_rgba(0,0,0,0.9)]",
        onClick ? "cursor-pointer" : "cursor-default",
        selected
          ? "border-cyan-500/60 bg-zinc-900 ring-1 ring-cyan-500/40 shadow-[0_0_0_1px_rgba(34,211,238,0.18)]"
          : "border-zinc-800",
      ].join(" ")}
    >
      <CardContent className="space-y-3.5 p-3.5">
        <div className="flex items-start justify-between gap-3">
          <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-zinc-100 group-hover:text-zinc-50">
            {ticket.title}
          </h3>
          <span
            className={[
              "mt-1 h-2.5 w-2.5 shrink-0 rounded-full",
              selected ? "bg-cyan-400 shadow-[0_0_0_4px_rgba(34,211,238,0.20)]" : "bg-zinc-600 group-hover:bg-zinc-500",
            ].join(" ")}
            aria-hidden
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className="border-zinc-700 bg-zinc-800/80 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-300"
          >
            {ticket.queue}
          </Badge>
          <Badge
            variant="outline"
            className="border-violet-500/40 bg-violet-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-violet-300"
          >
            {ticket.type}
          </Badge>
          <Badge
            variant="outline"
            className={`px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${getStatusTone(ticket.status)}`}
          >
            {ticket.status}
          </Badge>
        </div>

        <div className="flex items-center justify-between gap-2 text-[11px] text-zinc-400">
          <span className="truncate uppercase tracking-wide">{ticket.category}</span>
          <span className="shrink-0">{new Date(ticket.timestamp).toLocaleString()}</span>
        </div>
      </CardContent>
    </Card>
  );
}
