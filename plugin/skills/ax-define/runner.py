"""
ax-define runner.py — Define 파이프라인 5단계 실행기

사용:
    # 전체 파이프라인 (Stage 1~5, Stage 3 뒤 PO 게이트)
    python runner.py --idea "러프 아이디어" --output-dir ./strategy

    # 특정 stage만 실행
    python runner.py --stage seed-gen --input idea.md --output strategy/seed.md

    # PO 게이트 없이 전체 자동
    python runner.py --idea "..." --output-dir ./strategy --no-gate

stage 순서: seed-gen → jtbd-gen → problem-frame → [PO gate] → scope-gen → prd-gen
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STAGES_DIR = SCRIPT_DIR / "stages"
PYTHON = sys.executable

STAGES = [
    ("seed-gen", "seed.md", ["seed.md"]),
    ("jtbd-gen", "jtbd.md", ["seed.md"]),
    ("problem-frame", "problem-frame.md", ["seed.md", "jtbd.md"]),
    ("scope-gen", "scope.md", ["problem-frame.md"]),
    ("prd-gen", "prd.md", ["seed.md", "jtbd.md", "problem-frame.md", "scope.md"]),
]

GATE_AFTER = "problem-frame"


def run_stage(stage: str, input_text: str) -> dict:
    """script.py 실행. stdin→input, stdout→산출물, stderr→토큰 메타."""
    script_py = STAGES_DIR / stage / "script.py"
    if not script_py.exists():
        return {"success": False, "error": f"script not found: {script_py}"}

    result = subprocess.run(
        [PYTHON, str(script_py)],
        input=input_text, capture_output=True, text=True, timeout=300,
    )

    # stderr에서 토큰 메타 수집
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
        error_lines = [l for l in result.stderr.splitlines()
                       if not l.strip().startswith("{")]
        return {
            "success": False,
            "error": "\n".join(error_lines)[:500],
            "tokens": tokens,
            "cost_usd": cost_usd,
        }

    return {
        "success": True,
        "output": result.stdout.strip(),
        "tokens": tokens,
        "cost_usd": round(cost_usd, 6),
    }


def build_input(output_dir: Path, input_files: list[str]) -> str:
    """앞 단계 산출물들을 이어 붙여 다음 stage의 input으로."""
    parts = []
    for name in input_files:
        path = output_dir / name
        if path.exists():
            parts.append(path.read_text().strip())
    return "\n\n---\n\n".join(parts)


def run_pipeline(idea: str, output_dir: Path, gate: bool = True):
    output_dir.mkdir(parents=True, exist_ok=True)

    # idea는 seed-gen의 input
    (output_dir / "_idea.md").write_text(idea)

    total_cost = 0.0
    total_tokens = {"input": 0, "output": 0}

    for stage, output_name, input_files in STAGES:
        print(f"\n── {stage} ─────────────────────────")

        # input 구성
        if stage == "seed-gen":
            input_text = idea
        else:
            input_text = build_input(output_dir, input_files)

        result = run_stage(stage, input_text)

        if not result["success"]:
            print(f"[실패] {result.get('error', '?')}")
            sys.exit(1)

        output_file = output_dir / output_name
        output_file.write_text(result["output"])
        print(f"[완료] {output_file}")

        tokens = result.get("tokens", {"input": 0, "output": 0})
        cost = result.get("cost_usd", 0)
        total_tokens["input"] += tokens["input"]
        total_tokens["output"] += tokens["output"]
        total_cost += cost

        print(f"  tokens: in={tokens['input']}, out={tokens['output']} | cost: ${cost:.4f}")

        # PO 게이트
        if gate and stage == GATE_AFTER:
            print(f"\n{'='*50}")
            print("PO 게이트: problem-frame.md 확인 후 계속")
            print(f"파일: {output_dir / 'problem-frame.md'}")
            print(f"{'='*50}")
            answer = input("계속 진행할까요? (y/n): ").strip().lower()
            if answer != "y":
                print("[중단] PO가 게이트에서 중단")
                sys.exit(0)

    # 정리
    (output_dir / "_idea.md").unlink(missing_ok=True)

    print(f"\n{'='*50}")
    print(f"[완료] 파이프라인 종료")
    print(f"  총 tokens: in={total_tokens['input']}, out={total_tokens['output']}")
    print(f"  총 cost: ${total_cost:.4f}")
    print(f"  산출물: {output_dir}")


def run_single(stage: str, input_file: Path, output_file: Path):
    if stage not in [s[0] for s in STAGES]:
        print(f"[에러] 알 수 없는 stage: {stage}")
        print(f"사용 가능: {', '.join(s[0] for s in STAGES)}")
        sys.exit(1)

    input_text = input_file.read_text() if input_file.exists() else ""
    if not input_text:
        print(f"[에러] 입력 파일이 비어있음: {input_file}")
        sys.exit(1)

    print(f"[실행] {stage}")
    result = run_stage(stage, input_text)

    if not result["success"]:
        print(f"[실패] {result.get('error', '?')}")
        sys.exit(1)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(result["output"])
    print(f"[완료] {output_file}")
    print(f"  tokens: {result['tokens']}")
    print(f"  cost: ${result['cost_usd']:.4f}")


def main():
    parser = argparse.ArgumentParser(prog="ax-define")
    parser.add_argument("--idea", help="러프 아이디어 (전체 파이프라인)")
    parser.add_argument("--output-dir", help="산출물 디렉토리 (전체 파이프라인)", default="./strategy")
    parser.add_argument("--no-gate", action="store_true", help="PO 게이트 건너뛰기")
    parser.add_argument("--stage", help="특정 stage만 실행")
    parser.add_argument("--input", help="단일 stage 입력 파일")
    parser.add_argument("--output", help="단일 stage 출력 파일")

    args = parser.parse_args()

    if args.stage:
        if not args.input or not args.output:
            parser.error("--stage 사용 시 --input, --output 필수")
        run_single(args.stage, Path(args.input).resolve(), Path(args.output).resolve())
    elif args.idea:
        run_pipeline(args.idea, Path(args.output_dir).resolve(), gate=not args.no_gate)
    else:
        parser.error("--idea 또는 --stage 중 하나 필요")


if __name__ == "__main__":
    main()
