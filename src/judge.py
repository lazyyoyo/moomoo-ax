"""
judge.py — 루브릭 → LLM Judge → 점수

rubric.yml 항목마다 Claude에게 Yes/No 판정.
점수 = Yes 비율 (0.0 ~ 1.0). critical No → 강제 0점.
토큰 사용량을 집계하여 반환.
"""

import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claude as claude_api


def load_rubric(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text()).get("items", [])


def judge_item(question: str, output: str) -> tuple[bool, dict]:
    """단일 항목 판정. (passed, tokens_meta) 반환."""
    prompt = f"""아래 산출물을 평가해.

## 산출물

{output}

## 질문

{question}

## 규칙

- Yes 또는 No로만 답해. 다른 말 하지 마.
- 산출물에 해당 내용이 명확히 존재하면 Yes, 아니면 No."""

    result = claude_api.call(prompt, timeout=60)

    tokens_meta = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
    }

    if not result["success"]:
        return False, tokens_meta

    return result["output"].strip().lower().startswith("yes"), tokens_meta


def evaluate(rubric_path: Path, output: str) -> tuple[float, list[dict], dict]:
    """
    루브릭 전체 평가.

    Returns:
        (score, failed_items, judge_tokens)
        score: 0.0 ~ 1.0
        failed_items: No 판정 항목 리스트
        judge_tokens: {"tokens": {"input": N, "output": N}, "cost_usd": N}
    """
    items = load_rubric(rubric_path)
    if not items:
        return 0.0, [], {"tokens": {"input": 0, "output": 0}, "cost_usd": 0}

    results = []
    failed = []
    critical_fail = False
    total_input = 0
    total_output = 0
    total_cost = 0

    for item in items:
        passed, meta = judge_item(item["question"], output)
        results.append(passed)
        total_input += meta["tokens"]["input"]
        total_output += meta["tokens"]["output"]
        total_cost += meta["cost_usd"]

        if not passed:
            failed.append(item)
            if item.get("critical", False):
                critical_fail = True

    judge_tokens = {
        "tokens": {"input": total_input, "output": total_output},
        "cost_usd": round(total_cost, 6),
    }

    if critical_fail:
        return 0.0, failed, judge_tokens

    score = round(sum(1 for r in results if r) / len(results), 3)
    return score, failed, judge_tokens


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python judge.py <rubric.yml> <output_file>")
        sys.exit(1)

    score, failed, tokens = evaluate(Path(sys.argv[1]), Path(sys.argv[2]).read_text())
    print(f"Score: {score}")
    print(f"Tokens: {tokens}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for item in failed:
            crit = " [CRITICAL]" if item.get("critical") else ""
            print(f"  - {item['question']}{crit}")
