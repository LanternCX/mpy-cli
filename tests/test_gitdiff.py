"""Git diff parser tests."""

from pathlib import Path

from mpy_cli.gitdiff import collect_git_changes, parse_name_status_line


def test_parse_rename_line() -> None:
    """@brief Rename line should map old and new paths correctly."""
    entry = parse_name_status_line("R100\told.py\tnew.py")

    assert entry.status == "R"
    assert entry.src_path == "old.py"
    assert entry.dst_path == "new.py"


def test_parse_delete_line() -> None:
    """@brief Delete line should preserve deleted target path."""
    entry = parse_name_status_line("D\tobsolete.py")

    assert entry.status == "D"
    assert entry.src_path is None
    assert entry.dst_path == "obsolete.py"


def test_collect_git_changes_scopes_git_commands_to_current_directory(
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief collect_git_changes 应使用当前目录作用域收集变更。"""

    captured: list[list[str]] = []

    def fake_run_git(args: list[str], repo_path: Path) -> str:
        captured.append(args)
        assert repo_path == Path("/tmp/repo")
        return ""

    monkeypatch.setattr("mpy_cli.gitdiff._run_git", fake_run_git)

    collect_git_changes(Path("/tmp/repo"))

    assert captured == [
        ["diff", "--name-status", "--relative", "HEAD", "--", "."],
        ["ls-files", "--others", "--exclude-standard", "--", "."],
    ]


def test_collect_git_changes_uses_custom_base_ref(monkeypatch) -> None:  # noqa: ANN001
    """@brief collect_git_changes 应允许使用自定义基准提交。"""

    captured: list[list[str]] = []

    def fake_run_git(args: list[str], repo_path: Path) -> str:
        captured.append(args)
        assert repo_path == Path("/tmp/repo")
        return ""

    monkeypatch.setattr("mpy_cli.gitdiff._run_git", fake_run_git)

    collect_git_changes(Path("/tmp/repo"), base_ref="abc123")

    assert captured == [
        ["diff", "--name-status", "--relative", "abc123", "--", "."],
        ["ls-files", "--others", "--exclude-standard", "--", "."],
    ]
