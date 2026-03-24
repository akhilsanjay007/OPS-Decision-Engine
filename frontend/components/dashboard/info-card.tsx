import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type InfoCardProps = {
  title: string;
  content: string;
  className?: string;
};

export default function InfoCard({ title, content, className }: InfoCardProps) {
  return (
    <Card
      className={[
        "border-zinc-800 bg-zinc-900/70 shadow-[0_12px_35px_-24px_rgba(0,0,0,0.9)]",
        className ?? "",
      ].join(" ")}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-sm leading-relaxed text-zinc-200">{content}</p>
      </CardContent>
    </Card>
  );
}
