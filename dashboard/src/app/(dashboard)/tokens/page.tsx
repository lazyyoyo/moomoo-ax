import { supabase } from "@/lib/supabase";
import type { LevelupRun } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export default async function TokensPage() {
  const { data } = await supabase
    .from("levelup_runs")
    .select("*")
    .eq("type", "iteration")
    .order("created_at", { ascending: false })
    .limit(100);

  const iters = (data ?? []) as LevelupRun[];

  // stage별 집계
  const byStage = new Map<
    string,
    { runs: number; input: number; output: number; cost: number }
  >();

  for (const r of iters) {
    const cur = byStage.get(r.stage) ?? {
      runs: 0,
      input: 0,
      output: 0,
      cost: 0,
    };
    cur.runs += 1;
    const t = r.tokens ?? {};
    for (const part of ["script", "judge", "improve"] as const) {
      cur.input += t[part]?.input ?? 0;
      cur.output += t[part]?.output ?? 0;
    }
    cur.cost += r.cost_usd ?? 0;
    byStage.set(r.stage, cur);
  }

  const totalCost = Array.from(byStage.values()).reduce(
    (s, v) => s + v.cost,
    0
  );
  const totalInput = Array.from(byStage.values()).reduce(
    (s, v) => s + v.input,
    0
  );
  const totalOutput = Array.from(byStage.values()).reduce(
    (s, v) => s + v.output,
    0
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Tokens</h1>
      <p className="text-sm text-muted-foreground mb-6">
        levelup loop 의 토큰 소비와 비용. 북극성 지표의 보조선.
      </p>

      {/* 총합 */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        <Metric label="total cost" value={`$${totalCost.toFixed(4)}`} />
        <Metric label="input tokens" value={totalInput.toLocaleString()} />
        <Metric label="output tokens" value={totalOutput.toLocaleString()} />
      </div>

      {/* stage별 */}
      <section>
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          STAGE별 토큰
        </h2>
        {byStage.size === 0 ? (
          <div className="border border-dashed rounded-md p-6 text-center text-sm text-muted-foreground">
            아직 수집된 iteration 없음
          </div>
        ) : (
          <div className="border rounded-md overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">stage</th>
                  <th className="px-3 py-2 text-right">runs</th>
                  <th className="px-3 py-2 text-right">input</th>
                  <th className="px-3 py-2 text-right">output</th>
                  <th className="px-3 py-2 text-right">cost</th>
                  <th className="px-3 py-2 text-right">avg/run</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(byStage.entries()).map(([stage, v]) => (
                  <tr key={stage} className="border-t">
                    <td className="px-3 py-2 font-mono">{stage}</td>
                    <td className="px-3 py-2 text-right">{v.runs}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {v.input.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      {v.output.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      ${v.cost.toFixed(4)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-muted-foreground">
                      ${(v.cost / v.runs).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-xs text-muted-foreground mt-4">
        주의: Claude CLI의 prompt caching 적용으로 input token 수가 실제 프롬프트 크기보다 작게 집계될 수 있음 (v0.2에서 조사 예정).
      </p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border rounded-md p-4">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-2xl font-bold font-mono">{value}</div>
    </div>
  );
}
