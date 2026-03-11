"""Docs and CI presence tests."""

import re
from pathlib import Path


def _readme_section(content: str, command: str) -> str:
    """@brief 返回 README 中指定命令的小节内容。"""

    marker = f"### `mpy-cli {command}`"
    start = content.index(marker)
    next_start = content.find("\n### `mpy-cli ", start + len(marker))
    if next_start == -1:
        return content[start:]
    return content[start:next_start]


def _readme_bash_blocks(section: str) -> list[str]:
    """@brief 返回 README 小节中的 bash 代码块内容。"""

    return re.findall(r"```bash\n(.*?)\n```", section, flags=re.DOTALL)


def test_docs_entrypoints() -> None:
    """@brief README 快速开始和开发文档入口应存在。"""
    assert Path("README.md").exists()
    assert Path("docs/developer-guide.md").exists()


def test_release_workflow_is_tag_to_draft_only() -> None:
    """@brief Tag push workflow 应只做测试并创建 draft release。"""
    workflow = Path(".github/workflows/release.yml")
    assert workflow.exists()

    content = workflow.read_text(encoding="utf-8")
    assert "tags:" in content
    assert "draft: true" in content
    assert "package:" not in content


def test_readme_mentions_interactive_port_scan() -> None:
    """@brief README 应说明交互模式下会扫描端口。"""

    content = Path("README.md").read_text(encoding="utf-8")
    assert "未提供" in content
    assert "--port" in content
    assert "自动扫描" in content


def test_readme_mentions_config_wizard_command() -> None:
    """@brief README 应说明可通过 config 命令重配。"""

    content = Path("README.md").read_text(encoding="utf-8")
    assert "mpy-cli config" in content
    assert "无需手动编辑" in content


def test_readme_lists_all_cli_parameters() -> None:
    """@brief README 应覆盖所有核心命令参数。"""

    content = Path("README.md").read_text(encoding="utf-8")

    for token in [
        "mpy-cli init",
        "mpy-cli config",
        "mpy-cli list",
        "mpy-cli plan",
        "mpy-cli deploy",
        "mpy-cli upload",
        "mpy-cli run",
        "mpy-cli delete",
        "mpy-cli tree",
        "--force",
        "--no-interactive",
        "--mode",
        "--port",
        "--local",
        "--remote",
        "--path",
        "--workers",
        "--probe-timeout",
        "--scan-mode",
        "--reset",
        "--base",
        "--yes",
    ]:
        assert token in content


def test_readme_lists_short_option_aliases() -> None:
    """@brief README 应覆盖各命令新增的短参数别名。"""

    content = Path("README.md").read_text(encoding="utf-8")

    for short_token, long_token in [
        ("`-f`", "`--force`"),
        ("`-n`", "`--no-interactive`"),
        ("`-w`", "`--workers`"),
        ("`-t`", "`--probe-timeout`"),
        ("`-s`", "`--scan-mode`"),
        ("`-r`", "`--reset`"),
        ("`-m`", "`--mode`"),
        ("`-b`", "`--base`"),
        ("`-p`", "`--port`"),
        ("`-y`", "`--yes`"),
        ("`-l`", "`--local`"),
        ("`-r`", "`--remote`"),
        ("`-f`", "`--path`"),
        ("`-a`", "`--path`"),
    ]:
        assert short_token in content
        assert long_token in content


