"""Build deployment plan from local files and git changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mpy_cli.gitdiff import ChangeEntry
from mpy_cli.ignore import IgnoreMatcher
from mpy_cli.scanner import LocalFileEntry


@dataclass(frozen=True)
class PlanOperation:
    """@brief 部署操作项。"""

    op_type: Literal["wipe", "upload", "delete"]
    local_path: str | None
    remote_path: str | None
    reason: str


@dataclass(frozen=True)
class DeployPlan:
    """@brief 部署计划。"""

    mode: Literal["full", "incremental"]
    operations: list[PlanOperation]


def build_plan(
    mode: Literal["full", "incremental"],
    local_files: list[str] | list[LocalFileEntry],
    changes: list[ChangeEntry],
    matcher: IgnoreMatcher,
) -> DeployPlan:
    """@brief 根据模式构建部署计划。"""

    if mode == "full":
        operations = _build_full_plan(local_files=local_files, matcher=matcher)
        return DeployPlan(mode=mode, operations=operations)

    operations = _build_incremental_plan(
        local_files=local_files, changes=changes, matcher=matcher
    )
    return DeployPlan(mode=mode, operations=operations)


def _build_full_plan(
    local_files: list[str] | list[LocalFileEntry], matcher: IgnoreMatcher
) -> list[PlanOperation]:
    """@brief 构建全量模式计划。"""

    operations: list[PlanOperation] = [
        PlanOperation(
            op_type="wipe", local_path=None, remote_path=None, reason="full-sync"
        ),
    ]
    for local_path, remote_path in _normalize_full_local_files(local_files):
        if matcher.is_ignored(remote_path):
            continue
        operations.append(
            PlanOperation(
                op_type="upload",
                local_path=local_path,
                remote_path=remote_path,
                reason="full-sync",
            )
        )
    return operations


def _build_incremental_plan(
    local_files: list[str] | list[LocalFileEntry],
    changes: list[ChangeEntry],
    matcher: IgnoreMatcher,
) -> list[PlanOperation]:
    """@brief 构建增量模式计划。"""

    operations: list[PlanOperation] = []
    upload_seen: set[str] = set()
    delete_seen: set[str] = set()

    for change in changes:
        if change.status == "D":
            target = change.dst_path
            if target not in delete_seen:
                delete_seen.add(target)
                operations.append(
                    PlanOperation(
                        op_type="delete",
                        local_path=None,
                        remote_path=target,
                        reason="git-diff",
                    )
                )
            continue

        target = change.dst_path
        if matcher.is_ignored(target):
            continue
        if target not in upload_seen:
            upload_seen.add(target)
            operations.append(
                PlanOperation(
                    op_type="upload",
                    local_path=target,
                    remote_path=target,
                    reason="git-diff",
                )
            )

    normalized_local_files = [
        item.remote_path if isinstance(item, LocalFileEntry) else item
        for item in local_files
    ]

    for path in sorted(set(normalized_local_files)):
        if matcher.is_ignored(path):
            continue
        if path in upload_seen:
            continue
        upload_seen.add(path)
        operations.append(
            PlanOperation(
                op_type="upload", local_path=path, remote_path=path, reason="local-new"
            )
        )

    return operations


def _normalize_full_local_files(
    local_files: list[str] | list[LocalFileEntry],
) -> list[tuple[str, str]]:
    """@brief 归一化 full 模式文件输入。"""

    normalized: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for item in local_files:
        if isinstance(item, LocalFileEntry):
            pair = (item.local_path, item.remote_path)
        else:
            pair = (item, item)

        if pair in seen:
            continue
        seen.add(pair)
        normalized.append(pair)

    return sorted(normalized, key=lambda pair: pair[1])
