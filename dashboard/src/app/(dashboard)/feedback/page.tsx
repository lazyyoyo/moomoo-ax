import { supabase } from "@/lib/supabase";
import type { FeedbackBacklog } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export default async function FeedbackPage() {
  const { data } = await supabase
    .from("feedback_backlog")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(50);

  const items = (data ?? []) as FeedbackBacklog[];

  const byStatus = {
    open: items.filter((i) => i.status === "open").length,
    in_progress: items.filter((i) => i.status === "in_progress").length,
    resolved: items.filter((i) => i.status === "resolved").length,
    dismissed: items.filter((i) => i.status === "dismissed").length,
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Feedback</h1>
      <p className="text-sm text-muted-foreground mb-6">
        <code className="bg-muted px-1 rounded">/ax-feedback</code> 백로그. 개선 우선순위 입력 채널.
      </p>

      {/* 상태별 요약 */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <StatusChip label="open" count={byStatus.open} />
        <StatusChip label="in progress" count={byStatus.in_progress} />
        <StatusChip label="resolved" count={byStatus.resolved} />
        <StatusChip label="dismissed" count={byStatus.dismissed} />
      </div>

      {items.length === 0 ? (
        <div className="border border-dashed rounded-md p-8 text-center">
          <div className="text-sm text-muted-foreground mb-3">
            아직 수집된 피드백 없음
          </div>
          <div className="text-xs text-muted-foreground mb-4">
            v0.2에서 <code className="bg-muted px-1 rounded">/ax-feedback</code> 명령으로 수집 시작.
          </div>
          <div className="text-left inline-block text-xs font-mono bg-muted p-3 rounded max-w-md">
            <div className="text-muted-foreground mb-1"># 사용 예</div>
            /ax-feedback &quot;design 단계에서 색상 선택이 너무 어두웠다&quot;
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="border rounded-md p-3">
              <div className="flex justify-between items-start mb-1">
                <div className="flex gap-2 items-center">
                  <PriorityBadge priority={item.priority} />
                  <span className="text-xs text-muted-foreground font-mono">
                    {item.project ?? "-"} / {item.stage ?? "-"}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {new Date(item.created_at).toLocaleDateString("ko-KR")}
                </span>
              </div>
              <div className="text-sm">{item.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusChip({ label, count }: { label: string; count: number }) {
  return (
    <div className="border rounded-md p-3 text-center">
      <div className="text-2xl font-bold font-mono">{count}</div>
      <div className="text-xs text-muted-foreground mt-1">{label}</div>
    </div>
  );
}

function PriorityBadge({ priority }: { priority: "high" | "medium" | "low" }) {
  const style: Record<string, string> = {
    high: "bg-red-500/10 text-red-700",
    medium: "bg-yellow-500/10 text-yellow-700",
    low: "bg-blue-500/10 text-blue-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono ${style[priority]}`}>
      {priority}
    </span>
  );
}
