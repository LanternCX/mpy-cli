"""CLI command tests."""

from dataclasses import dataclass
from pathlib import Path

from mpy_cli.config import AppConfig, SyncConfig
from mpy_cli.cli import _resolve_port, main


@dataclass
class FakeScanner:
    """@brief 测试用端口扫描器。"""

    ports: list[str]
    called: bool = False

    def list_ports(self) -> list[str]:
        """@brief 返回预设端口列表。"""

        self.called = True
        return self.ports


def test_init_command_creates_config_and_ignore(tmp_path: Path, monkeypatch) -> None:
    """@brief init command should create config, ignore, and runtime dir."""
    monkeypatch.chdir(tmp_path)

    code = main(["init"])

    assert code == 0
    assert (tmp_path / ".mpy-cli.toml").exists()
    assert (tmp_path / ".mpyignore").exists()
    assert (tmp_path / ".mpy-cli").exists()


def test_resolve_port_uses_scanned_choice_in_interactive(monkeypatch) -> None:  # noqa: ANN001
    """@brief 交互模式下无端口时应扫描并选择。"""

    scanner = FakeScanner(ports=["/dev/ttyACM0", "/dev/ttyUSB0"])
    monkeypatch.setattr(
        "mpy_cli.cli._ask_select", lambda *_args, **_kwargs: "/dev/ttyUSB0"
    )

    selected = _resolve_port(
        arg_port=None,
        config_port=None,
        interactive=True,
        scanner=scanner,
    )

    assert scanner.called is True
    assert selected == "/dev/ttyUSB0"


def test_resolve_port_falls_back_to_manual_input_when_scan_empty(monkeypatch) -> None:  # noqa: ANN001
    """@brief 扫描无结果时应回退到手动输入。"""

    scanner = FakeScanner(ports=[])
    monkeypatch.setattr("mpy_cli.cli._ask_text", lambda *_args, **_kwargs: "COM3")

    selected = _resolve_port(
        arg_port=None,
        config_port=None,
        interactive=True,
        scanner=scanner,
    )

    assert scanner.called is True
    assert selected == "COM3"


def test_resolve_port_non_interactive_without_port_returns_none() -> None:
    """@brief 非交互模式下无端口时应保持 None。"""

    scanner = FakeScanner(ports=["/dev/ttyACM0"])

    selected = _resolve_port(
        arg_port=None,
        config_port=None,
        interactive=False,
        scanner=scanner,
    )

    assert scanner.called is False
    assert selected is None


def test_config_command_updates_existing_config(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """@brief config 子命令应通过向导更新配置文件。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    updated = AppConfig(
        serial_port="COM5",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        sync=SyncConfig(mode="full"),
    )

    monkeypatch.setattr(
        "mpy_cli.cli.run_config_wizard", lambda *_args, **_kwargs: updated
    )

    code = main(["config"])

    assert code == 0
    content = (tmp_path / ".mpy-cli.toml").read_text(encoding="utf-8")
    assert "COM5" in content
    assert "mode = 'full'" in content
