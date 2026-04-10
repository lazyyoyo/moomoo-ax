"""
db.py — Supabase 로그 래퍼

iterations 테이블에 로그 insert.
환경 변수: SUPABASE_URL, SUPABASE_KEY
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Supabase REST API로 직접 호출 (의존성 최소화)
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

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://aqwhjtlpzpcizatvchfb.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

AX_VERSION = "v0.2"


def insert_log(
    user: str,
    project: str,
    detail: dict,
    ax_version: str = AX_VERSION,
) -> bool:
    """iterations 테이블에 로그 1건 insert."""
    if not SUPABASE_KEY:
        print("[db] SUPABASE_KEY 미설정 — 로그 스킵")
        return False

    url = f"{SUPABASE_URL}/rest/v1/iterations"
    payload = json.dumps({
        "ax_version": ax_version,
        "user": user,
        "project": project,
        "detail": detail,
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
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
        print(f"[db] insert 실패: {e}")
        return False


def log_iteration(user: str, project: str, experiment: str, **kwargs) -> bool:
    """iteration 로그. kwargs가 그대로 detail에 들어감."""
    return insert_log(user, project, {
        "type": "iteration",
        "experiment": experiment,
        **kwargs,
    })


def log_summary(user: str, project: str, experiment: str, **kwargs) -> bool:
    """run 종료 시 summary 로그."""
    return insert_log(user, project, {
        "type": "summary",
        "experiment": experiment,
        **kwargs,
    })
