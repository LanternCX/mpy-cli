"""Local scanner tests."""

from pathlib import Path

from mpy_cli.scanner import list_local_files


def test_list_local_files_supports_absolute_source_outside_project(
    tmp_path: Path,
) -> None:
    """@brief 绝对 source_dir 在仓库外时仍应返回可用文件映射。"""

    project_root = tmp_path / "tool"
    project_root.mkdir(parents=True, exist_ok=True)

    source_root = tmp_path / "external_source"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "yaw_sender.py").write_text("print('ok')\n", encoding="utf-8")

    entries = list_local_files(
        project_root=project_root,
        source_dir=source_root.as_posix(),
        runtime_dir=".mpy-cli",
    )

    assert len(entries) == 1
    assert entries[0].local_path == (source_root / "yaw_sender.py").as_posix()
    assert entries[0].remote_path == "yaw_sender.py"


def test_list_local_files_uses_source_relative_remote_path_for_relative_source_dir(
    tmp_path: Path,
) -> None:
    """@brief 相对 source_dir 时远端路径应相对 source_dir 计算。"""

    project_root = tmp_path
    source_root = project_root / "app_src"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "main.py").write_text("print('ok')\n", encoding="utf-8")

    entries = list_local_files(
        project_root=project_root,
        source_dir="app_src",
        runtime_dir=".mpy-cli",
    )

    assert len(entries) == 1
    assert entries[0].local_path == (source_root / "main.py").as_posix()
    assert entries[0].remote_path == "main.py"
