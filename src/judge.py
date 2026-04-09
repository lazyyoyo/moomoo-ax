"""
judge.py — 루브릭 → LLM Judge → 점수

rubric.yml 항목마다 Claude에게 Yes/No 판정 요청.
점수 = Yes 비율 (0.0 ~ 1.0). critical No → 강제 실패.
"""

import json
import subprocess
import sys
import yaml
from pathlib import Path


def load_rubric(path: Path) -> list[dict]:
    """rubric.yml 파싱. [{question, critical}, ...]"""
    data = yaml.safe_load(path.read_text())
    return data.get("items", [])


def judge_item(question: str, output: str) -> bool:
    """단일 루브릭 항목에 대해 Claude Judge 호출. Yes=True, No=False."""
    prompt = f"""아래 산출물을 평가해.

## 산출물

{output}

## 질문

{question}

## 규칙

- Yes 또는 No로만 답해. 다른 말 하지 마.
- 산출물에 해당 내용이 명확히 존재하면 Yes, 아니면 No."""

    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True, timeout=60,
    )

    if result.returncode != 0:
        print(f"[judge] Claude 호출 실패: {result.stderr.strip()[:200]}", file=sys.stderr)
        return False

    answer = result.stdout.strip().lower()
    return answer.startswith("yes")


def evaluate(rubric_path: Path, output: str) -> tuple[float, list[dict]]:
    """
    루브릭 전체 평가.

    Returns:
        (score, failed_items)
        score: 0.0 ~ 1.0 (Yes 비율. critical 실패 시 0.0)
        failed_items: No 판정받은 항목 리스트
    """
    items = load_rubric(rubric_path)
    if not items:
        print("[judge] 루브릭 항목 없음", file=sys.stderr)
        return 0.0, []

    results = []
    failed = []
    critical_fail = False

    for item in items:
        question = item["question"]
        is_critical = item.get("critical", False)

        passed = judge_item(question, output)
        results.append(passed)

        if not passed:
            failed.append(item)
            if is_critical:
                critical_fail = True

    if critical_fail:
        return 0.0, failed

    yes_count = sum(1 for r in results if r)
    score = yes_count / len(results)

    return round(score, 3), failed


if __name__ == "__main__":
    """테스트용: python judge.py <rubric.yml> <output_file>"""
    if len(sys.argv) < 3:
        print("Usage: python judge.py <rubric.yml> <output_file>")
        sys.exit(1)

    rubric_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    score, failed = evaluate(rubric_path, output_path.read_text())

    print(f"Score: {score}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for item in failed:
            crit = " [CRITICAL]" if item.get("critical") else ""
            print(f"  - {item['question']}{crit}")
