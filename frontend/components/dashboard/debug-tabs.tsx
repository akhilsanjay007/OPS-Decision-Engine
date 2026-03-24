import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { DebugTrace } from "@/types/ops-decision-engine";

type DebugTabsProps = {
  debugTrace: DebugTrace;
};

function CodeBlock({ content }: { content: string }) {
  return (
    <pre className="max-h-[320px] overflow-auto rounded-xl border border-zinc-800 bg-zinc-950/80 p-3 text-xs leading-relaxed text-zinc-200">
      <code>{content}</code>
    </pre>
  );
}

function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export default function DebugTabs({ debugTrace }: DebugTabsProps) {
  return (
    <Card className="border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-zinc-100">Debug Trace</CardTitle>
        <p className="text-xs text-zinc-400">
          Retrieval and generation internals for inspection and diagnostics
        </p>
      </CardHeader>

      <CardContent className="pt-0">
        <Tabs defaultValue="raw-retrieval" className="w-full">
          <TabsList className="mb-3 flex h-auto w-full flex-wrap gap-1 bg-zinc-950/70 p-1">
            <TabsTrigger value="raw-retrieval">Raw Retrieval</TabsTrigger>
            <TabsTrigger value="reranked-results">Reranked Results</TabsTrigger>
            <TabsTrigger value="deduplicated-results">Deduplicated Results</TabsTrigger>
            <TabsTrigger value="prompt">Prompt</TabsTrigger>
            <TabsTrigger value="raw-llm-output">Raw LLM Output</TabsTrigger>
          </TabsList>

          <TabsContent value="raw-retrieval">
            <CodeBlock content={prettyJson(debugTrace.rawRetrieval)} />
          </TabsContent>

          <TabsContent value="reranked-results">
            <CodeBlock content={prettyJson(debugTrace.rerankedResults)} />
          </TabsContent>

          <TabsContent value="deduplicated-results">
            <CodeBlock content={prettyJson(debugTrace.deduplicatedResults)} />
          </TabsContent>

          <TabsContent value="prompt">
            <CodeBlock content={debugTrace.prompt} />
          </TabsContent>

          <TabsContent value="raw-llm-output">
            <CodeBlock content={debugTrace.rawLlmOutput} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
