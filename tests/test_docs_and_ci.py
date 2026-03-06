"""Docs and CI presence tests."""

from pathlib import Path


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
        "--yes",
    ]:
        assert token in content


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
