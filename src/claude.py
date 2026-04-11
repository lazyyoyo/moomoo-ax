"""
claude.py — Claude CLI 호출 래퍼

모든 Claude 호출을 이 모듈로 통일. 토큰 + 비용을 항상 반환.
"""

import json
import subprocess
import sys
import time


def call(prompt: str, output_format: str = "json", timeout: int = 300) -> dict:
    """
    Claude CLI 호출.

    Returns:
        {
            "success": bool,
            "output": str,          # 결과 텍스트
            "tokens": {
                "input": int,           # non-cached 입력 (이번 호출에서 새로 흘러들어온)
                "output": int,          # 생성 토큰
                "cache_creation": int,  # 이번 호출에서 캐시에 쓴 양 (비용 있음)
                "cache_read": int,      # 이전 캐시에서 읽은 양 (거의 무료)
            },
            "cost_usd": float,      # Claude CLI 가 계산한 실제 비용 (가장 정확)
            "duration_sec": float,
            "error": str | None,
        }

    주의: input_tokens 만 보면 전체 프롬프트 크기를 크게 과소평가한다.
    Claude CLI 가 system prompt + 도구 정의 대부분을 cache 로 분리하기 때문.
    토큰 효율 비교 시 cost_usd 또는 (input + cache_creation + cache_read) 합산 사용.
    """
    start = time.monotonic()
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", output_format],
        capture_output=True, text=True, timeout=timeout,
    )
    duration = round(time.monotonic() - start, 1)

    empty_tokens = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}

    if result.returncode != 0:
        return {
            "success": False,
            "output": "",
            "tokens": empty_tokens,
            "cost_usd": 0,
            "duration_sec": duration,
            "error": result.stderr.strip()[:500] or f"exit {result.returncode}",
        }

    # JSON 출력 파싱
    if output_format == "json":
        try:
            data = json.loads(result.stdout)
            usage = data.get("usage", {})
            return {
                "success": True,
                "output": data.get("result", ""),
                "tokens": {
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "cache_creation": usage.get("cache_creation_input_tokens", 0),
                    "cache_read": usage.get("cache_read_input_tokens", 0),
                },
                "cost_usd": data.get("total_cost_usd", 0),
                "duration_sec": duration,
                "error": None,
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": result.stdout.strip(),
                "tokens": empty_tokens,
                "cost_usd": 0,
                "duration_sec": duration,
                "error": None,
            }

    # text 출력
    return {
        "success": True,
        "output": result.stdout.strip(),
        "tokens": empty_tokens,
        "cost_usd": 0,
        "duration_sec": duration,
        "error": None,
    }


def call_for_script(prompt: str, timeout: int = 120) -> tuple[str, dict]:
    """
    script.py용. 산출물 텍스트 + 토큰 메타를 분리 반환.
    토큰 정보는 stderr로 출력 (subprocess에서 수집 가능).

    Returns:
        (output_text, {"tokens": {...}, "cost_usd": float})
    """
    result = call(prompt, output_format="json", timeout=timeout)

    meta = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
    }

    # stderr로 메타 출력 (loop.py가 수집)
    print(json.dumps(meta), file=sys.stderr)

    if not result["success"]:
        print(f"Claude 호출 실패: {result['error']}", file=sys.stderr)
        sys.exit(1)

    return result["output"], meta
