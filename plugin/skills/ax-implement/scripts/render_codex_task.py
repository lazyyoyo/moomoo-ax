#!/usr/bin/env python3
"""Render Codex executor/reviewer task files from plugin templates."""

from __future__ import annotations

import argparse
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates"


def block(lines: list[str], fallback: str = "- (none)") -> str:
    clean = [line for line in lines if line.strip()]
    return "\n".join(f"- {line}" for line in clean) if clean else fallback


def render_executor(task_id: str, task_summary: str, relevant_files: list[str], constraints: list[str]) -> str:
    template = (TEMPLATE_DIR / "CODEX_EXECUTOR_TASK_TEMPLATE.md").read_text(encoding="utf-8")
    return (
        template
        .replace("{{TASK_ID}}", task_id)
        .replace("{{TASK_SUMMARY}}", task_summary)
        .replace("{{RELEVANT_FILES}}", block(relevant_files))
        .replace("{{CONSTRAINTS}}", block(constraints))
    )


def render_reviewer(task_id: str, task_summary: str, review_scope: list[str], spec_paths: list[str]) -> str:
    template = (TEMPLATE_DIR / "CODEX_REVIEWER_TASK_TEMPLATE.md").read_text(encoding="utf-8")
    return (
        template
        .replace("{{TASK_ID}}", task_id)
        .replace("{{TASK_SUMMARY}}", task_summary)
        .replace("{{REVIEW_SCOPE}}", block(review_scope))
        .replace("{{SPEC_PATHS}}", block(spec_paths))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render executor/reviewer Codex task prompt")
    parser.add_argument("--role", required=True, choices=["executor", "reviewer"])
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--relevant-file", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--review-scope", action="append", default=[])
    parser.add_argument("--spec-path", action="append", default=[])
    args = parser.parse_args()

    if args.role == "executor":
        rendered = render_executor(
            task_id=args.task_id,
            task_summary=args.task_summary,
            relevant_files=args.relevant_file,
            constraints=args.constraint,
        )
    else:
        rendered = render_reviewer(
            task_id=args.task_id,
            task_summary=args.task_summary,
            review_scope=args.review_scope,
            spec_paths=args.spec_path,
        )

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
