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
                },
                "cost_usd": data.get("total_cost_usd", 0),
                "duration_sec": duration,
                "error": None,
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": result.stdout.strip(),
                "tokens": {"input": 0, "output": 0},
                "cost_usd": 0,
                "duration_sec": duration,
                "error": None,
            }

    # text 출력
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
