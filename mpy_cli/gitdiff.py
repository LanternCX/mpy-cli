"""Git diff parsing for incremental sync."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitDiffError(RuntimeError):
    """@brief Git diff 解析异常。"""


@dataclass(frozen=True)
class ChangeEntry:
    """@brief 单条 Git 变更记录。"""

    status: str
    src_path: str | None
    dst_path: str


def parse_name_status_line(line: str) -> ChangeEntry:
    """@brief 解析 `git diff --name-status` 单行输出。"""

    parts = line.strip().split("\t")
    if len(parts) < 2:
        raise GitDiffError(f"无法解析 git diff 行: {line}")

    status_token = parts[0]
    status = status_token[0]

    if status in {"R", "C"} and len(parts) >= 3:
        return ChangeEntry(status=status, src_path=parts[1], dst_path=parts[2])
    return ChangeEntry(status=status, src_path=None, dst_path=parts[1])


def collect_git_changes(repo_path: Path) -> list[ChangeEntry]:
    """@brief 收集当前工作区变更和未跟踪文件。"""

    name_status_output = _run_git(
        ["diff", "--name-status", "--relative", "HEAD", "--", "."],
        repo_path,
    )
    untracked_output = _run_git(
        ["ls-files", "--others", "--exclude-standard", "--", "."],
        repo_path,
    )

    changes: list[ChangeEntry] = []
    seen: set[tuple[str, str | None, str]] = set()

    for line in name_status_output.splitlines():
        line = line.strip()
        if not line:
            continue
        entry = parse_name_status_line(line)
        key = (entry.status, entry.src_path, entry.dst_path)
        if key not in seen:
            seen.add(key)
            changes.append(entry)

    for line in untracked_output.splitlines():
        path = line.strip()
        if not path:
            continue
        entry = ChangeEntry(status="A", src_path=None, dst_path=path)
        key = (entry.status, entry.src_path, entry.dst_path)
        if key not in seen:
            seen.add(key)
            changes.append(entry)

    return changes


def _run_git(args: list[str], repo_path: Path) -> str:
    """@brief 执行 Git 命令并返回输出。"""

    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise GitDiffError(str(exc)) from exc
    if completed.returncode != 0:
        raise GitDiffError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout
