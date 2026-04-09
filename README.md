# moomoo-ax

auto-research 패턴 기반 자율 제품 개발 파이프라인.

## 빠른 시작

**Step 1: 설치**

```bash
/plugin marketplace add https://github.com/lazyyoyo/moomoo-ax
/plugin install moomoo-ax
```

**Step 2: 실행**

```bash
# 자율 빌드 루프
python skills/ax-loop/scripts/orchestrator.py run \
  --project ~/your-project --max-iter 5

# 상태 확인
python skills/ax-loop/scripts/orchestrator.py status \
  --project ~/your-project
```

## 라이선스

MIT
