-- v0.4 migration — product_runs 를 product loop 관찰 인프라에 맞게 확장
--
-- 전제:
-- - v0.1 에서 product_runs 테이블은 이미 존재
-- - v0.4 는 drop/recreate 하지 않고 ALTER 기반으로 확장
-- - dashboard/src/lib/supabase.ts 와 scripts/ax_product_run.py 가 이 shape 를 사용

BEGIN;

ALTER TABLE product_runs
  ADD COLUMN IF NOT EXISTS duration_sec numeric,
  ADD COLUMN IF NOT EXISTS num_turns int,
  ADD COLUMN IF NOT EXISTS fixture_id text,
  ADD COLUMN IF NOT EXISTS session_id text,
  ADD COLUMN IF NOT EXISTS tool_call_stats jsonb DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS intervention_count int DEFAULT 0;

-- 기존 nullable 컬럼은 유지하되, v0.4 에서 driver 가 채우는 것을 기대한다.
COMMENT ON COLUMN product_runs.duration_sec IS
  'parent-side driver 가 기록하는 전체 run duration (초)';
COMMENT ON COLUMN product_runs.num_turns IS
  'Claude conductor 세션의 turn 수';
COMMENT ON COLUMN product_runs.fixture_id IS
  'fixture 기반 run 일 때 템플릿 식별자';
COMMENT ON COLUMN product_runs.session_id IS
  'LLM runtime session/thread 식별자 (best-effort)';
COMMENT ON COLUMN product_runs.tool_call_stats IS
  'task/check/review 등 주요 tool 호출 수 요약';
COMMENT ON COLUMN product_runs.intervention_count IS
  '해당 run 에 연결된 intervention 수의 snapshot 또는 후행 집계값';

CREATE INDEX IF NOT EXISTS product_runs_stage_created_idx
  ON product_runs (stage, created_at DESC);

CREATE INDEX IF NOT EXISTS product_runs_session_id_idx
  ON product_runs (session_id);

COMMIT;
