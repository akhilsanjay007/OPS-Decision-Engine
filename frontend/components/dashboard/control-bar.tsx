import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

type ControlBarProps = {
  simulationRunning: boolean;
  debugMode: boolean;
  speed: string;
  onStart: () => void;
  onPause: () => void;
  onClear: () => void;
  onDebugToggle: (checked: boolean) => void;
  onSpeedChange: (value: string) => void;
  onManualTicket: () => void;
};

const SPEED_OPTIONS = [
  { label: "Slow", value: "Slow" },
  { label: "Normal", value: "Normal" },
  { label: "Fast", value: "Fast" },
] as const;

export default function ControlBar({
  simulationRunning,
  debugMode,
  speed,
  onStart,
  onPause,
  onClear,
  onDebugToggle,
  onSpeedChange,
  onManualTicket,
}: ControlBarProps) {
  return (
    <section className="rounded-2xl border border-zinc-800/90 bg-zinc-900/70 p-4 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md sm:p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            type="button"
            onClick={onStart}
            disabled={simulationRunning}
            className="bg-emerald-600 text-white shadow-sm hover:bg-emerald-500 disabled:bg-zinc-800 disabled:text-zinc-500"
          >
            Start Simulation
          </Button>

          <Button
            type="button"
            variant="secondary"
            onClick={onPause}
            disabled={!simulationRunning}
            className="bg-zinc-800 text-zinc-100 shadow-sm hover:bg-zinc-700 disabled:bg-zinc-900 disabled:text-zinc-500"
          >
            Pause Simulation
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={onClear}
            className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800 hover:text-zinc-100"
          >
            Clear Tickets
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={onManualTicket}
            className="border-cyan-600/50 bg-cyan-500/10 text-cyan-200 hover:bg-cyan-500/20 hover:text-cyan-100"
          >
            Manual Ticket
          </Button>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Simulation Speed
            </span>
            <Select value={speed} onValueChange={onSpeedChange}>
              <SelectTrigger className="h-9 w-[140px] border-zinc-700 bg-zinc-900 text-zinc-100">
                <SelectValue placeholder="Select speed" />
              </SelectTrigger>
              <SelectContent className="border-zinc-700 bg-zinc-900 text-zinc-100">
                {SPEED_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Debug Mode
            </span>
            <Switch checked={debugMode} onCheckedChange={onDebugToggle} />
            <Badge
              variant="outline"
              className={
                debugMode
                  ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
                  : "border-zinc-700 bg-zinc-800/70 text-zinc-400"
              }
            >
              {debugMode ? "Enabled" : "Disabled"}
            </Badge>
          </div>
        </div>
      </div>
    </section>
  );
}
