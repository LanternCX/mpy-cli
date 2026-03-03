"""Local file scanner for full sync mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalFileEntry:
    """@brief 本地文件条目。

    @param local_path 本地文件绝对路径。
    @param remote_path 设备端相对路径。
    """

    local_path: str
    remote_path: str


def list_local_files(
    project_root: Path, source_dir: str, runtime_dir: str
) -> list[LocalFileEntry]:
    """@brief 列举本地候选文件。

    @param project_root 项目根目录。
    @param source_dir 扫描目录（支持相对或绝对路径）。
    @param runtime_dir 运行目录名称（用于排除）。
    @return 本地路径与远端路径映射列表。
    """

    source_path = Path(source_dir)
    if source_path.is_absolute():
        base_dir = source_path.resolve()
        map_to_project = False
    else:
        base_dir = (project_root / source_path).resolve()
        map_to_project = True

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

    collected: list[LocalFileEntry] = []
    seen: set[tuple[str, str]] = set()

    for path in base_dir.rglob("*"):
        if path.is_dir():
            continue

        remote_path = _to_remote_path(
            file_path=path,
            project_root=project_root,
            source_root=base_dir,
            map_to_project=map_to_project,
        )

        if any(part in ignored_dirs for part in remote_path.split("/")):
            continue

        local_path = path.as_posix()
        key = (local_path, remote_path)
        if key in seen:
            continue
        seen.add(key)
        collected.append(LocalFileEntry(local_path=local_path, remote_path=remote_path))

    return sorted(collected, key=lambda entry: entry.remote_path)


def _to_remote_path(
    file_path: Path,
    project_root: Path,
    source_root: Path,
    map_to_project: bool,
) -> str:
    """@brief 计算设备端相对路径。"""

    if map_to_project:
        try:
            return file_path.relative_to(project_root).as_posix()
        except ValueError:
            pass

    return file_path.relative_to(source_root).as_posix()
