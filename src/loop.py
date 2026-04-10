"""
loop.py — 범용 오케스트레이터

labs/{stage}/ 디렉토리의 script.py를 반복 실행 + 개선하여 rubric 점수를 올린다.

사용법:
    python src/loop.py seed-gen --project moomoo-ax --user yoyo
    python src/loop.py seed-gen --project moomoo-ax --user yoyo --max-iter 5 --threshold 0.9
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from judge import evaluate
from db import log_iteration, log_summary

AX_VERSION = "v0.2"
LABS_DIR = Path(__file__).resolve().parent.parent / "labs"
PYTHON = sys.executable


def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text().strip()
    return ""


def file_hash(path: Path) -> str:
    if path.exists():
        return hashlib.md5(path.read_bytes()).hexdigest()[:8]
    return "none"


def call_claude(prompt: str) -> dict:
    """Claude CLI 호출."""
    start = time.monotonic()
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True, text=True, timeout=300,
    )
    duration = time.monotonic() - start

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip()[:500] or f"exit {result.returncode}",
            "duration_sec": round(duration, 1),
            "tokens": {"input": 0, "output": 0},
        }

    try:
        data = json.loads(result.stdout)
        tokens = {
            "input": data.get("input_tokens", 0),
            "output": data.get("output_tokens", 0),
        }
        text = data.get("result", result.stdout)
        return {
            "success": True,
            "output": text,
            "duration_sec": round(duration, 1),
            "tokens": tokens,
        }
    except json.JSONDecodeError:
        return {
            "success": True,
            "output": result.stdout.strip(),
            "duration_sec": round(duration, 1),
            "tokens": {"input": 0, "output": 0},
        }


def run_script(script_py: Path, input_file: Path) -> dict:
    """script.py 실행. stdin으로 input 전달, stdout에서 산출물 수신."""
    input_text = read_file(input_file) if input_file.is_file() else ""

    # input 디렉토리인 경우 모든 파일 합치기
    if input_file.is_dir():
        parts = []
        for f in sorted(input_file.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                parts.append(f.read_text().strip())
        input_text = "\n\n---\n\n".join(parts)

    start = time.monotonic()
    result = subprocess.run(
        [PYTHON, str(script_py)],
        input=input_text,
        capture_output=True, text=True,
        timeout=300,
        cwd=script_py.parent,
    )
    duration = time.monotonic() - start

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr.strip()[:500] or f"exit {result.returncode}",
            "duration_sec": round(duration, 1),
        }

    return {
        "success": True,
        "output": result.stdout.strip(),
        "duration_sec": round(duration, 1),
    }


def improve_script(program: str, script_py: Path, failed_items: list, output: str) -> bool:
    """실패 항목 기반으로 script.py 개선. 성공 시 True."""
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
프롬프트 내용, 후처리 로직, 출력 형식 등을 수정해서 다음에 더 나은 산출물이 나오도록 해.
개선된 script.py 전체 코드를 출력해. ```python``` 코드 블록으로 감싸줘."""

    result = call_claude(prompt)
    if not result.get("success"):
        print(f"[개선] Claude 호출 실패: {result.get('error', '?')}")
        return False

    # Python 코드 블록 추출
    text = result["output"]
    import re
    match = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
    if match:
        new_code = match.group(1).strip()
        script_py.write_text(new_code + "\n")
        return True

    # 코드 블록 없으면 전체가 코드인지 시도
    if "def " in text and "import " in text:
        script_py.write_text(text.strip() + "\n")
        return True

    print("[개선] script.py 코드 추출 실패")
    return False


