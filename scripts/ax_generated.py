"""
ax_generated.py — team-ax 가 생성한 파일 매니페스트 헬퍼

대상 프로젝트 루트에 .ax-generated.jsonl (append-only 매니페스트) +
.ax-artifacts/{rel_path} (원본 사본) 을 관리한다.

사용 패턴:
    from ax_generated import record, lookup, reconcile

    # team-ax 가 파일을 생성한 직후
    record(project_root, "src/foo.ts", stage="ax-implement",
           fixture_id="haru:abc1234", user_name="yoyo", content=generated_text)

    # post-commit hook 내부에서
    entry = lookup(project_root, "src/foo.ts")
    if entry:
        original = read_artifact(project_root, "src/foo.ts")
        # diff 측정 후
        reconcile(project_root, "src/foo.ts")

매니페스트 라인 형식 (JSONL):
    {"path": "src/foo.ts", "generated_at": "ISO", "stage": "ax-implement",
     "fixture_id": "haru:abc1234", "user_name": "yoyo"}
"""

import json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = ".ax-generated.jsonl"
ARTIFACTS_DIR = ".ax-artifacts"


def _manifest_path(project_root: Path) -> Path:
    return project_root / MANIFEST_NAME


def _artifact_path(project_root: Path, rel_path: str) -> Path:
    return project_root / ARTIFACTS_DIR / rel_path


def record(
    project_root: Path,
    rel_path: str,
    *,
    stage: str,
    fixture_id: str | None,
    user_name: str,
    content: str,
) -> None:
    """
    team-ax 가 파일을 생성한 직후 호출. 매니페스트 append + 원본 artifact 복사.

    rel_path: 프로젝트 루트 기준 상대 경로
    content: ax 가 생성한 원본 텍스트 (나중 diff 비교의 베이스라인)
    """
    project_root = Path(project_root).resolve()

    # artifact 저장 (디렉토리 구조 미러)
    artifact = _artifact_path(project_root, rel_path)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(content)

    # 매니페스트 append
    entry = {
        "path": rel_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "fixture_id": fixture_id,
        "user_name": user_name,
    }
    manifest = _manifest_path(project_root)
    with manifest.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def lookup(project_root: Path, rel_path: str) -> dict | None:
    """
    매니페스트에서 rel_path 에 대한 **가장 최근** 엔트리 반환. 없으면 None.
    """
    project_root = Path(project_root).resolve()
    manifest = _manifest_path(project_root)
    if not manifest.exists():
        return None

    latest = None
    for line in manifest.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("path") == rel_path:
            latest = entry
    return latest


def read_artifact(project_root: Path, rel_path: str) -> str | None:
    """artifact 사본 읽기. 없으면 None."""
    artifact = _artifact_path(Path(project_root).resolve(), rel_path)
    if not artifact.exists():
        return None
    return artifact.read_text()


def reconcile(project_root: Path, rel_path: str) -> bool:
    """
    rel_path 에 해당하는 매니페스트 엔트리 + artifact 제거.
    post-commit hook 이 intervention 기록 완료 후 호출.

    Returns: True if 제거 성공, False if 대상 없음.
    """
    project_root = Path(project_root).resolve()
    manifest = _manifest_path(project_root)
    if not manifest.exists():
        return False

    # 매니페스트 rewrite — 해당 path 엔트리 전부 제거
    lines = manifest.read_text().splitlines()
    kept = []
    removed = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            kept.append(line)
            continue
        if entry.get("path") == rel_path:
            removed = True
            continue
        kept.append(line)

    if removed:
        if kept:
            manifest.write_text("\n".join(kept) + "\n")
        else:
            manifest.unlink()

    # artifact 제거
    artifact = _artifact_path(project_root, rel_path)
    if artifact.exists():
        artifact.unlink()
        # 빈 디렉토리 정리 (.ax-artifacts 까지)
        parent = artifact.parent
        artifacts_root = project_root / ARTIFACTS_DIR
        while parent != artifacts_root.parent and parent.exists():
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    return removed


def all_tracked_paths(project_root: Path) -> set[str]:
    """현재 매니페스트에 남아 있는 모든 path 의 집합 (중복 제거)."""
    project_root = Path(project_root).resolve()
    manifest = _manifest_path(project_root)
    if not manifest.exists():
        return set()
    paths = set()
    for line in manifest.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if "path" in entry:
                paths.add(entry["path"])
        except json.JSONDecodeError:
            continue
    return paths
