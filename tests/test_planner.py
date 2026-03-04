"""Deployment planner tests."""

from mpy_cli.gitdiff import ChangeEntry
from mpy_cli.ignore import IgnoreMatcher
from mpy_cli.planner import build_plan


def test_full_mode_includes_wipe_first() -> None:
    """@brief Full mode must wipe before upload operations."""
    matcher = IgnoreMatcher([])

    plan = build_plan(
        mode="full",
        local_files=["main.py", "lib/utils.py"],
        changes=[],
        matcher=matcher,
    )

    assert plan.operations[0].op_type == "wipe"
    assert plan.operations[1].op_type == "upload"


def test_incremental_maps_delete_to_delete_operation() -> None:
    """@brief Incremental delete change should produce delete operation."""
    matcher = IgnoreMatcher([])

    plan = build_plan(
        mode="incremental",
        local_files=[],
        changes=[ChangeEntry(status="D", src_path=None, dst_path="obsolete.py")],
        matcher=matcher,
    )

    assert len(plan.operations) == 1
    assert plan.operations[0].op_type == "delete"
    assert plan.operations[0].remote_path == "obsolete.py"


def test_full_mode_scopes_wipe_and_upload_to_remote_base_dir() -> None:
    """@brief 配置上传目录后 full 计划应仅作用于该目录。"""

    matcher = IgnoreMatcher([])

    plan = build_plan(
        mode="full",
        local_files=["main.py", "lib/utils.py"],
        changes=[],
        matcher=matcher,
        remote_base_dir="apps/demo",
    )

    assert plan.operations[0].op_type == "wipe"
    assert plan.operations[0].remote_path == "apps/demo"
    upload_targets = [
        operation.remote_path
        for operation in plan.operations
        if operation.op_type == "upload"
    ]
    assert upload_targets == ["apps/demo/lib/utils.py", "apps/demo/main.py"]


def test_incremental_prefixes_remote_paths_with_remote_base_dir() -> None:
    """@brief 配置上传目录后增量上传/删除应带远端前缀。"""

    matcher = IgnoreMatcher([])

    plan = build_plan(
        mode="incremental",
        local_files=[],
        changes=[
            ChangeEntry(status="D", src_path=None, dst_path="obsolete.py"),
            ChangeEntry(status="M", src_path=None, dst_path="main.py"),
        ],
        matcher=matcher,
        remote_base_dir="apps/demo",
    )

    assert plan.operations[0].op_type == "delete"
    assert plan.operations[0].remote_path == "apps/demo/obsolete.py"
    assert plan.operations[1].op_type == "upload"
    assert plan.operations[1].local_path == "main.py"
    assert plan.operations[1].remote_path == "apps/demo/main.py"
