"""
db.py — Supabase 로그 래퍼

v0.1 스키마: levelup_runs 테이블에 write.
환경 변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

write는 service_role로, RLS 우회.
"""

import json
import os
from pathlib import Path

import urllib.request

# .env 로드 (외부 의존성 없이)
def _load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

_load_env()

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://aqwhjtlpzpcizatvchfb.supabase.co"
)
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

AX_VERSION = "v0.2"


def _post(table: str, payload: dict) -> bool:
    if not SUPABASE_KEY:
        print("[db] SUPABASE_SERVICE_ROLE_KEY 미설정 — 로그 스킵")
        return False

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(payload).encode()

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "return=minimal",
        },
    )

    try:
        urllib.request.urlopen(req)
        return True
    except Exception as e:
        print(f"[db] {table} insert 실패: {e}")
        return False


def log_iteration(
    *,
    user_name: str,
    stage: str,
    fixture_id: str | None,
    iteration_num: int,
    score: float | None,
    verdict: str | None,
    failed_items: list,
    tokens: dict,
    cost_usd: float,
    duration_sec: float | None,
    script_version: str | None,
    ax_version: str = AX_VERSION,
) -> bool:
    """levelup_runs 에 iteration row insert."""
    return _post("levelup_runs", {
        "ax_version": ax_version,
        "user_name": user_name,
        "stage": stage,
        "fixture_id": fixture_id,
        "type": "iteration",
        "iteration_num": iteration_num,
        "score": score,
        "verdict": verdict,
        "failed_items": failed_items,
        "tokens": tokens,
        "cost_usd": cost_usd,
        "duration_sec": duration_sec,
        "script_version": script_version,
    })


def log_summary(
    *,
    user_name: str,
    stage: str,
    fixture_id: str | None,
    best_score: float,
    total_iterations: int,
    total_cost_usd: float,
    ax_version: str = AX_VERSION,
) -> bool:
    """levelup_runs 에 summary row insert."""
    return _post("levelup_runs", {
        "ax_version": ax_version,
        "user_name": user_name,
        "stage": stage,
        "fixture_id": fixture_id,
        "type": "summary",
        "best_score": best_score,
        "total_iterations": total_iterations,
        "total_cost_usd": total_cost_usd,
    })
