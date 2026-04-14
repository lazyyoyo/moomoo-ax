import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseKey);

// =============================================================
// v0.1 스키마 — 3 레이어 (meta / levelup / product)
// =============================================================

export type TokenUsage = {
  input?: number;
  output?: number;
};

export type StageTokenBreakdown = {
  script?: TokenUsage;
  judge?: TokenUsage;
  improve?: TokenUsage;
};

/** levelup loop 실행 로그 (iteration 단위 + summary 단위 한 테이블) */
export type LevelupRun = {
  id: string;
  created_at: string;
  ax_version: string;
  user_name: string;
  stage: string; // ax-init / ax-define / ax-design / ax-implement / ax-qa / ax-deploy
  fixture_id: string | null;
  type: "iteration" | "summary";

  // iteration 전용
  iteration_num: number | null;
  score: number | null;
  verdict: "keep" | "discard" | "crash" | null;
  failed_items: Array<{ question: string; priority?: string }>;
  tokens: StageTokenBreakdown;
  cost_usd: number;
  duration_sec: number | null;
  script_version: string | null;

  // summary 전용
  best_score: number | null;
  total_iterations: number | null;
  total_cost_usd: number | null;
};

/** product loop 실행 로그 — team-ax 플러그인 호출 단위 */
export type ProductRun = {
  id: string;
  created_at: string;
  ax_version: string;
  user_name: string;
  project: string;
  command: string; // /ax-autopilot, /ax-define …
  stage: string | null;
  status: "running" | "done" | "failed" | "cancelled";
  started_at: string;
  finished_at: string | null;
  duration_sec: number | null;
  num_turns: number | null;
  fixture_id: string | null;
  session_id: string | null;
  tool_call_stats: Record<string, unknown> | null;
  intervention_count: number | null;
  input_intent: string | null;
  output_path: string | null;
  tokens: StageTokenBreakdown;
  cost_usd: number;
};

/** /ax-feedback 으로 수집되는 자유 서술 피드백 */
export type FeedbackBacklog = {
  id: string;
  created_at: string;
  user_name: string;
  project: string | null;
  stage: string | null;
  content: string;
  priority: "high" | "medium" | "low";
  status: "open" | "in_progress" | "resolved" | "dismissed";
  resolved_at: string | null;
  resolved_by_version: string | null;
};

/** 오너 개입 자동 diff 캡처 (v0.2부터 수집) */
export type Intervention = {
  id: string;
  created_at: string;
  user_name: string;
  project: string;
  stage: string;
  product_run_id: string | null;
  original_path: string | null;
  final_commit: string | null;
  hunks_added: number;
  hunks_deleted: number;
  lines_added: number;
  lines_deleted: number;
  files_changed: number;
  diff_summary: string | null;
  severity: "minor" | "moderate" | "major" | null;
};
