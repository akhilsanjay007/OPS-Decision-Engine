import { Card, CardContent } from "@/components/ui/card";

export default function EmptyState() {
  return (
    <Card className="flex h-full min-h-[420px] items-center justify-center border-zinc-800/90 bg-zinc-900/70 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md">
      <CardContent className="max-w-2xl space-y-3.5 px-8 py-12 text-center sm:px-10">
        <p className="text-base font-semibold text-zinc-100 sm:text-lg">
          Select an incoming ticket to analyze with the Ops Decision Engine.
        </p>
        <p className="text-sm leading-relaxed text-zinc-400">
          The system will predict priority, retrieve similar incidents, and generate action guidance for a faster, more confident operational response.
        </p>
      </CardContent>
    </Card>
  );
}
