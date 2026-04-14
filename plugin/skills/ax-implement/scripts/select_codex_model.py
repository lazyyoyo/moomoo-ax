#!/usr/bin/env python3
"""Select a Codex model for ax-implement executor/reviewer workers."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


FAST_MODEL = os.environ.get("AX_CODEX_FAST_MODEL", "gpt-5.4-mini")
STRONG_MODEL = os.environ.get("AX_CODEX_STRONG_MODEL", "gpt-5.3-codex")
FINAL_REVIEW_MODEL = os.environ.get("AX_CODEX_FINAL_REVIEW_MODEL", "gpt-5.4")
FAST_PROFILE = os.environ.get("AX_CODEX_FAST_PROFILE", "")
STRONG_PROFILE = os.environ.get("AX_CODEX_STRONG_PROFILE", "")
FINAL_REVIEW_PROFILE = os.environ.get("AX_CODEX_FINAL_REVIEW_PROFILE", "")

HIGH_RISK_SUMMARY_KEYWORDS = (
    "component",
    "컴포넌트",
    "shared",
    "공용",
    "design system",
    "design-system",
    "token",
    "provider",
    "config",
    "tsconfig",
    "package.json",
    "dependency",
    "schema",
    "migration",
    "auth",
    "middleware",
    "api",
    "security",
    "globals.css",
    "layout",
)

LOW_RISK_SUMMARY_KEYWORDS = (
    "page",
    "페이지",
    "copy",
    "문구",
    "test",
    "테스트",
    "story",
    "example",
    "demo",
    "wiring",
    "홈",
)

HIGH_RISK_FILE_MARKERS = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "tsconfig",
    "next.config",
    "eslint.config",
    ".eslintrc",
    "middleware.",
    "globals.css",
    "src/components/",
    "src/lib/",
    "src/server/",
    "src/auth/",
    "src/db/",
    "src/app/api/",
)

LOW_RISK_FILE_MARKERS = (
    "/page.tsx",
    "/loading.tsx",
    "/error.tsx",
    ".test.",
    ".spec.",
    "/stories/",
    "/example",
    "/examples/",
    "/demo",
    "/demos/",
)


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip().lower()


def _summary_flags(task_id: str, task_summary: str) -> tuple[bool, bool, list[str]]:
    summary = task_summary.lower()
    reasons: list[str] = []

    if task_id == "stage-final-review":
        reasons.append("stage-final-review is always high risk")
        return True, False, reasons

    high = False
    low = False

    for keyword in HIGH_RISK_SUMMARY_KEYWORDS:
        if keyword in summary:
            high = True
            reasons.append(f"task summary matched high-risk keyword: {keyword}")
            break

    if not high:
        for keyword in LOW_RISK_SUMMARY_KEYWORDS:
            if keyword in summary:
                low = True
                reasons.append(f"task summary matched low-risk keyword: {keyword}")
                break

    return high, low, reasons


def _file_flags(files: list[str]) -> tuple[bool, bool, list[str]]:
    normalized = [normalize_path(path) for path in files if path.strip()]
    reasons: list[str] = []

    if not normalized:
        return False, False, reasons

    high = False
    for path in normalized:
        for marker in HIGH_RISK_FILE_MARKERS:
            if marker in path:
                high = True
                reasons.append(f"scope file matched high-risk marker: {marker}")
                break
        if high:
            break

    if high:
        return True, False, reasons

    all_low = True
    any_low = False
    for path in normalized:
        matched = any(marker in path for marker in LOW_RISK_FILE_MARKERS)
        any_low = any_low or matched
        all_low = all_low and matched

    if all_low and any_low:
        reasons.append("all scope files matched low-risk markers")
        return False, True, reasons

    return False, False, reasons


def select_model(role: str, task_id: str, task_summary: str, files: list[str]) -> dict:
    summary_high, summary_low, summary_reasons = _summary_flags(task_id, task_summary)
    file_high, file_low, file_reasons = _file_flags(files)

    high_risk = summary_high or file_high
    low_risk = not high_risk and (summary_low or file_low)
    reasons = [*summary_reasons, *file_reasons]

    if role == "reviewer":
        if task_id == "stage-final-review":
            tier = "final-review"
            model = FINAL_REVIEW_MODEL
            profile = FINAL_REVIEW_PROFILE or None
        elif high_risk:
            tier = "strong"
            model = STRONG_MODEL
            profile = STRONG_PROFILE or None
        else:
            tier = "fast"
            model = FAST_MODEL
            profile = FAST_PROFILE or None
    elif role == "executor":
        if high_risk:
            tier = "strong"
            model = STRONG_MODEL
            profile = STRONG_PROFILE or None
        elif low_risk:
            tier = "fast"
            model = FAST_MODEL
            profile = FAST_PROFILE or None
        else:
            tier = "strong"
            model = STRONG_MODEL
            profile = STRONG_PROFILE or None
            reasons.append("executor defaulted to strong model because risk was ambiguous")
    else:
        raise ValueError(f"unsupported role: {role}")

    return {
        "role": role,
        "task_id": task_id,
        "tier": tier,
        "model": model,
        "profile": profile,
        "risk": "high" if high_risk else "low" if low_risk else "ambiguous",
        "reasons": reasons or ["used default routing policy"],
        "scope_files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select Codex model for ax-implement worker")
    parser.add_argument("--role", required=True, choices=["executor", "reviewer"])
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-summary", default="")
    parser.add_argument("--relevant-file", action="append", default=[])
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = select_model(
        role=args.role,
        task_id=args.task_id,
        task_summary=args.task_summary,
        files=[*args.relevant_file, *args.changed_file],
    )

    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
