import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Iteration } from "@/lib/supabase";

export function ExperimentCard({ summary }: { summary: Iteration }) {
  const d = summary.detail;
  const statusColor =
    d.status === "completed"
      ? "default"
      : d.status === "failed"
        ? "destructive"
        : "secondary";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{d.experiment}</CardTitle>
          <Badge variant={statusColor}>{d.status}</Badge>
        </div>
        <div className="text-xs text-muted-foreground">
          {summary.project} · {summary.user} · {summary.ax_version}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">Score</div>
            <div className="text-xl font-bold">
              {d.final_score?.toFixed(2) ?? "—"}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Iterations</div>
            <div className="text-xl font-bold">{d.total_iterations ?? "—"}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Cost</div>
            <div className="text-xl font-bold">
              ${d.total_cost_usd?.toFixed(2) ?? "—"}
            </div>
          </div>
        </div>
        <div className="text-xs text-muted-foreground mt-3">
          {new Date(summary.created_at).toLocaleString("ko-KR")}
        </div>
      </CardContent>
    </Card>
  );
}
