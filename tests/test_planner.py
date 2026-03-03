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
