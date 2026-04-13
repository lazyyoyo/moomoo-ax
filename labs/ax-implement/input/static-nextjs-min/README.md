# static-nextjs-min

ax-implement 의 end-to-end fixture. 최소 Next.js + TypeScript + ESLint + vitest.

독립 git repo (moomoo-ax 의 submodule 아님). `versions/v0.3-fixture/plan.md` 의 태스크를 ax-implement 가 소비한다.

## 사용

이 템플릿은 **readonly**. 직접 수정하지 말고 `scripts/ax_product_run.py --fixture <이 경로>` 로 호출. 드라이버가 worktree 를 만들어 격리된 복사본에서 작업한다.

## 첫 setup (최초 1회)

```bash
cd labs/ax-implement/input/static-nextjs-min
git init && git add -A && git commit -m "seed"
```
