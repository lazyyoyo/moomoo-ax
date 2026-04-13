#!/usr/bin/env python3
"""ARCHITECTURE.md 의 '기술 스택' 섹션 파싱 → package.json 설치 목록 대조 →
src/** import grep → 3-way 결과 JSON.

exit 0: 위반 없음 또는 정보성 mismatch (declared_but_missing 만 fail 로 취급)
exit 1: ARCHITECTURE.md 에 명시됐으나 package.json 에 미설치 (손코딩 대체 의심)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path.cwd()


def load_arch_deps(path: Path) -> set[str]:
    """ARCHITECTURE.md 의 backtick 단어 + 리스트 아이템에서 라이브러리 이름 후보 추출."""
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    deps: set[str] = set()
    for match in re.finditer(r"`([a-z0-9@][a-z0-9._/-]+)`", text):
        name = match.group(1)
        if name.startswith(("./", "../", "/")):
            continue
        if "/" in name or "-" in name or "." in name or len(name) >= 4:
            deps.add(name.split("@")[0] if name.startswith("@") and "@" in name[1:] else name)
    return deps


def load_pkg_deps(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    deps: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps.update((data.get(key) or {}).keys())
    return deps


def find_imports(src_dir: Path) -> set[str]:
    imports: set[str] = set()
    if not src_dir.exists():
        return imports
    pat = re.compile(r"""(?:import|require)[^"']*["']([^"']+)["']""")
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.mjs", "*.cjs"):
        for file in src_dir.rglob(ext):
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in pat.finditer(text):
                module = match.group(1)
                if module.startswith((".", "/")):
                    continue
                parts = module.split("/")
                if module.startswith("@") and len(parts) >= 2:
                    imports.add("/".join(parts[:2]))
                else:
                    imports.add(parts[0])
    return imports


def main() -> int:
    arch_path = ROOT / "ARCHITECTURE.md"
    pkg_path = ROOT / "package.json"
    src_dir = ROOT / "src"

    arch = load_arch_deps(arch_path)
    pkg = load_pkg_deps(pkg_path)
    imp = find_imports(src_dir)

    # filter arch candidates to those that look like package names — anything
    # also appearing in pkg is strong signal. keep everything that contains
    # package-like characters but report missing only if intersects pattern.
    declared_but_missing = sorted({d for d in arch if d in arch and d not in pkg and _looks_like_pkg(d)})
    installed_but_unused = sorted((pkg - imp) - _builtin_exceptions())
    undeclared_but_used = sorted((imp & pkg) - arch)

    result = {
        "declared_in_arch": sorted(arch),
        "installed_in_pkg": sorted(pkg),
        "imported_in_src": sorted(imp),
        "declared_but_missing": declared_but_missing,
        "installed_but_unused": installed_but_unused,
        "undeclared_but_used": undeclared_but_used,
    }

    status = "fail" if declared_but_missing else "pass"
    print(json.dumps({"status": status, **result}, indent=2))
    return 0 if status == "pass" else 1


def _looks_like_pkg(name: str) -> bool:
    if name.startswith("@") and "/" in name:
        return True
    if "/" in name:
        return False
    return bool(re.match(r"^[a-z][a-z0-9._-]{2,}$", name))


def _builtin_exceptions() -> set[str]:
    # devDependencies that are typically not imported in src but are legit
    return {
        "typescript",
        "eslint",
        "prettier",
        "vitest",
        "jest",
        "next",
        "@types/node",
        "@types/react",
        "@types/react-dom",
    }


if __name__ == "__main__":
    sys.exit(main())
