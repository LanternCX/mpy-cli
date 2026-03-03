"""Git diff parser tests."""

from mpy_cli.gitdiff import parse_name_status_line


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