def run(
    stage: str,
    project: str,
    user: str,
    input_file: Path | None = None,
    max_iter: int = 10,
    threshold: float = 0.85,
) -> dict:
    """단일 stage 루프 실행. 결과 dict 반환."""
    lab_dir = LABS_DIR / stage

    if not lab_dir.is_dir():
        print(f"[loop] labs/{stage}/ 없음")
        sys.exit(1)

    program = read_file(lab_dir / "program.md")
    script_py = lab_dir / "script.py"
    rubric_path = lab_dir / "rubric.yml"

    if not script_py.exists():
        print(f"[loop] {script_py} 없음")
        sys.exit(1)
    if not rubric_path.exists():
        print(f"[loop] {rubric_path} 없음")
        sys.exit(1)

    # input: 명시적 파일 > lab_dir/input/
    if input_file is None:
        input_file = lab_dir / "input"

    # 디렉토리 준비
    logs_dir = lab_dir / "logs"
    best_dir = lab_dir / "best"
    logs_dir.mkdir(exist_ok=True)
    best_dir.mkdir(exist_ok=True)

    best_score = 0.0
    best_output = ""
    total_tokens = 0

    print(f"[loop] stage: {stage}")
    print(f"[loop] project: {project}, user: {user}")
    print(f"[loop] max_iter: {max_iter}, threshold: {threshold}")
    print()

    for i in range(1, max_iter + 1):
        print(f"── iteration {i}/{max_iter} ──────────────────────")

        # 1. script.py 실행
        print("[실행] script.py 실행 중...")
        run_result = run_script(script_py, input_file)

        if not run_result.get("success"):
            print(f"[실행] 실패: {run_result.get('error', '?')}")
            # 로그
            log_data = {
                "iteration": i, "score": 0.0, "verdict": "crash",
                "failed_items": [{"question": run_result.get("error", "script 실행 실패")}],
                "tokens_input": 0, "tokens_output": 0,
                "duration_sec": run_result.get("duration_sec", 0),
                "script_version": file_hash(script_py),
            }
            (logs_dir / f"{i:03d}.json").write_text(json.dumps(log_data, indent=2, ensure_ascii=False))
            log_iteration(user=user, project=project, experiment=stage, **log_data)

            # script.py 수정 시도
            if program:
                print("[개선] crash 복구 중...")
                improve_script(program, script_py, [{"question": run_result.get("error", "")}], "")
            continue

        output = run_result["output"]
        duration = run_result["duration_sec"]

        # 2. 평가
        print("[평가] 루브릭 판정 중...")
        score, failed = evaluate(rubric_path, output)

        # 3. 판정
        if score > best_score:
            best_score = score
            best_output = output
            verdict = "keep"
            (best_dir / "output.md").write_text(output)
            (best_dir / "script.py").write_text(script_py.read_text())
            (best_dir / "score.txt").write_text(str(score))
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
            "tokens_input": 0, "tokens_output": 0,
            "duration_sec": duration,
            "script_version": file_hash(script_py),
        }
        (logs_dir / f"{i:03d}.json").write_text(json.dumps(log_data, indent=2, ensure_ascii=False))
        log_iteration(user=user, project=project, experiment=stage, **log_data)

        # 5. 종료 체크
        if score >= threshold:
            print(f"\n[loop] 임계값 도달 ({score} >= {threshold}) — 루프 종료")
            break

        # 6. script.py 개선
        if failed and program:
            print("[개선] script.py 수정 중...")
            improved = improve_script(program, script_py, failed, output)
            if improved:
                print(f"[개선] script.py 업데이트 ({file_hash(script_py)})")

        print()

    # summary
    log_summary(
        user=user, project=project, experiment=stage,
        final_score=best_score, total_iterations=i, total_tokens=total_tokens,
    )

    print(f"\n[loop] 완료 — best: {best_score}, iterations: {i}")

    return {
        "stage": stage,
        "best_score": best_score,
        "best_output": best_output,
        "iterations": i,
    }


def main():
    parser = argparse.ArgumentParser(
        prog="loop",
        description="ax-loop: 단일 stage의 script.py를 루프로 개선",
    )
    parser.add_argument("stage", help="stage 이름 (labs/ 하위 디렉토리)")
    parser.add_argument("--project", "-p", required=True)
    parser.add_argument("--user", "-u", required=True, help="yoyo / jojo")
    parser.add_argument("--input", "-i", help="입력 파일/디렉토리 (기본: labs/{stage}/input/)")
    parser.add_argument("--max-iter", "-n", type=int, default=10)
    parser.add_argument("--threshold", "-t", type=float, default=0.85)

    args = parser.parse_args()
    input_file = Path(args.input).resolve() if args.input else None

    run(args.stage, args.project, args.user, input_file, args.max_iter, args.threshold)


if __name__ == "__main__":
    main()
