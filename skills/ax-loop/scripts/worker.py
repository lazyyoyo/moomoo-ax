#!/usr/bin/env python3
"""
worker.py — Claude headless CLI 래퍼 (MVP v0.1)

agents/*.md에서 역할 정의를 로드하고, Claude CLI를 headless 호출.
산출물을 JSON으로 stdout에 출력.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

AX_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # moomoo-ax/
AGENTS_DIR = AX_ROOT / "agents"
DEFAULT_AGENT = "coder"


def load_agent(name: str) -> str:
    """agents/{name}.md 로드."""
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text().strip()
    return ""


def build_prompt(
    task: str,
    rework: str | None,
    project_root: Path,
    agent_prompt: str,
) -> str:
    """워커에게 전달할 프롬프트 조립."""
    parts = []

    if agent_prompt:
        parts.append(f"# 역할\n\n{agent_prompt}")

    parts.append(f"# 프로젝트 경로\n\n{project_root}")
    parts.append(f"# 태스크\n\n{task}")

    if rework:
        parts.append(f"# 재작업 지시\n\n이전 시도가 게이트를 통과하지 못했다. 아래 피드백을 반영해서 수정해.\n\n{rework}")

    parts.append(
        "# 규칙\n\n"
        "- 기존 코드를 읽고 이해한 뒤 수정하라\n"
        "- 요청된 변경만 수행하라 (불필요한 리팩토링 금지)\n"
        "- 빌드/린트/타입체크를 통과해야 한다"
    )

    return "\n\n---\n\n".join(parts)


def call_claude(prompt: str, project_root: Path) -> dict:
    """Claude CLI headless 호출."""
    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
    ]

    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=300,  # 5분 타임아웃
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip() or f"claude exit code {result.returncode}",
        }

    # Claude --output-format json은 JSON 객체를 반환
    try:
        output = json.loads(result.stdout)
        return {"success": True, "output": output}
    except json.JSONDecodeError:
        # JSON 파싱 실패해도 코드는 이미 수정됐을 수 있음
        return {"success": True, "raw": result.stdout.strip()[:500]}


def main():
    parser = argparse.ArgumentParser(description="ax 워커 (Claude headless)")
    parser.add_argument("--project-root", required=True, help="대상 프로젝트 루트")
    parser.add_argument("--task", required=True, help="태스크 설명")
    parser.add_argument("--rework", help="재작업 프롬프트 (이전 게이트 실패 피드백)")
    parser.add_argument("--agent", default=DEFAULT_AGENT, help=f"에이전트 이름 (기본: {DEFAULT_AGENT})")

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    # 에이전트 프롬프트 로드
    agent_prompt = load_agent(args.agent)

    # 프롬프트 조립
    prompt = build_prompt(
        task=args.task,
        rework=args.rework,
        project_root=project_root,
        agent_prompt=agent_prompt,
    )

    # Claude 호출
    result = call_claude(prompt, project_root)

    # JSON stdout 출력 (orchestrator가 파싱)
    json.dump(result, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
