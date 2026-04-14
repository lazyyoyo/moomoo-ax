import { supabase } from "@/lib/supabase";
import type { LevelupRun, ProductRun } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export default async function LivePage() {
  // 최근 30분 내 levelup iteration
  const since = new Date(Date.now() - 30 * 60 * 1000).toISOString();

  const [levelup, product] = await Promise.all([
    supabase
      .from("levelup_runs")
      .select("*")
      .eq("type", "iteration")
      .gte("created_at", since)
      .order("created_at", { ascending: false })
      .limit(10),
    supabase
      .from("product_runs")
      .select("*")
      .eq("status", "running")
      .order("created_at", { ascending: false })
      .limit(10),
  ]);

  const levelupRuns = (levelup.data ?? []) as LevelupRun[];
  const productRuns = (product.data ?? []) as ProductRun[];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Live</h1>
      <p className="text-sm text-muted-foreground mb-6">
        지금 돌고 있는 loop. "자동이되, 보인다" 원칙 — 무개입 ≠ 블랙박스.
      </p>

      <section className="mb-8">
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          LEVELUP LOOP (최근 30분)
        </h2>
        {levelupRuns.length === 0 ? (
          <EmptyState>최근 30분 내 levelup 활동 없음</EmptyState>
        ) : (
          <div className="border rounded-md overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">시각</th>
                  <th className="px-3 py-2">stage</th>
                  <th className="px-3 py-2">fixture</th>
                  <th className="px-3 py-2">iter</th>
                  <th className="px-3 py-2 text-right">score</th>
                  <th className="px-3 py-2">verdict</th>
                </tr>
              </thead>
              <tbody>
                {levelupRuns.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-3 py-2 font-mono text-xs">
                      {new Date(r.created_at).toLocaleTimeString("ko-KR")}
                    </td>
                    <td className="px-3 py-2 font-mono">{r.stage}</td>
                    <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                      {r.fixture_id ?? "-"}
                    </td>
                    <td className="px-3 py-2">{r.iteration_num}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {r.score?.toFixed(2) ?? "-"}
                    </td>
                    <td className="px-3 py-2">
                      <VerdictBadge verdict={r.verdict} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          PRODUCT LOOP (진행 중)
        </h2>
        {productRuns.length === 0 ? (
          <EmptyState>진행 중인 product run 없음</EmptyState>
        ) : (
          <div className="space-y-2">
            {productRuns.map((r) => (
              <div key={r.id} className="border rounded-md p-3">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="font-mono text-sm">{r.command}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {r.project} / {r.user_name}
                    </span>
                    <div className="text-xs text-muted-foreground mt-1 font-mono">
                      stage {r.stage ?? "-"} · started{" "}
                      {new Date(r.started_at).toLocaleTimeString("ko-KR")} · duration{" "}
                      {formatDuration(r.duration_sec)}
                    </div>
                  </div>
                  <StatusBadge status={r.status} />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="border border-dashed rounded-md p-6 text-center text-sm text-muted-foreground">
      {children}
    </div>
  );
}

function VerdictBadge({ verdict }: { verdict: LevelupRun["verdict"] }) {
  if (!verdict) return <span className="text-muted-foreground">-</span>;
  const style: Record<string, string> = {
    keep: "bg-green-500/10 text-green-700 dark:text-green-400",
    discard: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400",
    crash: "bg-red-500/10 text-red-700 dark:text-red-400",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-mono ${style[verdict]}`}
    >
      {verdict}
    </span>
  );
}

function StatusBadge({ status }: { status: ProductRun["status"] }) {
  const style: Record<ProductRun["status"], string> = {
    running: "bg-green-500/10 text-green-700 dark:text-green-400",
    done: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
    failed: "bg-red-500/10 text-red-700 dark:text-red-400",
    cancelled: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-mono ${style[status]}`}>
      {status}
    </span>
  );
}

function formatDuration(value: number | null) {
  if (value == null) return "-";
  if (value < 60) return `${Math.round(value)}s`;
  const min = Math.floor(value / 60);
  const sec = Math.round(value % 60);
  return `${min}m ${sec}s`;
}
