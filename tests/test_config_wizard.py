"""Interactive config wizard tests."""

from dataclasses import dataclass

from mpy_cli.config import AppConfig, SyncConfig
from mpy_cli.config_wizard import run_config_wizard


@dataclass
class FakeScanner:
    """@brief 测试用端口扫描器。"""

    ports: list[str]

    def list_ports(self) -> list[str]:
        """@brief 返回预设端口列表。"""

        return self.ports


def test_wizard_selects_scanned_port(monkeypatch) -> None:  # noqa: ANN001
    """@brief 有扫描结果时应允许直接选择端口。"""

    current = AppConfig(
        serial_port=None,
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        sync=SyncConfig(mode="incremental"),
    )

    monkeypatch.setattr(
        "mpy_cli.config_wizard._ask_select",
        lambda message, choices, default: choices[0],
    )
    monkeypatch.setattr(
        "mpy_cli.config_wizard._ask_text",
        lambda *_args, default="": default,
    )

    updated = run_config_wizard(current, FakeScanner(ports=["/dev/ttyACM0"]))

    assert updated.serial_port == "/dev/ttyACM0"


def test_wizard_falls_back_to_manual_port(monkeypatch) -> None:  # noqa: ANN001
    """@brief 无扫描结果时应回退到手动输入。"""

    current = AppConfig(
        serial_port=None,
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        sync=SyncConfig(mode="incremental"),
    )

    monkeypatch.setattr(
        "mpy_cli.config_wizard._ask_text",
        lambda *_args, default="": "COM7" if not default else default,
    )
    monkeypatch.setattr(
        "mpy_cli.config_wizard._ask_select",
        lambda message, choices, default: default,
    )

    updated = run_config_wizard(current, FakeScanner(ports=[]))

    assert updated.serial_port == "COM7"
