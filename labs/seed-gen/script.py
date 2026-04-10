"""
seed-gen script.py — 러프 아이디어 → seed.md

stdin으로 러프 아이디어를 받아 구조화된 seed.md를 stdout으로 출력.
"""

import json
import subprocess
import sys


def generate(idea: str) -> str:
    prompt = f"""아래 러프 아이디어를 구조화된 시드 문서로 변환해.

## 러프 아이디어

{idea}

## 출력 형식 (마크다운, 이 구조 정확히 따를 것)

## 한줄 아이디어
(원본 아이디어의 핵심을 한 문장으로)

## 대상 사용자
(누가 이걸 쓸지 1~3문장. 추정이면 "추정:" 접두사)

## 핵심 불만/동기
(왜 이게 필요한지 1~3문장)

## 관련 도메인
(어떤 분야/영역인지)

## 제약 조건
(있다면. 없으면 "특별한 제약 없음")

## 규칙
- 각 항목 1~3문장
- 입력에 없는 정보를 지어내지 마. 합리적 추론만.
- 추정은 "추정:" 접두사로 명시
- 서론/요약 없이 바로 본문"""

    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True, text=True, timeout=120,
    )

    if result.returncode != 0:
        print(f"Claude 호출 실패: {result.stderr[:300]}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
        return data.get("result", result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()


if __name__ == "__main__":
    idea = sys.stdin.read().strip()
    if not idea:
        print("stdin으로 아이디어를 입력해주세요", file=sys.stderr)
        sys.exit(1)
    print(generate(idea))
