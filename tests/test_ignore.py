"""Ignore rule matching tests."""

from pathlib import Path

from mpy_cli.ignore import IgnoreMatcher


def test_ignore_and_unignore_rules(tmp_path: Path) -> None:
    """@brief Verify negation rule can unignore a matched file."""
    ignore_file = tmp_path / ".mpyignore"
    ignore_file.write_text("*.pyc\n!important.pyc\n", encoding="utf-8")

    matcher = IgnoreMatcher.from_file(ignore_file)

    assert matcher.is_ignored("foo.pyc")
    assert not matcher.is_ignored("important.pyc")


def test_directory_rule_matches_nested_files(tmp_path: Path) -> None:
    """@brief Verify directory rule ignores nested files."""
    ignore_file = tmp_path / ".mpyignore"
    ignore_file.write_text("build/\n", encoding="utf-8")

    matcher = IgnoreMatcher.from_file(ignore_file)

    assert matcher.is_ignored("build/main.py")
    assert not matcher.is_ignored("src/main.py")
