"""
loop.py — levelup loop 오케스트레이터

labs/{stage}/의 script.py를 반복 실행 + 개선하여 rubric 점수를 올린다.

사용법:
    python src/loop.py ax-qa --user yoyo --fixture rubato:0065654
    python src/loop.py ax-qa -u yoyo -f rubato:0065654 -n 5 -t 0.9
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from judge import evaluate
from db import log_iteration, log_summary
import claude as claude_api

AX_VERSION = "v0.1"
LABS_DIR = Path(__file__).resolve().parent.parent / "labs"
PYTHON = sys.executable


def read_file(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


def read_dir(path: Path) -> str:
    """디렉토리 하위 모든 파일을 재귀 탐색. '=== FILE: {rel} ===' 마커로 구분."""
    if not path.is_dir():
        return ""
    parts = []
    for f in sorted(path.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            rel = f.relative_to(path)
            parts.append(f"=== FILE: {rel} ===\n{f.read_text().strip()}")
    return "\n\n".join(parts)


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8] if path.exists() else "none"


def run_script(script_py: Path, input_text: str) -> dict:
    """
    script.py 실행. stdin→input, stdout→산출물, stderr→토큰 메타.

    Returns: {"success", "output", "tokens", "cost_usd", "duration_sec"}
    """
    start = time.monotonic()
    result = subprocess.run(
        [PYTHON, str(script_py)],
        input=input_text, capture_output=True, text=True,
        timeout=300, cwd=script_py.parent,
    )
    duration = round(time.monotonic() - start, 1)

    # stderr에서 토큰 메타 파싱
    tokens = {"input": 0, "output": 0}
    cost_usd = 0
    for line in result.stderr.splitlines():
        try:
            meta = json.loads(line)
            if "tokens" in meta:
                tokens["input"] += meta["tokens"].get("input", 0)
                tokens["output"] += meta["tokens"].get("output", 0)
                cost_usd += meta.get("cost_usd", 0)
        except json.JSONDecodeError:
            pass

    if result.returncode != 0:
        # stderr에서 토큰 메타 제외한 에러 메시지
        error_lines = [l for l in result.stderr.splitlines()
                       if not l.strip().startswith("{")]
        return {
            "success": False,
            "output": "",
            "tokens": tokens,
            "cost_usd": cost_usd,
            "duration_sec": duration,
            "error": "\n".join(error_lines)[:500],
        }

    return {
        "success": True,
        "output": result.stdout.strip(),
        "tokens": tokens,
        "cost_usd": round(cost_usd, 6),
        "duration_sec": duration,
    }


def improve_script(program: str, script_py: Path, failed_items: list, output: str) -> dict:
    """실패 항목 기반으로 script.py 개선. 토큰 정보 반환."""
    script_code = script_py.read_text()
    feedback_text = "\n".join(f"- {item['question']}" for item in failed_items)

    prompt = f"""{program}

## 현재 script.py

```python
{script_code}
```

## 이 스크립트가 생성한 산출물

{output[:2000]}

## 루브릭에서 실패한 항목

{feedback_text}

## 지시

위 실패 항목을 통과하도록 script.py를 개선해.
프롬프트 내용, 후처리 로직, 출력 형식 등을 수정.
개선된 script.py 전체 코드를 ```python``` 코드 블록으로 출력해.

## 절대 규칙 (위반 시 무효)

