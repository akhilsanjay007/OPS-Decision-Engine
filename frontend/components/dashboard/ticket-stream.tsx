import TicketCard from "@/components/dashboard/ticket-card";
import type { Ticket } from "@/types/ops-decision-engine";

type TicketStreamProps = {
  tickets: Ticket[];
  selectedTicketId?: string;
  onSelectTicket: (ticket: Ticket) => void;
};

function sortTicketsNewestFirst(tickets: Ticket[]): Ticket[] {
  return [...tickets].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default function TicketStream({
  tickets,
  selectedTicketId,
  onSelectTicket,
}: TicketStreamProps) {
  const orderedTickets = sortTicketsNewestFirst(tickets);

  return (
    <section className="flex h-full min-h-[420px] min-h-0 flex-col overflow-hidden rounded-2xl border border-zinc-800/90 bg-zinc-900/70 p-4 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md sm:p-5">
      <header className="mb-4 shrink-0 space-y-1.5 border-b border-zinc-800/90 pb-3.5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-100">
          Live Incident Stream
        </h2>
        <p className="text-xs leading-relaxed text-zinc-400">
          Incoming operational tickets awaiting analysis
        </p>
      </header>

      {orderedTickets.length === 0 ? (
        <div className="flex min-h-0 flex-1 items-center justify-center rounded-xl border border-dashed border-zinc-800 bg-zinc-950/60 p-8 text-center">
          <div className="max-w-xs space-y-2">
            <p className="text-sm font-medium text-zinc-200">No active tickets</p>
            <p className="text-xs leading-relaxed text-zinc-500">
              New incidents will appear here when simulation starts.
            </p>
          </div>
        </div>
      ) : (
        // Keep scrolling within the stream body so the panel height stays bounded.
        <div className="min-h-0 flex-1 overflow-y-auto pr-1.5">
          <div className="space-y-2.5">
          {orderedTickets.map((ticket) => (
            <TicketCard
              key={ticket.id}
              ticket={ticket}
              selected={ticket.id === selectedTicketId}
              onClick={() => onSelectTicket(ticket)}
            />
          ))}
          </div>
        </div>
      )}
    </section>
  );
}
