"""
claude.py — Claude CLI 호출 래퍼

모든 Claude 호출을 이 모듈로 통일. 토큰 + 비용 + per-tool 이벤트를 함께 반환.

v0.3 Phase 1 변경점:
- `call()` 시그니처 확장: allowed_tools / permission_mode / plugin_dir / bare /
  setting_sources 키워드 옵션 추가. 기본값은 v0.2 동작과 호환 (옵션 미지정 시
  플래그 추가 안 함).
- `output_format="stream-json"` 지원: per-tool_use / tool_result 이벤트를
  `tool_events` 리스트로 반환하여 감사/회계/디버깅에 사용.
- 반환 shape 에 `tool_events`, `num_turns`, `session_id` 필드 추가.
"""

import json
import subprocess
import sys
import time
from pathlib import Path


EMPTY_TOKENS = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}


def _empty_result(duration: float, error: str | None = None) -> dict:
    return {
        "success": error is None,
        "output": "",
        "tokens": dict(EMPTY_TOKENS),
        "cost_usd": 0,
        "duration_sec": duration,
        "tool_events": [],
        "num_turns": 0,
        "session_id": None,
        "error": error,
    }


def _usage_to_tokens(usage: dict) -> dict:
    return {
        "input": usage.get("input_tokens", 0),
        "output": usage.get("output_tokens", 0),
        "cache_creation": usage.get("cache_creation_input_tokens", 0),
        "cache_read": usage.get("cache_read_input_tokens", 0),
    }


