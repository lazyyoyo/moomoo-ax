# 보안 규칙

## 하드코딩 금지

```
X: const API_KEY = "sk-..."
O: const API_KEY = process.env.API_KEY
```

- 키, 토큰, 시크릿, 쿠키값은 환경 변수로만
- 코드에 직접 넣지 마라
- .env.example에는 변수명만 (값 없이)

## 민감정보 로그 금지

```
X: console.log("Token:", token)
X: console.log("User:", { password, session })
O: console.log("Auth attempt for user:", userId)
```

- 토큰, 비밀번호, 세션값 로그 출력 금지
- 사용자 식별은 ID만 (개인정보 노출 금지)

## env 파일 접근 금지

- .env 파일은 cat/read 하지 않는다
- 변수명만 .env.example에서 확인
- 실제 값이 필요하면 오너에게 요청

## 보안 자동 스캔

커밋 전 시크릿 스캔 권장:
- Gitleaks
- git-secrets
- trufflehog

## 복귀 시 산출물 규칙

| 복귀 대상 | 리셋되는 것 | 유지되는 것 |
|----------|-----------|-----------|
| qa → implement | plan 일부 태스크 재실행 | specs, flows, mockup, API_SPEC 유지 |
| qa → design | flows/mockup 재작업 가능 | specs 유지, 기존 코드는 브랜치에 보존 |
| qa → define | specs 수정 가능 | ROADMAP, brand, strategy 유지 |
| design 내부 루프 | mockup 재작업 | flows 수정 가능, specs 유지 |

원칙: 복귀 시 해당 단계 이전 산출물은 유지. 코드는 revert 안 하고 브랜치에 보존 후 수정.
