"""
judge.py — 루브릭 → LLM Judge → 점수

rubric.yml 전체를 1회 Claude 호출로 판정.
priority별 가중치: critical(No→즉시 0.0), high(3), medium(2), low(1).
"""

import json
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claude as claude_api

PRIORITY_WEIGHTS = {
    "critical": 0,  # 별도 처리 (No → 0.0)
    "high": 3,
    "medium": 2,
    "low": 1,
}


def load_rubric(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text()).get("items", [])


def evaluate(rubric_path: Path, output: str) -> tuple[float, list[dict], dict]:
    """
    루브릭 전체 평가 (1회 호출).

    Returns:
        (score, failed_items, judge_meta)
        score: 0.0 ~ 1.0 (priority 가중 점수. critical No → 0.0)
        failed_items: No 판정 항목 리스트
        judge_meta: {"tokens": {...}, "cost_usd": N}
    """
    items = load_rubric(rubric_path)
    if not items:
        return 0.0, [], {"tokens": {"input": 0, "output": 0}, "cost_usd": 0}

    # 번호 매겨서 프롬프트 구성
    questions_text = ""
    for idx, item in enumerate(items, 1):
        pri = item.get("priority", "medium")
        questions_text += f"{idx}. [{pri}] {item['question']}\n"

    prompt = f"""아래 산출물을 루브릭 항목별로 평가해.

## 산출물

{output}

## 루브릭 항목

{questions_text}

## 규칙

각 항목에 대해 Yes 또는 No로 판정해.
아래 JSON 형식으로만 답해. 다른 말 하지 마.

```json
{{
  "results": [
    {{"index": 1, "answer": "Yes"}},
    {{"index": 2, "answer": "No"}}
  ]
}}
```"""

    result = claude_api.call(prompt, timeout=120)

    judge_meta = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
    }

    if not result["success"]:
        return 0.0, items, judge_meta

    # JSON 파싱
    answers = _parse_answers(result["output"], len(items))

    # 점수 계산
    failed = []
    critical_fail = False
    weighted_yes = 0
    weighted_total = 0

    for idx, item in enumerate(items):
        pri = item.get("priority", "medium")
        passed = answers.get(idx, False)

        if not passed:
            failed.append(item)
            if pri == "critical":
                critical_fail = True

        if pri != "critical":
            weight = PRIORITY_WEIGHTS.get(pri, 1)
            weighted_total += weight
            if passed:
                weighted_yes += weight

    if critical_fail:
        return 0.0, failed, judge_meta

    score = round(weighted_yes / weighted_total, 3) if weighted_total > 0 else 0.0
    return score, failed, judge_meta


def _parse_answers(text: str, count: int) -> dict[int, bool]:
    """Claude 응답에서 {index: bool} 딕셔너리 추출."""
    import re

    # JSON 블록 추출
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    json_text = match.group(1) if match else text

    try:
        data = json.loads(json_text)
        results = data.get("results", [])
        return {
            r["index"] - 1: r["answer"].lower().startswith("yes")
            for r in results
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # fallback: 줄 단위 Yes/No 파싱
    answers = {}
    for i, line in enumerate(text.strip().splitlines()):
        if i >= count:
            break
        answers[i] = "yes" in line.lower()

    return answers


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python judge.py <rubric.yml> <output_file>")
        sys.exit(1)

    score, failed, meta = evaluate(Path(sys.argv[1]), Path(sys.argv[2]).read_text())
    print(f"Score: {score}")
    print(f"Tokens: {meta}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for item in failed:
            pri = item.get("priority", "medium")
            print(f"  [{pri}] {item['question']}")