def parse_stream_json(stdout: str) -> dict:
    """
    NDJSON stdout 을 파싱해서 통합 dict 반환.

    Returns:
        {
            "output": str,                # 최종 assistant text reply
            "tokens": {...},              # result event 의 usage 4필드
            "cost_usd": float,
            "tool_events": list[dict],    # per-tool_use → tool_result pair
            "num_turns": int,
            "session_id": str | None,
            "model": str | None,
        }

    각 tool_events entry:
        {
            "tool_name": str,
            "tool_input": dict,
            "tool_result": str | list | None,
            "tool_use_id": str,
            "usage": dict,               # tool_use 를 낸 assistant message 의 usage
        }
    """
    result = {
        "output": "",
        "tokens": dict(EMPTY_TOKENS),
        "cost_usd": 0.0,
        "tool_events": [],
        "num_turns": 0,
        "session_id": None,
        "model": None,
    }
    pending: dict[str, dict] = {}  # tool_use_id → event

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue

        t = evt.get("type")
        st = evt.get("subtype")

        if t == "system" and st == "init":
            result["session_id"] = evt.get("session_id")
            result["model"] = evt.get("model")

        elif t == "assistant":
            msg = evt.get("message", {})
            usage = msg.get("usage", {})
            for block in msg.get("content", []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    tid = block.get("id")
                    pending[tid] = {
                        "tool_name": block.get("name"),
                        "tool_input": block.get("input"),
                        "tool_result": None,
                        "tool_use_id": tid,
                        "usage": usage,
                    }
                elif block.get("type") == "text":
                    # 최종 text reply 는 result event 에서 덮어쓰지만,
                    # stream 중간 text 도 누적 보존 (fallback)
                    txt = block.get("text", "")
                    if txt:
                        result["output"] = txt

        elif t == "user":
            msg = evt.get("message", {})
            content = msg.get("content", [])
            # user message content 는 string 일 수도 있음 (tool_result 가 직접)
            if isinstance(content, str):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    tid = block.get("tool_use_id")
                    if tid in pending:
                        pending[tid]["tool_result"] = block.get("content")
                        result["tool_events"].append(pending.pop(tid))

        elif t == "result":
            # result event 가 최종 진실
            result["output"] = evt.get("result", result["output"])
            result["cost_usd"] = evt.get("total_cost_usd", 0.0)
            result["num_turns"] = evt.get("num_turns", 0)
            result["tokens"] = _usage_to_tokens(evt.get("usage", {}))
            if evt.get("session_id"):
                result["session_id"] = evt["session_id"]

    # orphan tool_use (result 못 받은 것들) 도 append
    for _tid, entry in pending.items():
        result["tool_events"].append(entry)

    return result


def _build_command(
    prompt: str,
    output_format: str,
    allowed_tools: list[str] | None,
    permission_mode: str | None,
    plugin_dir: str | Path | None,
    bare: bool,
    setting_sources: str | None,
    include_hook_events: bool = False,
) -> list[str]:
    cmd = ["claude", "-p", prompt, "--output-format", output_format]
    if output_format == "stream-json":
        cmd.append("--verbose")  # stream-json 은 --verbose 필요
    if allowed_tools:
        cmd.append("--allowedTools")
        cmd.extend(allowed_tools)
    if permission_mode:
        cmd.extend(["--permission-mode", permission_mode])
    if plugin_dir:
        cmd.extend(["--plugin-dir", str(plugin_dir)])
    if bare:
        cmd.append("--bare")
    if setting_sources:
        cmd.extend(["--setting-sources", setting_sources])
    if include_hook_events:
        cmd.append("--include-hook-events")
    return cmd


def call(
    prompt: str,
    *,
    output_format: str = "json",
    timeout: int = 300,
    allowed_tools: list[str] | None = None,
    permission_mode: str | None = None,
    plugin_dir: str | Path | None = None,
    bare: bool = False,
    setting_sources: str | None = None,
    include_hook_events: bool = False,
    cwd: str | Path | None = None,
    stdout_path: str | Path | None = None,
) -> dict:
    """
    Claude CLI 호출.

    Args:
        prompt: -p 로 넘길 프롬프트
        output_format: "json" (기본, 단일 result JSON) / "stream-json" (NDJSON per-event) / "text"
        timeout: subprocess timeout (초)
        allowed_tools: --allowedTools 에 넘길 도구 이름 목록.
            예: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
            또는 필터: ["Bash(git:*)", "Edit"]
            None 이면 플래그 생략 (v0.2 호환 동작).
        permission_mode: "acceptEdits" / "plan" / "auto" / "bypassPermissions" /
            "dontAsk" / "default". None 이면 플래그 생략.
        plugin_dir: `--plugin-dir` 경로. 로컬 플러그인을 세션에 로드.
        bare: --bare 모드. hook/plugin sync/auto-memory/CLAUDE.md 자동 발견 skip.
        setting_sources: "user,project,local" 중 쉼표 구분. 설정 로드 범위 제한.

    Returns:
        {
            "success": bool,
            "output": str,                  # 최종 텍스트
            "tokens": {...},                # 4필드 (input/output/cache_creation/cache_read)
            "cost_usd": float,              # total_cost_usd
            "duration_sec": float,
            "tool_events": list[dict],      # stream-json 일 때만 채워짐, 그 외 []
            "num_turns": int,
            "session_id": str | None,
            "error": str | None,
        }
    """
    start = time.monotonic()
    cmd = _build_command(
        prompt=prompt,
        output_format=output_format,
        allowed_tools=allowed_tools,
        permission_mode=permission_mode,
        plugin_dir=plugin_dir,
        bare=bare,
        setting_sources=setting_sources,
        include_hook_events=include_hook_events,
    )
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )
    except subprocess.TimeoutExpired as e:
        duration = round(time.monotonic() - start, 1)
        return _empty_result(duration, error=f"timeout after {timeout}s: {e}")

    if stdout_path:
        Path(stdout_path).write_text(proc.stdout, encoding="utf-8")

    duration = round(time.monotonic() - start, 1)

    if proc.returncode != 0:
        return _empty_result(
            duration,
            error=proc.stderr.strip()[:500] or f"exit {proc.returncode}",
        )

    if output_format == "stream-json":
        parsed = parse_stream_json(proc.stdout)
        return {
            "success": True,
            "output": parsed["output"],
            "tokens": parsed["tokens"],
            "cost_usd": parsed["cost_usd"],
            "duration_sec": duration,
            "tool_events": parsed["tool_events"],
            "num_turns": parsed["num_turns"],
            "session_id": parsed["session_id"],
            "error": None,
        }

    if output_format == "json":
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {
                "success": True,
                "output": proc.stdout.strip(),
                "tokens": dict(EMPTY_TOKENS),
                "cost_usd": 0,
                "duration_sec": duration,
                "tool_events": [],
                "num_turns": 0,
                "session_id": None,
                "error": None,
            }
        return {
            "success": True,
            "output": data.get("result", ""),
            "tokens": _usage_to_tokens(data.get("usage", {})),
            "cost_usd": data.get("total_cost_usd", 0),
            "duration_sec": duration,
            "tool_events": [],  # json 모드는 per-tool 없음
            "num_turns": data.get("num_turns", 0),
            "session_id": data.get("session_id"),
            "error": None,
        }

    # text 또는 기타
    return {
        "success": True,
        "output": proc.stdout.strip(),
        "tokens": dict(EMPTY_TOKENS),
        "cost_usd": 0,
        "duration_sec": duration,
        "tool_events": [],
        "num_turns": 0,
        "session_id": None,
        "error": None,
    }


def call_for_script(
    prompt: str,
    timeout: int = 120,
    **options,
) -> tuple[str, dict]:
    """
    script.py 용. 산출물 텍스트 + 토큰/tool 메타를 분리 반환.
    토큰 정보는 stderr 로 출력 (loop.py 가 수집).

    Args:
        prompt: -p 프롬프트
        timeout: subprocess timeout
        **options: call() 에 그대로 전달 (output_format, allowed_tools, permission_mode,
            plugin_dir, bare, setting_sources)

    Returns:
        (output_text, {"tokens": {...}, "cost_usd": float,
         "tool_events": list, "num_turns": int})
    """
    result = call(prompt, timeout=timeout, **options)

    meta = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
        "tool_events": result.get("tool_events", []),
        "num_turns": result.get("num_turns", 0),
    }

    # stderr 로 메타 출력 (loop.py 가 수집). tool_events 는 크기 제한 위해 요약만.
    compact_meta = {
        "tokens": meta["tokens"],
        "cost_usd": meta["cost_usd"],
        "num_turns": meta["num_turns"],
        "tool_call_count": len(meta["tool_events"]),
    }
    print(json.dumps(compact_meta), file=sys.stderr)

    if not result["success"]:
        print(f"Claude 호출 실패: {result['error']}", file=sys.stderr)
        sys.exit(1)

    return result["output"], meta
