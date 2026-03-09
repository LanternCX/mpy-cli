"""Runtime layout tests."""

from pathlib import Path

from mpy_cli.runtime import (
    clear_scan_records,
    ensure_runtime_layout,
    list_scanned_ports,
    list_successful_scanned_ports,
    mark_scanned_port_successes,
    upsert_scanned_ports,
)


def test_runtime_layout_uses_project_dir(tmp_path: Path) -> None:
    """@brief Runtime directory should be created under project path."""
    runtime_dir = tmp_path / ".mpy-cli"

    paths = ensure_runtime_layout(runtime_dir)

    assert paths.root == runtime_dir
    assert (runtime_dir / "logs").exists()
    assert (runtime_dir / "data" / "runtime.db").exists()


def test_runtime_layout_creates_scanned_ports_table(tmp_path: Path) -> None:
    """@brief 运行库初始化后应包含扫描端口缓存表。"""

    runtime_dir = tmp_path / ".mpy-cli"
    paths = ensure_runtime_layout(runtime_dir)

    assert list_scanned_ports(paths.db_path) == []


def test_upsert_scanned_ports_deduplicates_and_updates_recency(tmp_path: Path) -> None:
    """@brief 端口缓存应去重并按最近扫描时间排序。"""

    runtime_dir = tmp_path / ".mpy-cli"
    paths = ensure_runtime_layout(runtime_dir)

    upsert_scanned_ports(
        paths.db_path,
        ["COM3", "/dev/ttyACM0", "COM3"],
        recorded_at="2026-03-09 09:00:00",
    )
    upsert_scanned_ports(
        paths.db_path,
        ["/dev/ttyACM0"],
        recorded_at="2026-03-09 09:05:00",
    )

    assert list_scanned_ports(paths.db_path) == ["/dev/ttyACM0", "COM3"]


def test_mark_scanned_port_successes_tracks_successful_ports_only(
    tmp_path: Path,
) -> None:
    """@brief 成功缓存应只返回探测成功过的端口。"""

    runtime_dir = tmp_path / ".mpy-cli"
    paths = ensure_runtime_layout(runtime_dir)

    upsert_scanned_ports(
        paths.db_path,
        ["COM3", "/dev/ttyACM0"],
        recorded_at="2026-03-09 10:00:00",
    )
    mark_scanned_port_successes(
        paths.db_path,
        ["/dev/ttyACM0"],
        recorded_at="2026-03-09 10:05:00",
    )

    assert list_scanned_ports(paths.db_path) == ["/dev/ttyACM0", "COM3"]
    assert list_successful_scanned_ports(paths.db_path) == ["/dev/ttyACM0"]


def test_mark_scanned_port_successes_replaces_previous_success_snapshot(
    tmp_path: Path,
) -> None:
    """@brief 成功缓存应只保留上一次扫描成功结果。"""

    runtime_dir = tmp_path / ".mpy-cli"
    paths = ensure_runtime_layout(runtime_dir)

    upsert_scanned_ports(
        paths.db_path,
        ["COM3", "COM7"],
        recorded_at="2026-03-09 10:00:00",
    )
    mark_scanned_port_successes(
        paths.db_path,
        ["COM3"],
        recorded_at="2026-03-09 10:01:00",
    )
    mark_scanned_port_successes(
        paths.db_path,
        ["COM7"],
        recorded_at="2026-03-09 10:02:00",
    )

    assert list_successful_scanned_ports(paths.db_path) == ["COM7"]


def test_clear_scan_records_removes_scanned_and_successful_cache(
    tmp_path: Path,
) -> None:
    """@brief 重置扫描记录后应清空扫描历史与成功缓存。"""

    runtime_dir = tmp_path / ".mpy-cli"
    paths = ensure_runtime_layout(runtime_dir)

    upsert_scanned_ports(
        paths.db_path,
        ["COM3", "COM7"],
        recorded_at="2026-03-09 10:00:00",
    )
    mark_scanned_port_successes(
        paths.db_path,
        ["COM7"],
        recorded_at="2026-03-09 10:01:00",
    )

    clear_scan_records(paths.db_path)

    assert list_scanned_ports(paths.db_path) == []
    assert list_successful_scanned_ports(paths.db_path) == []
