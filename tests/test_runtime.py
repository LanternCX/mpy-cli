"""Runtime layout tests."""

from pathlib import Path

from mpy_cli.runtime import ensure_runtime_layout


def test_runtime_layout_uses_project_dir(tmp_path: Path) -> None:
    """@brief Runtime directory should be created under project path."""
    runtime_dir = tmp_path / ".mpy-cli"

    paths = ensure_runtime_layout(runtime_dir)

    assert paths.root == runtime_dir
    assert (runtime_dir / "logs").exists()
    assert (runtime_dir / "data" / "runtime.db").exists()
