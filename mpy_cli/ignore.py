"""Ignore rule parsing for `.mpyignore`."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath


DEFAULT_IGNORE_TEXT = """# mpy-cli 忽略规则
.git/
.github/
.opencode/
.mpy-cli/
docs/
tests/
__pycache__/
*.pyc
"""


@dataclass(frozen=True)
class IgnoreRule:
    """@brief 忽略规则模型。"""

    pattern: str
    negated: bool


class IgnoreMatcher:
    """@brief `.mpyignore` 匹配器。"""

    def __init__(self, rules: list[IgnoreRule]):
        """@brief 构造匹配器。

        @param rules 忽略规则列表。
        """

        self.rules = rules

    @classmethod
    def from_file(cls, file_path: Path) -> "IgnoreMatcher":
        """@brief 从忽略文件加载规则。"""

        if not file_path.exists():
            return cls([])

        rules: list[IgnoreRule] = []
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            negated = line.startswith("!")
            pattern = line[1:] if negated else line
            rules.append(IgnoreRule(pattern=pattern, negated=negated))
        return cls(rules)

    def is_ignored(self, path: str) -> bool:
        """@brief 判断路径是否被忽略。"""

        normalized = _normalize(path)
        ignored = False
        for rule in self.rules:
            if _match_rule(rule.pattern, normalized):
                ignored = not rule.negated
        return ignored


def init_ignore(ignore_path: Path, overwrite: bool = False) -> None:
    """@brief 初始化 `.mpyignore` 文件。"""

    if ignore_path.exists() and not overwrite:
        return
    ignore_path.write_text(DEFAULT_IGNORE_TEXT, encoding="utf-8")


def _normalize(path: str) -> str:
    """@brief 统一路径分隔格式。"""

    normalized = PurePosixPath(path).as_posix()
    return normalized[2:] if normalized.startswith("./") else normalized


def _match_rule(pattern: str, normalized_path: str) -> bool:
    """@brief 执行单条规则匹配。"""

    anchored = pattern.startswith("/")
    core_pattern = pattern[1:] if anchored else pattern
    directory_rule = core_pattern.endswith("/")

    if directory_rule:
        dir_name = core_pattern.rstrip("/")
        if anchored:
            return normalized_path == dir_name or normalized_path.startswith(
                f"{dir_name}/"
            )
        segments = normalized_path.split("/")
        return dir_name in segments

    if anchored:
        return fnmatchcase(normalized_path, core_pattern)

    if fnmatchcase(normalized_path, core_pattern):
        return True
    basename = normalized_path.split("/")[-1]
    return fnmatchcase(basename, core_pattern)
