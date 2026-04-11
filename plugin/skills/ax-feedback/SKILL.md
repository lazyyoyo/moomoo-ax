---
name: ax-feedback
description: "team-ax 자유 서술 피드백을 feedback_backlog 에 남긴다. Use when: /ax-feedback, 피드백, 개선점 기록, feedback. First argument: 피드백 본문 (필수). Options: --priority {high|medium|low}, --stage <name>, --project <name>"
---

# /ax-feedback

team-ax 파이프라인 사용 중 떠오른 개선점/불만/관찰을 Supabase `feedback_backlog` 에 즉시 기록한다. 북극성 지표(오너 개입 횟수)의 **정성 채널** — "왜 고쳐야 하는가" 를 수집.

## 호출 예

```bash
/ax-feedback "design 단계에서 폰트 선택이 매번 바뀐다"
/ax-feedback --priority high "implement 가 타입 오류 있는 코드를 자꾸 생성"
/ax-feedback --stage ax-implement --project haru "변수명 일관성 없음"
```

## 동작

1. `MOOMOO_AX_ROOT/scripts/ax_feedback.py` 를 moomoo-ax venv 의 python 으로 호출
2. 기본값 자동 추출:
   - `project`: 현재 git repo 이름 (`git rev-parse --show-toplevel` basename)
   - `user_name`: `MOOMOO_AX_USER` 환경변수 → `git config user.name` 매핑 → `yoyo` 폴백
   - `priority`: medium
3. `feedback_backlog` 에 row insert (status=open, created_at=now)
4. 확인 메시지 + row id 출력

## 실행

```bash
/Users/sunha/hq/projects/moomoo-ax/.venv/bin/python \
  /Users/sunha/hq/projects/moomoo-ax/scripts/ax_feedback.py \
  [--priority {high|medium|low}] \
  [--stage <stage_name>] \
  [--project <project_name>] \
  [--user <user_name>] \
  "<feedback content>"
```

**본문이 길면 stdin 으로 파이프**:

```bash
echo "여러 줄 내용..." | /Users/sunha/hq/projects/moomoo-ax/.venv/bin/python \
  /Users/sunha/hq/projects/moomoo-ax/scripts/ax_feedback.py --priority high
```

## 왜 이 채널이 필요한가

자동 diff(`interventions`) 는 "얼마나 고쳤나" 를 정량으로 잡지만 "왜" 를 모른다. `/ax-feedback` 은 오너가 그 순간 느낀 이유/맥락을 직접 캡처한다. 두 채널을 별도로 저장한 뒤 대시보드에서 나란히 본다. 자세한 이유는 `docs/north-star.md`.

## 주의

- 피드백 본문이 비어있으면 에러
- `--priority` 는 high / medium / low 셋 뿐 (DB CHECK 제약)
- priority LLM 자동 추정은 v0.3+ 예정 — v0.2 는 오너 명시만
- status 는 항상 `open` 으로 시작. 전환(`in_progress`, `resolved`, `dismissed`) 은 별도 흐름