- 산출물은 반드시 stdout (print)으로만 출력해야 한다
- 파일 저장 (open, write, Path.write_text 등)을 절대 하지 마
- stdin으로 입력 받고 stdout으로 출력하는 구조를 유지해
- call_for_script import 구조를 유지해"""

    result = claude_api.call(prompt)

    improve_tokens = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
    }

    if not result["success"]:
        print(f"[개선] 실패: {result['error']}")
        return improve_tokens

    # Python 코드 블록 추출
    match = re.search(r'```python\s*\n(.*?)```', result["output"], re.DOTALL)
    if match:
        script_py.write_text(match.group(1).strip() + "\n")
    elif "def " in result["output"] and "import " in result["output"]:
        script_py.write_text(result["output"].strip() + "\n")
    else:
        print("[개선] script.py 코드 추출 실패")

    return improve_tokens


def get_input_text(lab_dir: Path, input_file: Path | None) -> str:
    if input_file:
        if input_file.is_dir():
            return read_dir(input_file)
        return read_file(input_file)
    return read_dir(lab_dir / "input")


def run(
    stage: str,
    user_name: str,
    fixture_id: str | None = None,
    input_file: Path | None = None,
    output_file: Path | None = None,
    max_iter: int = 10,
    threshold: float = 0.85,
) -> dict:
    """
    단일 stage 의 levelup loop 실행.

    output_file 지정:
      - 주어지면: 프로젝트 산출물로 간주. best 도달 시 해당 경로에 저장.
      - 없으면: 실험 모드. labs/{stage}/best/에 저장.
    """
    lab_dir = LABS_DIR / stage

    if not lab_dir.is_dir():
        print(f"[loop] labs/{stage}/ 없음")
        sys.exit(1)

    program = read_file(lab_dir / "program.md")
    script_py = lab_dir / "script.py"
    rubric_path = lab_dir / "rubric.yml"

    if not script_py.exists():
        print(f"[loop] {script_py} 없음"); sys.exit(1)
    if not rubric_path.exists():
        print(f"[loop] {rubric_path} 없음"); sys.exit(1)

    input_text = get_input_text(lab_dir, input_file)

    logs_dir = lab_dir / "logs"
    best_dir = lab_dir / "best"
    logs_dir.mkdir(exist_ok=True)
    best_dir.mkdir(exist_ok=True)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)

    best_score = 0.0
    best_output = ""
    total_cost = 0.0

    print(f"[loop] stage: {stage}")
    print(f"[loop] user: {user_name}, fixture: {fixture_id or '(none)'}")
    print(f"[loop] max_iter: {max_iter}, threshold: {threshold}")
    print()

    for i in range(1, max_iter + 1):
        print(f"── iteration {i}/{max_iter} ──────────────────────")
        iter_tokens = {"script": {"input": 0, "output": 0},
                       "judge": {"input": 0, "output": 0},
                       "improve": {"input": 0, "output": 0}}
        iter_cost = 0.0

        # 1. script.py 실행
        print("[실행] script.py...")
        sr = run_script(script_py, input_text)
        iter_tokens["script"] = sr["tokens"]
        iter_cost += sr.get("cost_usd", 0)

        if not sr["success"]:
            print(f"[실행] 실패: {sr.get('error', '?')}")
            log_data = {
                "iteration": i, "score": 0.0, "verdict": "crash",
                "failed_items": [{"question": sr.get("error", "")}],
                "tokens": iter_tokens, "cost_usd": round(iter_cost, 6),
                "duration_sec": sr["duration_sec"],
                "script_version": file_hash(script_py),
            }
            (logs_dir / f"{i:03d}.json").write_text(
                json.dumps(log_data, indent=2, ensure_ascii=False))
            log_iteration(
                user_name=user_name,
                stage=stage,
                fixture_id=fixture_id,
                iteration_num=i,
                score=0.0,
                verdict="crash",
                failed_items=[{"question": sr.get("error", "")}],
                tokens=iter_tokens,
                cost_usd=round(iter_cost, 6),
                duration_sec=sr["duration_sec"],
                script_version=file_hash(script_py),
            )

            if program:
                imp = improve_script(program, script_py, [{"question": sr.get("error", "")}], "")
                iter_tokens["improve"] = imp.get("tokens", {"input": 0, "output": 0})
            continue

        output = sr["output"]

        # 2. 평가
        print("[평가] 루브릭...")
        score, failed, judge_meta = evaluate(rubric_path, output)
        iter_tokens["judge"] = judge_meta["tokens"]
        iter_cost += judge_meta["cost_usd"]

        # 3. 판정
        if score > best_score:
            best_score = score
            best_output = output
            verdict = "keep"
            (best_dir / "output.md").write_text(output)
            (best_dir / "script.py").write_text(script_py.read_text())
            (best_dir / "score.txt").write_text(str(score))
            # 프로젝트 산출물 경로 지정된 경우 해당 파일에도 저장
            if output_file:
                output_file.write_text(output)
        else:
            verdict = "discard"

        print(f"[판정] {verdict} — score: {score} (best: {best_score})")
        if failed:
            for item in failed[:5]:
                crit = " [CRITICAL]" if item.get("critical") else ""
                print(f"  ✗ {item['question']}{crit}")

        # 4. 로그
        log_data = {
            "iteration": i, "score": score, "verdict": verdict,
            "failed_items": failed,
            "tokens": iter_tokens, "cost_usd": round(iter_cost, 6),
            "duration_sec": sr["duration_sec"],
            "script_version": file_hash(script_py),
        }
        (logs_dir / f"{i:03d}.json").write_text(
            json.dumps(log_data, indent=2, ensure_ascii=False))
        log_iteration(
            user_name=user_name,
            stage=stage,
            fixture_id=fixture_id,
            iteration_num=i,
            score=score,
            verdict=verdict,
            failed_items=failed,
            tokens=iter_tokens,
            cost_usd=round(iter_cost, 6),
            duration_sec=sr["duration_sec"],
            script_version=file_hash(script_py),
        )

        total_cost += iter_cost

        # 5. 종료 체크
        if score >= threshold:
            print(f"\n[loop] 임계값 도달 ({score} >= {threshold})")
            break

        # 6. script.py 개선 (마지막 iter는 스킵 — 어차피 사용 안 됨)
        if failed and program and i < max_iter:
            print("[개선] script.py 수정...")
            imp = improve_script(program, script_py, failed, output)
            iter_tokens["improve"] = imp.get("tokens", {"input": 0, "output": 0})
            total_cost += imp.get("cost_usd", 0)
            print(f"[개선] 완료 ({file_hash(script_py)})")

        print()

    # summary
    log_summary(
        user_name=user_name,
        stage=stage,
        fixture_id=fixture_id,
        best_score=best_score,
        total_iterations=i,
        total_cost_usd=round(total_cost, 6),
    )

    print(f"\n[loop] 완료 — best: {best_score}, iterations: {i}, cost: ${total_cost:.4f}")

    return {
        "stage": stage,
        "best_score": best_score,
        "best_output": best_output,
        "iterations": i,
        "total_cost_usd": total_cost,
    }


def main():
    parser = argparse.ArgumentParser(prog="loop")
    parser.add_argument("stage", help="stage 이름 (labs/ 하위, 예: ax-qa)")
    parser.add_argument("--user", "-u", required=True, help="yoyo / jojo")
    parser.add_argument("--fixture", "-f",
                        help="fixture 식별자 (예: rubato:0065654)")
    parser.add_argument("--input", "-i", help="입력 파일/디렉토리")
    parser.add_argument("--output", "-o", help="산출물 저장 경로 (product 모드)")
    parser.add_argument("--max-iter", "-n", type=int, default=10)
    parser.add_argument("--threshold", "-t", type=float, default=0.85)

    args = parser.parse_args()
    input_file = Path(args.input).resolve() if args.input else None
    output_file = Path(args.output).resolve() if args.output else None
    run(
        stage=args.stage,
        user_name=args.user,
        fixture_id=args.fixture,
        input_file=input_file,
        output_file=output_file,
        max_iter=args.max_iter,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
