import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ActionsCardProps = {
  title: string;
  items: string[];
};

export default function ActionsCard({ title, items }: ActionsCardProps) {
  return (
    <Card className="border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          {title}
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-0">
        {items.length === 0 ? (
          <p className="text-sm text-zinc-500">No items available.</p>
        ) : (
          <ul className="space-y-2.5">
            {items.map((item, index) => (
              <li key={`${title}-${index}`} className="flex items-start gap-2.5">
                <span
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400"
                  aria-hidden
                />
                <span className="text-sm leading-relaxed text-zinc-200">{item}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
