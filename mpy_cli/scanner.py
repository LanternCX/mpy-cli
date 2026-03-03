"""Local file scanner for full sync mode."""

from __future__ import annotations

from pathlib import Path


def list_local_files(
    project_root: Path, source_dir: str, runtime_dir: str
) -> list[str]:
    """@brief 列举本地候选文件。

    @param project_root 项目根目录。
    @param source_dir 扫描目录（相对项目根）。
    @param runtime_dir 运行目录名称（用于排除）。
    @return 相对项目根的 POSIX 路径列表。
    """

    base_dir = (project_root / source_dir).resolve()
    if not base_dir.exists():
        return []

    ignored_dirs = {
        ".git",
        runtime_dir,
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
    }

    collected: list[str] = []
    for path in base_dir.rglob("*"):
        if path.is_dir():
            continue

        rel = path.relative_to(project_root).as_posix()
        if any(part in ignored_dirs for part in rel.split("/")):
            continue
        collected.append(rel)

    return sorted(set(collected))
