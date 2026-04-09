#!/usr/bin/env python3
"""
worker.py — Claude headless CLI 래퍼 (MVP v0.1)

CPS/PRD + 에이전트 정의를 조립해 Claude CLI headless 호출.
산출물: {files, summary} JSON → 파일 적용 → 결과 stdout 출력.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

AX_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # moomoo-ax/
AGENTS_DIR = AX_ROOT / "agents"
SCHEMA_PATH = AX_ROOT / "harness" / "schemas" / "code_patch.json"


def load_agent(name: str = "coder") -> str:
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text().strip()
    return ""


def get_project_context(project: Path) -> str:
    """프로젝트 구조/스택 요약 생성."""
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

    # src/ 디렉토리 구조 (2레벨까지)
    src = project / "src"
    if src.is_dir():
        dirs = []
        for p in sorted(src.iterdir()):
            if p.is_dir() and not p.name.startswith("."):
                dirs.append(p.name)
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


def call_claude(prompt: str, project: Path) -> dict:
    """Claude CLI headless 호출."""
    cmd = ["claude", "-p", prompt, "--output-format", "json"]

    result = subprocess.run(
        cmd, cwd=project,
        capture_output=True, text=True, timeout=300,
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip() or f"claude exit code {result.returncode}",
            "tokens": {"input": 0, "output": 0},
        }

    try:
        output = json.loads(result.stdout)
        # Claude --output-format json 에서 토큰 정보 추출
        tokens = {
            "input": output.get("input_tokens", 0),
            "output": output.get("output_tokens", 0),
        }
        return {"success": True, "output": output, "tokens": tokens}
    except json.JSONDecodeError:
        return {
            "success": True,
            "raw": result.stdout.strip()[:1000],
            "tokens": {"input": 0, "output": 0},
        }


def apply_patch(project: Path, files: list) -> list:
    """files 배열을 프로젝트에 적용. 적용된 파일 목록 반환."""
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
    """Claude 응답에서 {files, summary} 구조 추출."""
    # 직접 files 키가 있는 경우
    if "files" in output and "summary" in output:
        return output

    # result 키 안에 있는 경우
    if "result" in output:
        text = output["result"]
        if isinstance(text, str):
            # JSON 블록 추출 시도
            import re
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # 전체가 JSON인 경우
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

    return None


def main():
    parser = argparse.ArgumentParser(description="ax 워커 (Claude headless)")
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

    # Claude 호출
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
        # 패치 구조가 아닌 경우 — Claude가 직접 파일 수정했을 수 있음
        result = {
            "success": True,
            "summary": "Claude 직접 수정 (패치 구조 없음)",
            "applied": [],
            "tokens": claude_result.get("tokens", {}),
        }

    json.dump(result, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
