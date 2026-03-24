import { Card, CardContent } from "@/components/ui/card";

type AnalysisErrorStateProps = {
  message: string;
};

export default function AnalysisErrorState({ message }: AnalysisErrorStateProps) {
  return (
    <Card className="flex h-full min-h-[420px] items-center justify-center border-amber-500/30 bg-zinc-900/70 shadow-[0_20px_50px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md">
      <CardContent className="max-w-2xl space-y-3.5 px-8 py-12 text-center sm:px-10">
        <p className="text-base font-semibold text-amber-200 sm:text-lg">Analysis could not be completed</p>
        <p className="text-sm leading-relaxed text-zinc-400">{message}</p>
        <p className="text-xs text-zinc-500">
          Confirm the FastAPI backend is running and that <code className="text-zinc-400">NEXT_PUBLIC_API_URL</code>{" "}
          matches its base URL. You can select the ticket again to retry.
        </p>
      </CardContent>
    </Card>
  );
}
