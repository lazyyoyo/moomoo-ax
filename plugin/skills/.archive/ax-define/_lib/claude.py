"""
plugin 내부 Claude CLI 래퍼.

stdin으로 프롬프트 받고 산출물을 stdout으로, 토큰 메타를 stderr로 출력하는 공통 헬퍼.
plugin은 순정 배포물이므로 외부 의존성 없이 동작.
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
            "output": str,
            "tokens": {"input": int, "output": int},
            "cost_usd": float,
            "duration_sec": float,
            "error": str | None,
        }
    """
    start = time.monotonic()
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", output_format],
        capture_output=True, text=True, timeout=timeout,
    )
    duration = round(time.monotonic() - start, 1)

    if result.returncode != 0:
        return {
            "success": False,
            "output": "",
            "tokens": {"input": 0, "output": 0},
            "cost_usd": 0,
            "duration_sec": duration,
            "error": result.stderr.strip()[:500] or f"exit {result.returncode}",
        }

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
                },
                "cost_usd": data.get("total_cost_usd", 0),
                "duration_sec": duration,
                "error": None,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "output": result.stdout.strip(),
        "tokens": {"input": 0, "output": 0},
        "cost_usd": 0,
        "duration_sec": duration,
        "error": None,
    }


def call_for_script(prompt: str, timeout: int = 120) -> tuple[str, dict]:
    """
    script.py용. 산출물 텍스트 + 토큰 메타를 분리 반환.
    토큰 정보는 stderr로 출력 (runner.py에서 수집 가능).
    """
    result = call(prompt, output_format="json", timeout=timeout)

    meta = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
    }

    print(json.dumps(meta), file=sys.stderr)

    if not result["success"]:
        print(f"Claude 호출 실패: {result['error']}", file=sys.stderr)
        sys.exit(1)

    return result["output"], meta