def test_readme_command_sections_document_alias_pairs() -> None:
    """@brief README 各命令小节应按命令局部文档化短长参数映射。"""

    content = Path("README.md").read_text(encoding="utf-8")

    expected = {
        "init": {
            "synopsis": [
                "mpy-cli init",
                "[-f]",
                "[--force]",
                "[-n]",
                "[--no-interactive]",
            ],
            "pairs": [("`-f`", "`--force`"), ("`-n`", "`--no-interactive`")],
        },
        "list": {
            "synopsis": [
                "mpy-cli list",
                "[-w N]",
                "[--workers N]",
                "[-t SECONDS]",
                "[--probe-timeout SECONDS]",
                "[-s MODE]",
                "[--scan-mode MODE]",
                "[-r]",
                "[--reset]",
            ],
            "pairs": [
                ("`-w`", "`--workers`"),
                ("`-t`", "`--probe-timeout`"),
                ("`-s`", "`--scan-mode`"),
                ("`-r`", "`--reset`"),
            ],
        },
        "plan": {
            "synopsis": [
                "mpy-cli plan",
                "[-m {incremental,full}]",
                "[--mode {incremental,full}]",
                "[-b BASE]",
                "[--base BASE]",
                "[-p PORT]",
                "[--port PORT]",
                "[-n]",
                "[--no-interactive]",
                "[-y]",
                "[--yes]",
            ],
            "pairs": [
                ("`-m`", "`--mode`"),
                ("`-b`", "`--base`"),
                ("`-p`", "`--port`"),
                ("`-n`", "`--no-interactive`"),
                ("`-y`", "`--yes`"),
            ],
        },
        "deploy": {
            "synopsis": [
                "mpy-cli deploy",
                "[-m {incremental,full}]",
                "[--mode {incremental,full}]",
                "[-b BASE]",
                "[--base BASE]",
                "[-p PORT]",
                "[--port PORT]",
                "[-n]",
                "[--no-interactive]",
                "[-y]",
                "[--yes]",
            ],
            "pairs": [
                ("`-m`", "`--mode`"),
                ("`-b`", "`--base`"),
                ("`-p`", "`--port`"),
                ("`-n`", "`--no-interactive`"),
                ("`-y`", "`--yes`"),
            ],
        },
        "upload": {
            "synopsis": [
                "mpy-cli upload",
                "[-l LOCAL]",
                "[--local LOCAL]",
                "[-r REMOTE]",
                "[--remote REMOTE]",
                "[-p PORT]",
                "[--port PORT]",
                "[-n]",
                "[--no-interactive]",
                "[-y]",
                "[--yes]",
            ],
            "pairs": [
                ("`-l`", "`--local`"),
                ("`-r`", "`--remote`"),
                ("`-p`", "`--port`"),
                ("`-n`", "`--no-interactive`"),
                ("`-y`", "`--yes`"),
            ],
        },
        "run": {
            "synopsis": [
                "mpy-cli run",
                "[-f PATH]",
                "[--path PATH]",
                "[-p PORT]",
                "[--port PORT]",
                "[-n]",
                "[--no-interactive]",
                "[-y]",
                "[--yes]",
            ],
            "pairs": [
                ("`-f`", "`--path`"),
                ("`-p`", "`--port`"),
                ("`-n`", "`--no-interactive`"),
                ("`-y`", "`--yes`"),
            ],
        },
        "delete": {
            "synopsis": [
                "mpy-cli delete",
                "[-f PATH]",
                "[--path PATH]",
                "[-p PORT]",
                "[--port PORT]",
                "[-n]",
                "[--no-interactive]",
                "[-y]",
                "[--yes]",
            ],
            "pairs": [
                ("`-f`", "`--path`"),
                ("`-p`", "`--port`"),
                ("`-n`", "`--no-interactive`"),
                ("`-y`", "`--yes`"),
            ],
        },
        "tree": {
            "synopsis": [
                "mpy-cli tree",
                "[-a PATH]",
                "[--path PATH]",
                "[-p PORT]",
                "[--port PORT]",
                "[-n]",
                "[--no-interactive]",
            ],
            "pairs": [
                ("`-a`", "`--path`"),
                ("`-p`", "`--port`"),
                ("`-n`", "`--no-interactive`"),
            ],
        },
    }

    for command, requirements in expected.items():
        section = _readme_section(content, command)
        for token in requirements["synopsis"]:
            assert token in section
        for short_token, long_token in requirements["pairs"]:
            assert short_token in section
            assert long_token in section


def test_readme_command_sections_include_short_form_examples() -> None:
    """@brief README 代表性命令小节应提供短参数示例以增强可发现性。"""

    content = Path("README.md").read_text(encoding="utf-8")

    expected = {
        "list": [
            ("mpy-cli list", "-w", "-t"),
            ("mpy-cli list", "-s"),
            ("mpy-cli list", "-r"),
        ],
        "deploy": [("mpy-cli deploy", "-n", "-y")],
        "upload": [("mpy-cli upload", "-l")],
        "run": [("mpy-cli run", "-f")],
        "delete": [("mpy-cli delete", "-f")],
        "tree": [("mpy-cli tree", "-a")],
    }

    for command, example_token_groups in expected.items():
        blocks = _readme_bash_blocks(_readme_section(content, command))
        for token_group in example_token_groups:
            assert any(all(token in block for token in token_group) for block in blocks)


def test_readme_documents_incremental_base_flag() -> None:
    """@brief README 应说明 incremental 的 --base 参数语义。"""

    content = Path("README.md").read_text(encoding="utf-8")
    assert "--base" in content
    assert "Git 基准提交" in content


def test_readme_mentions_device_upload_dir_config() -> None:
    """@brief README 应说明设备上传目录配置行为。"""

    content = Path("README.md").read_text(encoding="utf-8")
    assert "device_upload_dir" in content
    assert "上传目录" in content


def test_readme_lists_run_command_parameters() -> None:
    """@brief README 应包含 run 命令及参数说明。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli run", "--path"]:
        assert token in content


def test_readme_lists_delete_command_parameters() -> None:
    """@brief README 应包含 delete 命令及参数说明。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli delete", "--path"]:
        assert token in content


def test_readme_mentions_source_dir_root_mapping() -> None:
    """@brief README 应说明 source_dir 作为远端路径映射根目录。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["source_dir", "相对 `source_dir`", "不保留 `source_dir` 前缀"]:
        assert token in content


def test_readme_mentions_upload_default_remote_path_semantics() -> None:
    """@brief README 应说明 upload 默认远端路径的 source_dir 语义。"""

    content = Path("README.md").read_text(encoding="utf-8")
    assert "默认优先使用“相对 `source_dir` 路径”" in content
    assert "默认与本地路径一致" not in content


def test_readme_lists_tree_command_parameters() -> None:
    """@brief README 应包含 tree 命令及参数说明。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli tree", "--path"]:
        assert token in content


def test_readme_lists_list_command_usage() -> None:
    """@brief README 应包含 list 命令及用途说明。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli list", "探测", "MicroPython 设备"]:
        assert token in content


def test_readme_lists_list_command_performance_parameters() -> None:
    """@brief README 应包含 list 命令的性能参数说明。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in [
        "--workers",
        "--probe-timeout",
        "--scan-mode",
        "known-first",
        "--reset",
    ]:
        assert token in content
