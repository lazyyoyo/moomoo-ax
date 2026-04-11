-- v0.1 Supabase 스키마
-- moomoo-ax 3 레이어에 맞춰 재설계
-- 기존 iterations 테이블은 drop

-- 0. 기존 테이블 정리
DROP TABLE IF EXISTS iterations CASCADE;

-- =============================================================
-- 1. levelup_runs — levelup loop 실행 로그
-- =============================================================
-- labs/ax-*/ 의 script.py를 개선하는 루프 기록.
-- iteration 단위와 run 전체 summary 모두 같은 테이블에 type으로 구분.

CREATE TABLE levelup_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),

  ax_version text NOT NULL,                         -- 'v0.1'
  user_name text NOT NULL,                          -- 'yoyo'
  stage text NOT NULL,                              -- 'ax-qa', 'ax-define' …
  fixture_id text,                                  -- 'rubato:0065654' 등 실험 대상 식별자

  type text NOT NULL
    CHECK (type IN ('iteration', 'summary')),

  -- iteration 전용
  iteration_num int,
  score numeric,
  verdict text
    CHECK (verdict IS NULL OR verdict IN ('keep', 'discard', 'crash')),
  failed_items jsonb DEFAULT '[]'::jsonb,
  tokens jsonb DEFAULT '{}'::jsonb,                 -- {script, judge, improve: {input, output}}
  cost_usd numeric DEFAULT 0,
  duration_sec numeric,
  script_version text,                              -- md5 8자리

  -- summary 전용
  best_score numeric,
  total_iterations int,
  total_cost_usd numeric
);

CREATE INDEX levelup_runs_stage_created_idx
  ON levelup_runs (stage, created_at DESC);
CREATE INDEX levelup_runs_type_idx
  ON levelup_runs (type);


-- =============================================================
-- 2. product_runs — product loop 실행 로그
-- =============================================================
-- 사용자가 team-ax 플러그인을 돌린 기록.
-- /ax-autopilot, /ax-define 같은 호출 단위.

CREATE TABLE product_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),

  ax_version text NOT NULL,
  user_name text NOT NULL,                          -- 'yoyo' / 'jojo'
  project text NOT NULL,                            -- 'rubato', 'rofan-world' …
  command text NOT NULL,                            -- '/ax-autopilot', '/ax-define' …
  stage text,                                       -- ax-autopilot일 때 현재 돌고 있는 stage
  status text NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'done', 'failed', 'cancelled')),

  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,

  input_intent text,                                -- 오너가 전달한 의도
  output_path text,                                 -- 산출물 저장 경로
  tokens jsonb DEFAULT '{}'::jsonb,
  cost_usd numeric DEFAULT 0
);

CREATE INDEX product_runs_user_project_idx
  ON product_runs (user_name, project, created_at DESC);
CREATE INDEX product_runs_status_idx
  ON product_runs (status);


-- =============================================================
-- 3. feedback_backlog — 사용자 피드백 큐
-- =============================================================
-- /ax-feedback 으로 수집하는 자유 서술 피드백.
-- 북극성 지표의 정량 수치가 아니라, 개선 우선순위 입력 역할.

CREATE TABLE feedback_backlog (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),

  user_name text NOT NULL,
  project text,                                     -- nullable
  stage text,                                       -- nullable (어느 stage에 대한 피드백)

  content text NOT NULL,                            -- 자유 서술
  priority text NOT NULL DEFAULT 'medium'
    CHECK (priority IN ('high', 'medium', 'low')),
  status text NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'in_progress', 'resolved', 'dismissed')),

  resolved_at timestamptz,
  resolved_by_version text                          -- 'v0.3' 등 해결된 버전
);

CREATE INDEX feedback_backlog_status_priority_idx
  ON feedback_backlog (status, priority, created_at DESC);


-- =============================================================
-- 4. interventions — 오너 개입 자동 diff 캡처
-- =============================================================
-- plugin 산출물 vs 최종 커밋의 diff 기록.
-- 북극성 지표(오너 개입 횟수)의 정량 측정 소스.
-- v0.1은 스키마만. 실제 수집은 v0.2부터.

CREATE TABLE interventions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),

  user_name text NOT NULL,
  project text NOT NULL,
  stage text NOT NULL,                              -- 어느 stage 산출물에 대한 개입인지
  product_run_id uuid
    REFERENCES product_runs(id) ON DELETE SET NULL,

  original_path text,                               -- plugin이 생성한 원본 경로
  final_commit text,                                -- 오너가 최종 커밋한 sha

  -- diff 통계
  hunks_added int DEFAULT 0,
  hunks_deleted int DEFAULT 0,
  lines_added int DEFAULT 0,
  lines_deleted int DEFAULT 0,
  files_changed int DEFAULT 0,

  diff_summary text,                                -- (v0.3+) LLM 요약
  severity text                                     -- (v0.3+) LLM 판정
    CHECK (severity IS NULL OR severity IN ('minor', 'moderate', 'major'))
);

CREATE INDEX interventions_project_stage_idx
  ON interventions (project, stage, created_at DESC);


-- =============================================================
-- RLS 정책
-- =============================================================
-- 전략: service_role과 anon 분리.
-- - dashboard (anon): SELECT만 허용
-- - src/db.py (service_role): RLS 자동 우회, 모든 write 가능
-- - delete는 아무도 허용 안 함 (실수 방지)

ALTER TABLE levelup_runs      ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_runs      ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_backlog  ENABLE ROW LEVEL SECURITY;
ALTER TABLE interventions     ENABLE ROW LEVEL SECURITY;

-- anon: 읽기만
CREATE POLICY "levelup_runs_anon_select"     ON levelup_runs     FOR SELECT TO anon USING (true);
CREATE POLICY "product_runs_anon_select"     ON product_runs     FOR SELECT TO anon USING (true);
CREATE POLICY "feedback_backlog_anon_select" ON feedback_backlog FOR SELECT TO anon USING (true);
CREATE POLICY "interventions_anon_select"    ON interventions    FOR SELECT TO anon USING (true);

-- service_role은 RLS 우회하므로 별도 정책 불필요 (src/db.py에서 사용)
