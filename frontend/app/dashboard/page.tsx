"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import AnalysisWorkspace from "@/components/dashboard/analysis-workspace";
import ControlBar from "@/components/dashboard/control-bar";
import Header from "@/components/dashboard/header";
import ManualTicketModal from "@/components/dashboard/manual-ticket-modal";
import TicketStream from "@/components/dashboard/ticket-stream";
import { getMockAnalysisResult, mockTickets } from "@/lib/mock-data";
import type { AnalysisResult, Ticket } from "@/types/ops-decision-engine";

type ManualTicketInput = {
  issue_description: string;
  type: string;
  queue: string;
};

const SPEED_TO_DELAY_MS: Record<string, number> = {
  Slow: 4500,
  Normal: 2500,
  Fast: 1200,
};

function buildManualTicket(input: ManualTicketInput): Ticket {
  const now = new Date();
  const suffix = Math.floor(1000 + Math.random() * 9000);
  const id = `MAN-${now.getFullYear()}${suffix}`;

  return {
    id,
    title: `${input.type}: ${input.issue_description.slice(0, 52)}${
      input.issue_description.length > 52 ? "..." : ""
    }`,
    issue_description: input.issue_description,
    type: input.type,
    queue: input.queue,
    timestamp: now.toISOString(),
    status: "Open",
    category: "manual",
  };
}

export default function DashboardPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [speed, setSpeed] = useState("Normal");
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [nextTicketIndex, setNextTicketIndex] = useState(0);

  const analysisTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const simulationDelay = useMemo(
    () => SPEED_TO_DELAY_MS[speed] ?? SPEED_TO_DELAY_MS.Normal,
    [speed]
  );

  useEffect(() => {
    if (!simulationRunning || nextTicketIndex >= mockTickets.length) {
      return;
    }

    const timeoutId = setTimeout(() => {
      const nextTicket = mockTickets[nextTicketIndex];
      setTickets((prev) => [nextTicket, ...prev]);
      setNextTicketIndex((prev) => prev + 1);
    }, simulationDelay);

    return () => clearTimeout(timeoutId);
  }, [simulationRunning, nextTicketIndex, simulationDelay]);

  useEffect(() => {
    if (nextTicketIndex >= mockTickets.length) {
      setSimulationRunning(false);
    }
  }, [nextTicketIndex]);

  useEffect(() => {
    return () => {
      if (analysisTimeoutRef.current) {
        clearTimeout(analysisTimeoutRef.current);
      }
    };
  }, []);

  const runAnalysis = (ticket: Ticket) => {
    setSelectedTicket(ticket);
    setLoading(true);
    setAnalysisResult(null);

    if (analysisTimeoutRef.current) {
      clearTimeout(analysisTimeoutRef.current);
    }

    analysisTimeoutRef.current = setTimeout(() => {
      setAnalysisResult(getMockAnalysisResult(ticket));
      setLoading(false);
    }, 1000);
  };

  const handleStart = () => setSimulationRunning(true);
  const handlePause = () => setSimulationRunning(false);

  const handleClear = () => {
    setSimulationRunning(false);
    setTickets([]);
    setSelectedTicket(null);
    setAnalysisResult(null);
    setLoading(false);
    setNextTicketIndex(0);
    if (analysisTimeoutRef.current) {
      clearTimeout(analysisTimeoutRef.current);
    }
  };

  const handleManualTicket = () => setManualModalOpen(true);

  const handleManualSubmit = (ticketInput: ManualTicketInput) => {
    const manualTicket = buildManualTicket(ticketInput);
    setTickets((prev) => [manualTicket, ...prev]);
    runAnalysis(manualTicket);
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900 text-zinc-100">
      <div className="mx-auto flex min-h-screen w-full max-w-[1800px] flex-col gap-5 px-4 py-5 sm:gap-6 sm:px-6 sm:py-6 lg:px-8">
        <Header />

        <ControlBar
          simulationRunning={simulationRunning}
          debugMode={debugMode}
          speed={speed}
          onStart={handleStart}
          onPause={handlePause}
          onClear={handleClear}
          onDebugToggle={setDebugMode}
          onSpeedChange={setSpeed}
          onManualTicket={handleManualTicket}
        />

        <section className="flex-1 min-h-0">
          <div className="grid h-full min-h-0 grid-cols-1 gap-5 xl:grid-cols-12 xl:gap-6">
            <aside className="min-h-0 xl:col-span-4 xl:h-full">
              <TicketStream
                tickets={tickets}
                selectedTicketId={selectedTicket?.id}
                onSelectTicket={runAnalysis}
              />
            </aside>

            <section className="min-h-0 xl:col-span-8 xl:h-full">
              <AnalysisWorkspace
                ticket={selectedTicket}
                result={analysisResult}
                loading={loading}
                debugMode={debugMode}
              />
            </section>
          </div>
        </section>
      </div>

      <ManualTicketModal
        open={manualModalOpen}
        onOpenChange={setManualModalOpen}
        onSubmit={handleManualSubmit}
      />
    </main>
  );
}
