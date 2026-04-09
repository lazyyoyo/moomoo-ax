"""
loop.py — 범용 오케스트레이터

labs/{experiment}/ 디렉토리에서 루프 실행.
script.md를 반복 개선하여 rubric 점수를 올린다.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 같은 src/ 안의 모듈
sys.path.insert(0, str(Path(__file__).parent))
from judge import evaluate
from db import log_iteration, log_summary

AX_VERSION = "v0.2"


def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text().strip()
    return ""


def read_dir(path: Path) -> str:
    """디렉토리 안의 모든 파일 내용을 합쳐서 반환."""
    if not path.is_dir():
        return ""
    parts = []
    for f in sorted(path.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            parts.append(f"## {f.name}\n\n{f.read_text().strip()}")
    return "\n\n---\n\n".join(parts)


def script_hash(script: str) -> str:
    return hashlib.md5(script.encode()).hexdigest()[:8]


def call_claude(prompt: str) -> dict:
    """Claude CLI 호출. {success, output, tokens}"""
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
        # result 키에서 텍스트 추출
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


def generate_output(program: str, script: str, input_ctx: str, feedback: list | None) -> dict:
    """script.md 기반으로 산출물 생성."""
    prompt = f"""{program}

## 생성 스크립트

{script}

## 입력

{input_ctx}"""

    if feedback:
        feedback_text = "\n".join(f"- {item['question']}" for item in feedback)
        prompt += f"""

## 이전 시도에서 실패한 항목 (반드시 개선)

{feedback_text}"""

    prompt += """

## 지시

위 생성 스크립트의 절차를 따라 산출물을 생성해. 스크립트에 정의된 출력 형식을 준수해."""

    return call_claude(prompt)


def improve_script(program: str, script: str, failed_items: list, output: str) -> dict:
    """실패 항목 기반으로 script.md 개선."""
    feedback_text = "\n".join(f"- {item['question']}" for item in failed_items)

    prompt = f"""{program}

## 현재 스크립트

{script}

## 이 스크립트로 생성한 산출물 (일부)

{output[:2000]}

## 루브릭에서 실패한 항목

{feedback_text}

## 지시

위 실패 항목을 통과하도록 스크립트를 개선해.
스크립트의 절차, 규칙, 출력 형식을 수정해서 다음에 더 나은 산출물이 나오도록 해.
개선된 스크립트 전체를 출력해. 마크다운 형식."""

    return call_claude(prompt)


def run(
    lab_dir: Path,
    project: str,
    user: str,
    max_iter: int = 10,
    threshold: float = 0.85,
):
    """루프 실행."""
    program = read_file(lab_dir / "program.md")
    script = read_file(lab_dir / "script.md")
    rubric_path = lab_dir / "rubric.yml"
    input_ctx = read_dir(lab_dir / "input")

    if not program:
        print("[loop] program.md 없음")
        sys.exit(1)
    if not script:
        print("[loop] script.md 없음")
        sys.exit(1)
    if not rubric_path.exists():
        print("[loop] rubric.yml 없음")
        sys.exit(1)

    # 디렉토리 준비
    logs_dir = lab_dir / "logs"
    best_dir = lab_dir / "best"
    logs_dir.mkdir(exist_ok=True)
    best_dir.mkdir(exist_ok=True)

    experiment = lab_dir.name
    best_score = 0.0
    feedback = None
    total_tokens = 0

    print(f"[loop] 실험: {experiment}")
    print(f"[loop] 프로젝트: {project}, 유저: {user}")
    print(f"[loop] 최대 반복: {max_iter}, 임계값: {threshold}")
    print()

    for i in range(1, max_iter + 1):
        print(f"── iteration {i}/{max_iter} ──────────────────────")

        # 1. 산출물 생성
        print("[생성] Claude 호출 중...")
        gen_result = generate_output(program, script, input_ctx, feedback)

        if not gen_result.get("success"):
            print(f"[생성] 실패: {gen_result.get('error', '?')}")
            continue

        output = gen_result["output"]
        tokens = gen_result["tokens"]
        duration = gen_result["duration_sec"]
        total_tokens += tokens.get("input", 0) + tokens.get("output", 0)

        # 2. 평가
        print("[평가] 루브릭 판정 중...")
        score, failed = evaluate(rubric_path, output)

        # 3. 판정
        if score > best_score:
            best_score = score
            verdict = "keep"
            # best 저장
            (best_dir / "output.md").write_text(output)
            (best_dir / "script.md").write_text(script)
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
            "iteration": i,
            "score": score,
            "verdict": verdict,
            "failed_items": failed,
            "tokens_input": tokens.get("input", 0),
            "tokens_output": tokens.get("output", 0),
            "duration_sec": duration,
            "script_version": script_hash(script),
        }

        # 로컬 로그
        log_file = logs_dir / f"{i:03d}.json"
        log_file.write_text(json.dumps(log_data, indent=2, ensure_ascii=False))

        # Supabase 로그
        log_iteration(
            user=user, project=project, experiment=experiment,
            **{k: v for k, v in log_data.items()},
        )

        # 5. 종료 체크
        if score >= threshold:
            print(f"\n[loop] 임계값 도달 ({score} >= {threshold}) — 루프 종료")
            break

        # 6. 스크립트 개선
        if failed:
            print("[개선] 스크립트 수정 중...")
            improve_result = improve_script(program, script, failed, output)
            if improve_result.get("success"):
                script = improve_result["output"]
                # 개선된 스크립트를 lab에도 저장
                (lab_dir / "script.md").write_text(script)
                total_tokens += (
                    improve_result["tokens"].get("input", 0)
                    + improve_result["tokens"].get("output", 0)
                )

        feedback = failed
        print()

    # summary 로그
    log_summary(
        user=user, project=project, experiment=experiment,
        final_score=best_score,
        total_iterations=i,
        total_tokens=total_tokens,
    )

    print(f"\n[loop] 완료 — best score: {best_score}, iterations: {i}, tokens: {total_tokens}")
    return best_score


def main():
    parser = argparse.ArgumentParser(prog="loop", description="ax-loop 오케스트레이터")
    parser.add_argument("lab_dir", help="실험 디렉토리 (labs/cps-gen 등)")
    parser.add_argument("--project", "-p", required=True, help="프로젝트명")
    parser.add_argument("--user", "-u", required=True, help="실행자 (yoyo/jojo)")
    parser.add_argument("--max-iter", "-n", type=int, default=10)
    parser.add_argument("--threshold", "-t", type=float, default=0.85)

    args = parser.parse_args()
    lab_dir = Path(args.lab_dir).resolve()

    if not lab_dir.is_dir():
        print(f"[loop] 디렉토리 없음: {lab_dir}")
        sys.exit(1)

    run(lab_dir, args.project, args.user, args.max_iter, args.threshold)


if __name__ == "__main__":
    main()
