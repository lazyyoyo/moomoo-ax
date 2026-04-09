#!/usr/bin/env python3
"""
worker.py — tmux 기반 Claude 워커 (MVP v0.1)

tmux 세션에서 Claude CLI 실행. 실행 중 `tmux attach -t ax-workers`로 관찰 가능.
산출물: {files, summary} JSON → 파일 적용 → 결과 stdout 출력.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AX_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # moomoo-ax/
AGENTS_DIR = AX_ROOT / "agents"

AX_SESSION = "ax-workers"
OUTPUT_DIR = Path("/tmp/ax-outputs")


# ── tmux 워커 ────────────────────────────────────────

def ensure_session():
    """tmux 세션 없으면 생성."""
    r = subprocess.run(
        ["tmux", "has-session", "-t", AX_SESSION],
        capture_output=True,
    )
    if r.returncode != 0:
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", AX_SESSION],
            capture_output=True,
        )


def call_worker(worker_id: str, cli_cmd: list[str], cwd: Path, timeout: int = 300) -> dict:
    """
    tmux 창에서 CLI 실행 → 결과 파일로 수신.

    실행 중 관찰: tmux attach -t ax-workers
    특정 워커:  tmux select-window -t ax-workers:<worker_id>
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{worker_id}.json"
    exit_file = OUTPUT_DIR / f"{worker_id}.exit"

    # 이전 결과 정리
    for f in [output_file, exit_file]:
        if f.exists():
            f.unlink()

    ensure_session()

    # tmux 새 창에서 워커 실행
    # 결과 → output_file, 종료코드 → exit_file
    cmd_str = " ".join(cli_cmd)
    shell_cmd = (
        f'cd {cwd} && {cmd_str} > {output_file} 2>&1; '
        f'echo $? > {exit_file}'
    )
    subprocess.run([
        "tmux", "new-window", "-t", AX_SESSION,
        "-n", worker_id,
        "bash", "-c", shell_cmd,
    ], capture_output=True)

    # 완료 대기 (폴링)
    elapsed = 0
    while elapsed < timeout:
        if exit_file.exists():
            break
        time.sleep(2)
        elapsed += 2

    if not exit_file.exists():
        return {
            "success": False,
            "error": f"timeout after {timeout}s (tmux attach -t {AX_SESSION} 로 확인)",
            "tokens": {"input": 0, "output": 0},
        }

    exit_code = int(exit_file.read_text().strip())
    output = output_file.read_text() if output_file.exists() else ""

    # 완료된 창 정리
    subprocess.run(
        ["tmux", "kill-window", "-t", f"{AX_SESSION}:{worker_id}"],
        capture_output=True,
    )

    if exit_code != 0:
        return {
            "success": False,
            "error": output.strip()[:2000] or f"exit code {exit_code}",
            "tokens": {"input": 0, "output": 0},
        }

    return {"success": True, "raw_output": output}


# ── 에이전트 / 프롬프트 ─────────────────────────────

def load_agent(name: str = "coder") -> str:
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text().strip()
    return ""


def get_project_context(project: Path) -> str:
    parts = []

    pkg = project / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            parts.append(f"프로젝트: {data.get('name', project.name)}")
            deps = list(data.get("dependencies", {}).keys())[:10]
            if deps:
                parts.append(f"주요 의존성: {', '.join(deps)}")
        except json.JSONDecodeError:
            pass

    src = project / "src"
    if src.is_dir():
        dirs = [p.name for p in sorted(src.iterdir())
                if p.is_dir() and not p.name.startswith(".")]
        if dirs:
            parts.append(f"src/ 구조: {', '.join(dirs[:15])}")

    return "\n".join(parts) if parts else f"프로젝트: {project.name}"


