# exp-02 — Stateful Multi-file Task

- 날짜: 2026-04-11
- 축: 3
- 상태: **exp-01 Test 3 에서 사실상 증명 완료 → 별도 full 실험 생략**

## 원래 목표

Python 하네스가 Claude 에게 "파일 하나 만들고 내용 적어봐" 지시 → 파일 실제 생성 여부 확인.

## 기 증명됨 — exp-01 Test 3

exp-01 Test 3 (`sandbox/exp01-test3-write.json`) 에서:

- 프롬프트: "Write a new file at sandbox/exp01-child-wrote.txt with contents 'X', then Read it back and echo"
- 결과:
  - `num_turns: 3` → Write + Read + reply 3-step tool loop
  - 디스크 확인: `sandbox/exp01-child-wrote.txt` 실제 생성 (46 bytes, 내용 일치)
  - `result: "파일 내용: 'written by child claude session, exp-01 test 3'"`

즉 "자식 `claude -p` 가 Write tool 로 파일을 생성하고 그 상태를 다음 turn 에서 Read tool 로 활용" 은 **stateful multi-step task 의 최소 케이스** 로서 이미 작동.

## 추가로 증명할 것 (미수행, 선택)

- 3개 이상의 파일 + 의존성 있는 연쇄 (a.txt → b.txt → c = concat(a,b))
- Git 작업 (add/commit)
- 긴 multi-turn (num_turns 10+) 에서 누적 토큰 및 cache behavior

이들은 Path A 선택 이후 v0.3 구현 단계에서 자연스럽게 노출될 문제이므로, **Phase 0 리서치에서는 별도 실험 불필요**.

## 판정

**exp-02: ✅ 성공 (exp-01 Test 3 에 포섭됨)**

Path A 에 대한 독립적 blocker 아님.
