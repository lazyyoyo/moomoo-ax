# 플러그인 호환성 가이드

team-ax가 다른 Claude Code 플러그인과 함께 있을 때 발생하는 충돌과 해소 절차.

## 알려진 충돌

### 1. team-design / team-product (my-agent-office 플러그인)

**증상**

- `ax-design` 실행 시 "UX", "디자인" 키워드가 `team-design`의 `ux-reviewer` 에이전트를 자동 트리거
- `team-product`의 `product-design`도 "디자인", "컴포넌트" 키워드로 동일 문제 발생
- 의도한 `ax-design` 플로우가 깨지고 다른 에이전트의 중간 산출물이 컨텍스트를 오염시킴

**원인**

- Claude Code 서브에이전트는 description의 키워드로 자동 선택
- team-design / team-product는 team-ax보다 먼저 설치되어 동일 키워드를 선점
- team-ax가 최종적으로 대체할 영역인데, 전환기에 중첩 상태

**해소 — 대상 프로젝트에서 비활성화**

대상 프로젝트 `.claude/settings.json`에 아래 추가:

```json
{
  "enabledPlugins": {
    "team-design@my-agent-office": false,
    "team-product@my-agent-office": false
  }
}
```

**확인 방법**

```bash
# 프로젝트 루트에서
cat .claude/settings.json | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("enabledPlugins",{}))'
```

`team-design` / `team-product`가 `false`면 비활성. Claude Code 재시작 후 적용.

**참고 — moomoo-ax repo 자체**

이 repo의 `.claude/settings.json`에는 `team-product@my-agent-office: false`만 등록되어 있다. `team-design`은 현재 활성이지만 moomoo-ax 개발 중 ax-design 호출이 드물어 충돌 사례가 없다. 충돌 발견 시 동일 방식으로 추가.

## 장기 계획

team-ax가 define / build / design / qa / deploy 전 범위를 완전 대체한 후 (v1.0+):

1. team-design / team-product 의존성 완전 제거
2. marketplace에서 archive 처리 안내
3. 이 가이드는 legacy 참고로 유지

## 권장 활성 플러그인 (team-ax 사용 시)

| 플러그인 | 상태 | 비고 |
|---|---|---|
| `team-ax@moomoo-ax` | 활성 (필수) | 메인 파이프라인 |
| `codex@jojo-codex` | 활성 (권장) | `ax-review`가 codex에 위임 |
| `playwright@claude-plugins-official` | 활성 (권장) | `ax-qa` 동적 검증 |
| `statusline@my-agent-office` | 선택 | 글로벌 statusline (프로젝트별 statusline과 무관) |
| `team-design@my-agent-office` | **비활성 권장** | ax-design과 충돌 |
| `team-product@my-agent-office` | **비활성 권장** | ax-build/qa와 충돌 |