def build_prompt(
    agent_def: str,
    cps_content: str,
    project_context: str,
    prev_errors: list | None = None,
) -> str:
    prompt = f"""{agent_def}

## 작업 컨텍스트

{project_context}

## 요구사항 (CPS/PRD)

{cps_content}

## 출력 형식

파일별 변경사항을 아래 JSON으로 출력:
```json
{{
  "files": [
    {{"path": "상대경로", "action": "create|modify|delete", "content": "전체 파일 내용"}}
  ],
  "summary": "변경 요약 1줄"
}}
```
"""
    if prev_errors:
        prompt += f"""
## 이전 시도 실패 원인 (반드시 수정)

{json.dumps(prev_errors, ensure_ascii=False, indent=2)}
"""
    return prompt


# ── Claude 호출 ──────────────────────────────────────

def call_claude(prompt: str, project: Path) -> dict:
    """Claude CLI를 tmux 워커로 호출."""
    worker_id = f"claude-{int(time.time())}"

    # 프롬프트를 임시 파일로 전달 (길이 제한 회피)
    prompt_file = OUTPUT_DIR / f"{worker_id}.prompt"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt)

    cli_cmd = [
        "claude", "-p", f"$(cat {prompt_file})",
        "--output-format", "json",
    ]

    result = call_worker(worker_id, cli_cmd, cwd=project, timeout=300)

    # 프롬프트 파일 정리
    if prompt_file.exists():
        prompt_file.unlink()

    if not result.get("success", False):
        return result

    # JSON 파싱
    raw = result.get("raw_output", "")
    try:
        output = json.loads(raw)
        tokens = {
            "input": output.get("input_tokens", 0),
            "output": output.get("output_tokens", 0),
        }
        return {"success": True, "output": output, "tokens": tokens}
    except json.JSONDecodeError:
        return {
            "success": True,
            "raw": raw.strip()[:1000],
            "tokens": {"input": 0, "output": 0},
        }


# ── 패치 적용 ────────────────────────────────────────

def apply_patch(project: Path, files: list) -> list:
    applied = []
    for f in files:
        path = project / f["path"]
        action = f.get("action", "modify")

        if action == "delete":
            if path.exists():
                path.unlink()
                applied.append(f"deleted: {f['path']}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f["content"])
            applied.append(f"{action}: {f['path']}")

    return applied


def extract_patch_from_output(output: dict) -> dict | None:
    if "files" in output and "summary" in output:
        return output

    if "result" in output:
        text = output["result"]
        if isinstance(text, str):
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

    return None


# ── CLI ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ax 워커 (tmux + Claude headless)")
    parser.add_argument("--project", required=True, help="대상 프로젝트 경로")
    parser.add_argument("--cps", required=True, help="CPS/PRD 내용")
    parser.add_argument("--prev-errors", help="이전 실패 에러 (JSON 배열)")
    parser.add_argument("--agent", default="coder", help="에이전트 이름")

    args = parser.parse_args()
    project = Path(args.project).resolve()

    prev_errors = None
    if args.prev_errors:
        try:
            prev_errors = json.loads(args.prev_errors)
        except json.JSONDecodeError:
            prev_errors = [args.prev_errors]

    # 프롬프트 조립
    agent_def = load_agent(args.agent)
    project_context = get_project_context(project)
    prompt = build_prompt(agent_def, args.cps, project_context, prev_errors)

    # Claude 호출 (tmux)
    claude_result = call_claude(prompt, project)

    if not claude_result.get("success", False):
        json.dump(claude_result, sys.stdout, ensure_ascii=False)
        sys.exit(1)

    # 패치 추출 + 적용
    output = claude_result.get("output", {})
    patch = extract_patch_from_output(output)

    if patch and "files" in patch:
        applied = apply_patch(project, patch["files"])
        result = {
            "success": True,
            "summary": patch.get("summary", ""),
            "applied": applied,
            "tokens": claude_result.get("tokens", {}),
        }
    else:
        result = {
            "success": True,
            "summary": "Claude 직접 수정 (패치 구조 없음)",
            "applied": [],
            "tokens": claude_result.get("tokens", {}),
        }

    json.dump(result, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
