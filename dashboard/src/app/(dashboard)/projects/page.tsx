import { supabase } from "@/lib/supabase";
import type { ProductRun } from "@/lib/supabase";

export const dynamic = "force-dynamic";

type ProjectInfo = {
  name: string;
  owner: "yoyo" | "jojo";
  description: string;
};

const KNOWN_PROJECTS: ProjectInfo[] = [
  { name: "rubato", owner: "yoyo", description: "독서 관리 웹앱" },
  { name: "rofan-world", owner: "yoyo", description: "로판 세계관 사이트" },
  { name: "dashboard", owner: "yoyo", description: "실행 추적 대시보드" },
  { name: "moomoo-ax", owner: "yoyo", description: "AI Transformation 엔진" },
  { name: "kudos", owner: "jojo", description: "jojo 프로젝트" },
  { name: "sasasa", owner: "jojo", description: "jojo 프로젝트" },
];

type LatestRunInfo = {
  stage: string | null;
  status: ProductRun["status"];
  command: string;
};

function summarizeQueryError(message?: string | null) {
  const firstLine = message?.split("\n")[0]?.trim();
  if (!firstLine) return "잠시 후 다시 시도해 주세요.";
  return firstLine.slice(0, 120);
}

export default async function ProjectsPage() {
  const { data, error } = await supabase
    .from("product_runs")
    .select("project, user_name, status, command, created_at, cost_usd, stage")
    .order("created_at", { ascending: false })
    .limit(100);

  const runsErrorMessage = error ? summarizeQueryError(error.message) : null;

  const runs = ((error ? [] : data) ?? []) as Pick<
    ProductRun,
    "project" | "user_name" | "status" | "command" | "created_at" | "cost_usd" | "stage"
  >[];

  // 프로젝트별 집계
  const byProject = new Map<
    string,
    {
      total: number;
      running: number;
      lastAt: string | null;
      totalCost: number;
      latestRun: LatestRunInfo | null;
    }
  >();
  for (const r of runs) {
    const cur = byProject.get(r.project) ?? {
      total: 0,
      running: 0,
      lastAt: null,
      totalCost: 0,
      latestRun: null,
    };
    cur.total += 1;
    if (r.status === "running") cur.running += 1;
    if (!cur.lastAt || r.created_at > cur.lastAt) {
      cur.lastAt = r.created_at;
      cur.latestRun = { stage: r.stage, status: r.status, command: r.command };
    }
    cur.totalCost += r.cost_usd ?? 0;
    byProject.set(r.project, cur);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Projects</h1>
      <p className="text-sm text-muted-foreground mb-6">
        team-ax 를 돌린 외부 프로젝트. product loop 사용 현황.
      </p>

      <section className="mb-8">
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          YOYO 프로젝트
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {KNOWN_PROJECTS.filter((p) => p.owner === "yoyo").map((p) => (
            <ProjectCard
              key={p.name}
              info={p}
              stats={byProject.get(p.name)}
              hasQueryError={Boolean(runsErrorMessage)}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">
          JOJO 프로젝트
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {KNOWN_PROJECTS.filter((p) => p.owner === "jojo").map((p) => (
            <ProjectCard
              key={p.name}
              info={p}
              stats={byProject.get(p.name)}
              hasQueryError={Boolean(runsErrorMessage)}
            />
          ))}
        </div>
      </section>

      {runsErrorMessage && (
        <div className="mt-8 border border-red-500/30 rounded-md p-6 text-center text-sm text-red-700 bg-red-500/5">
          product_runs 조회 실패 · {runsErrorMessage}
        </div>
      )}
      {!runsErrorMessage && runs.length === 0 && (
        <div className="mt-8 border border-dashed rounded-md p-6 text-center text-sm text-muted-foreground">
          아직 team-ax 를 돌린 product run 없음. v0.4 에서 관찰 인프라가 붙으면 여기부터 누적된다.
        </div>
      )}
    </div>
  );
}

const STATUS_STYLES: Record<ProductRun["status"], string> = {
  running: "bg-green-500/10 text-green-700",
  done: "bg-muted text-muted-foreground",
  failed: "bg-red-500/10 text-red-700",
  cancelled: "bg-muted text-muted-foreground",
};

function ProjectCard({
  info,
  stats,
  hasQueryError,
}: {
  info: ProjectInfo;
  stats?: {
    total: number;
    running: number;
    lastAt: string | null;
    totalCost: number;
    latestRun: LatestRunInfo | null;
  };
  hasQueryError: boolean;
}) {
  return (
    <div className="border rounded-md p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="font-semibold font-mono">{info.name}</div>
          <div className="text-xs text-muted-foreground">{info.description}</div>
        </div>
        {stats && stats.running > 0 && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-700">
            running
          </span>
        )}
      </div>

      {stats?.latestRun && (
        <div className="flex items-center gap-1.5 mt-2 flex-wrap">
          {stats.latestRun.stage && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 font-mono">
              {stats.latestRun.stage}
            </span>
          )}
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full ${STATUS_STYLES[stats.latestRun.status]}`}
          >
            {stats.latestRun.status}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground">
            {stats.latestRun.command}
          </span>
        </div>
      )}

      {stats ? (
        <div className="text-xs text-muted-foreground mt-2">
          총 {stats.total} runs · 마지막{" "}
          {stats.lastAt
            ? new Date(stats.lastAt).toLocaleDateString("ko-KR")
            : "-"}
          {" "}· 누적 비용 ${stats.totalCost.toFixed(2)}
        </div>
      ) : (
        <div className="text-xs text-muted-foreground mt-2">
          {hasQueryError ? "실행 기록 조회 실패" : "아직 실행 기록 없음"}
        </div>
      )}
    </div>
  );
}
