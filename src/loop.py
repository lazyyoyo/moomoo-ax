"""
loop.py — levelup loop 오케스트레이터

labs/{stage}/의 script.py를 반복 실행하고, program.md에 선언된 `improve_target`
(기본: script.py)을 rubric 피드백 기반으로 개선한다.

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

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from judge import evaluate
from db import log_iteration, log_summary
import claude as claude_api

AX_VERSION = "v0.2"
LABS_DIR = Path(__file__).resolve().parent.parent / "labs"
PYTHON = sys.executable

# 언어별 최소 줄수 가드 (improve 후 너무 짧으면 거부)
MIN_LINES = {
    "python": 30,
    "markdown": 40,
    "text": 20,
}


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


def load_program(program_path: Path) -> tuple[dict, str]:
    """
    program.md 로드. frontmatter(---...---)가 있으면 config로 파싱.

    Returns: (config, body)
    """
    if not program_path.exists():
        return {}, ""
    raw = program_path.read_text()
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end != -1:
            try:
                config = yaml.safe_load(raw[4:end]) or {}
            except yaml.YAMLError:
                config = {}
            body = raw[end + 5:].strip()
            return config if isinstance(config, dict) else {}, body
    return {}, raw.strip()


def detect_language(target: Path) -> str:
    suffix = target.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix == ".md":
        return "markdown"
    return "text"


def extract_code_block(output: str, language: str) -> str | None:
    """
    Claude 출력에서 대상 파일 내용을 추출.
    언어 태그가 있는 블록 우선, 없으면 모든 펜스 블록 중 가장 긴 것.

    R5 핵심 가드: 여러 블록이 있으면 **가장 긴 것**을 선택.
    부분 예시 코드(짧음)가 전체 파일(긺)을 덮어쓰는 사고 방지.
    """
    # 언어별 우선 패턴
    lang_patterns = {
        "python": [r'```python\s*\n(.*?)```', r'```py\s*\n(.*?)```'],
        "markdown": [r'```markdown\s*\n(.*?)```', r'```md\s*\n(.*?)```'],
        "text": [],
    }
    for pat in lang_patterns.get(language, []):
        matches = re.findall(pat, output, re.DOTALL)
        if matches:
            return max(matches, key=len).rstrip()

    # 폴백: 언어 태그 없는 모든 펜스 블록 중 최장
    matches = re.findall(r'```[\w+-]*\s*\n(.*?)```', output, re.DOTALL)
    if matches:
        return max(matches, key=len).rstrip()

    return None


def validate_structure(content: str, language: str) -> tuple[bool, str]:
    """
    improve 결과물의 최소 구조 검증. Returns (ok, reason).

    - 공통: 언어별 최소 줄수 가드
    - python: def main( 또는 if __name__ 존재
    - markdown: frontmatter 내 name: 또는 H2 섹션 2개 이상
    """
    lines = content.splitlines()
    min_lines = MIN_LINES.get(language, 20)
    if len(lines) < min_lines:
        return False, f"너무 짧음 ({len(lines)} < {min_lines} 줄)"

    if language == "python":
        if "def main(" not in content and "if __name__" not in content:
            return False, "main() 또는 __name__ guard 없음"

    elif language == "markdown":
        has_frontmatter_name = bool(
            re.search(
                r'^---\s*\n.*?^name:\s*\S',
                content,
                re.MULTILINE | re.DOTALL,
            )
        )
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        if not has_frontmatter_name and h2_count < 2:
            return False, "frontmatter name: 없고 H2 섹션도 2개 미만"

    return True, ""


def backup_and_write(target: Path, content: str) -> None:
    """target을 {target}.prev로 백업하고 새 내용 기록."""
    if target.exists():
        prev = target.with_suffix(target.suffix + ".prev")
        prev.write_text(target.read_text())
    if not content.endswith("\n"):
        content = content + "\n"
    target.write_text(content)


def build_improve_prompt(
    program_body: str,
    target: Path,
    language: str,
    current_content: str,
    failed_items: list,
    output: str,
) -> str:
    """improve 프롬프트 조립. program.md 본문 + 현재 대상 + 실패 항목 + 지시."""
    feedback_text = "\n".join(f"- {item['question']}" for item in failed_items)
    lang_tag = {"python": "python", "markdown": "markdown"}.get(language, "")

    return f"""{program_body}

## 현재 {target.name}

```{lang_tag}
{current_content}
```

## 이 실행이 생성한 산출물

{output[:2000]}

## 루브릭에서 실패한 항목

{feedback_text}

## 개선 지시

위 실패 항목을 통과하도록 `{target.name}` 을 개선해.

**반드시 지킬 것**:
1. 대상 파일 **전체** 를 단일 ```{lang_tag}``` 코드 블록에 담아서 출력해. 일부만 담으면 덮어쓰기가 거부된다.
2. 파일 전체가 유효한 형식이어야 함 (그대로 교체 가능해야 함).
3. program.md 본문에 명시된 불변/계약 조건을 모두 지켜.
"""


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
    tokens = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    cost_usd = 0
    for line in result.stderr.splitlines():
        try:
            meta = json.loads(line)
            if "tokens" in meta:
                for key in ("input", "output", "cache_creation", "cache_read"):
                    tokens[key] += meta["tokens"].get(key, 0)
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


def improve_artifact(
    program_body: str,
    target: Path,
    failed_items: list,
    output: str,
) -> dict:
    """
    실패 항목 기반으로 improve_target 파일을 개선.

    R5 fix: 구조 체크 + 최소 줄수 가드 + 백업. 실패 시 원본 유지.

    Returns: {
        "tokens": {...},
        "cost_usd": float,
        "skipped": bool,
        "skip_reason": str,
    }
    """
    language = detect_language(target)
    current_content = target.read_text() if target.exists() else ""

    prompt = build_improve_prompt(
        program_body, target, language, current_content, failed_items, output
    )
    result = claude_api.call(prompt)

    improve_meta = {
        "tokens": result["tokens"],
        "cost_usd": result["cost_usd"],
        "skipped": False,
        "skip_reason": "",
    }

    if not result["success"]:
        improve_meta["skipped"] = True
        improve_meta["skip_reason"] = f"claude call 실패: {result.get('error', '?')}"
        print(f"[개선] 실패: {result.get('error', '?')}")
        return improve_meta

    new_content = extract_code_block(result["output"], language)
    if new_content is None:
        improve_meta["skipped"] = True
        improve_meta["skip_reason"] = f"{language} 코드 블록 추출 실패"
        print(f"[개선] 코드 블록 추출 실패 — 원본 유지")
        return improve_meta

    ok, reason = validate_structure(new_content, language)
    if not ok:
        improve_meta["skipped"] = True
        improve_meta["skip_reason"] = f"구조 검증 실패: {reason}"
        print(f"[개선] 구조 검증 실패 — {reason} — 원본 유지")
        return improve_meta

    backup_and_write(target, new_content)
    print(f"[개선] 반영 완료 — {target.name} ({len(new_content.splitlines())}줄)")
    return improve_meta


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

    program.md 의 frontmatter 에 `improve_target:` 필드가 있으면 그 경로를
    iteration 간 개선 대상으로 삼는다. 없으면 `script.py` (기존 동작).
    """
    lab_dir = LABS_DIR / stage

    if not lab_dir.is_dir():
        print(f"[loop] labs/{stage}/ 없음")
        sys.exit(1)

    program_config, program_body = load_program(lab_dir / "program.md")
    script_py = lab_dir / "script.py"
    rubric_path = lab_dir / "rubric.yml"

    improve_target_rel = program_config.get("improve_target", "script.py")
    improve_target_path = (lab_dir / improve_target_rel).resolve()

    if not script_py.exists():
        print(f"[loop] {script_py} 없음"); sys.exit(1)
    if not rubric_path.exists():
        print(f"[loop] {rubric_path} 없음"); sys.exit(1)
    if not improve_target_path.exists():
        print(f"[loop] improve_target 없음: {improve_target_path}"); sys.exit(1)

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
    print(f"[loop] improve_target: {improve_target_path.relative_to(LABS_DIR.parent) if LABS_DIR.parent in improve_target_path.parents else improve_target_path}")
    print(f"[loop] max_iter: {max_iter}, threshold: {threshold}")
    print()

    empty_tokens = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    for i in range(1, max_iter + 1):
        print(f"── iteration {i}/{max_iter} ──────────────────────")
        iter_tokens = {
            "script": dict(empty_tokens),
            "judge": dict(empty_tokens),
            "improve": dict(empty_tokens),
        }
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
                "script_version": file_hash(improve_target_path),
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
                script_version=file_hash(improve_target_path),
            )

            if program_body and i < max_iter:
                imp = improve_artifact(
                    program_body,
                    improve_target_path,
                    [{"question": sr.get("error", "")}],
                    "",
                )
                iter_tokens["improve"] = imp.get("tokens", dict(empty_tokens))
                total_cost += imp.get("cost_usd", 0)
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
            (best_dir / improve_target_path.name).write_text(
                improve_target_path.read_text()
            )
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
            "script_version": file_hash(improve_target_path),
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
            script_version=file_hash(improve_target_path),
        )

        total_cost += iter_cost

        # 5. 종료 체크
        if score >= threshold:
            print(f"\n[loop] 임계값 도달 ({score} >= {threshold})")
            break

        # 6. improve_target 개선 (마지막 iter는 스킵 — 어차피 사용 안 됨)
        if failed and program_body and i < max_iter:
            print(f"[개선] {improve_target_path.name} 수정...")
            imp = improve_artifact(program_body, improve_target_path, failed, output)
            iter_tokens["improve"] = imp.get("tokens", dict(empty_tokens))
            total_cost += imp.get("cost_usd", 0)
            if not imp.get("skipped"):
                print(f"[개선] 완료 ({file_hash(improve_target_path)})")

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
