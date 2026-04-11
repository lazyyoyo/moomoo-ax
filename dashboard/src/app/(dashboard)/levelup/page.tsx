import { supabase } from "@/lib/supabase";
import type { LevelupRun } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export default async function LevelupPage() {
  const [iterations, summaries] = await Promise.all([
    supabase
      .from("levelup_runs")
      .select("*")
      .eq("type", "iteration")
      .order("created_at", { ascending: false })
      .limit(50),
    supabase
      .from("levelup_runs")
      .select("*")
      .eq("type", "summary")
      .order("created_at", { ascending: false })
      .limit(20),
  ]);

  const iters = (iterations.data ?? []) as LevelupRun[];
  const sums = (summaries.data ?? []) as LevelupRun[];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Levelup Loop</h1>
      <p className="text-sm text-muted-foreground mb-6">
        team-ax 플러그인을 개선하는 실험 로그. stage별 script.py + rubric 평가 결과.
      </p>

      <section className="mb-8">
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          RUN SUMMARY (최근 20건)
        </h2>
        {sums.length === 0 ? (
          <EmptyState>아직 완료된 run 없음</EmptyState>
        ) : (
          <div className="border rounded-md overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">시각</th>
                  <th className="px-3 py-2">stage</th>
                  <th className="px-3 py-2">fixture</th>
                  <th className="px-3 py-2 text-right">best</th>
                  <th className="px-3 py-2 text-right">iter</th>
                  <th className="px-3 py-2 text-right">cost</th>
                </tr>
              </thead>
              <tbody>
                {sums.map((s) => (
                  <tr key={s.id} className="border-t">
                    <td className="px-3 py-2 font-mono text-xs">
                      {new Date(s.created_at).toLocaleString("ko-KR")}
                    </td>
                    <td className="px-3 py-2 font-mono">{s.stage}</td>
                    <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                      {s.fixture_id ?? "-"}
                    </td>
                    <td className="px-3 py-2 text-right font-mono font-semibold">
                      {s.best_score?.toFixed(2) ?? "-"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {s.total_iterations}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs">
                      ${s.total_cost_usd?.toFixed(4) ?? "0"}
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
          ITERATIONS (최근 50건)
        </h2>
        {iters.length === 0 ? (
          <EmptyState>아직 실행된 iteration 없음</EmptyState>
        ) : (
          <div className="border rounded-md overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">시각</th>
                  <th className="px-3 py-2">stage</th>
                  <th className="px-3 py-2">fixture</th>
                  <th className="px-3 py-2 text-right">iter</th>
                  <th className="px-3 py-2 text-right">score</th>
                  <th className="px-3 py-2">verdict</th>
                  <th className="px-3 py-2 text-right">cost</th>
                  <th className="px-3 py-2 text-right">dur</th>
                </tr>
              </thead>
              <tbody>
                {iters.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-3 py-2 font-mono text-xs">
                      {new Date(r.created_at).toLocaleString("ko-KR")}
                    </td>
                    <td className="px-3 py-2 font-mono">{r.stage}</td>
                    <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                      {r.fixture_id ?? "-"}
                    </td>
                    <td className="px-3 py-2 text-right">{r.iteration_num}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {r.score?.toFixed(2) ?? "-"}
                    </td>
                    <td className="px-3 py-2">
                      <VerdictBadge verdict={r.verdict} />
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs">
                      ${r.cost_usd?.toFixed(4) ?? "0"}
                    </td>
                    <td className="px-3 py-2 text-right text-xs text-muted-foreground">
                      {r.duration_sec ? `${r.duration_sec}s` : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
