"""Interactive configuration wizard."""

from __future__ import annotations

import sys
from typing import Protocol

from mpy_cli.config import AppConfig, SyncConfig, default_config


MANUAL_PORT_CHOICE = "手动输入端口"


class PortScanner(Protocol):
    """@brief 向导端口扫描接口。"""

    def list_ports(self) -> list[str]:
        """@brief 返回可用端口列表。"""


def run_config_wizard(
    current_config: AppConfig | None,
    scanner: PortScanner,
) -> AppConfig:
    """@brief 运行交互式配置向导并返回新配置。"""

    current = current_config or default_config()
    serial_port = _select_port(current_port=current.serial_port, scanner=scanner)

    mode = _ask_select(
        "请选择默认同步模式",
        ["incremental", "full"],
        default=current.sync.mode,
    )
    ignore_file = _ask_text("请输入忽略文件路径", default=current.ignore_file)
    runtime_dir = _ask_text("请输入运行目录", default=current.runtime_dir)
    source_dir = _ask_text("请输入源代码目录", default=current.source_dir)
    device_upload_dir = _ask_text(
        "请输入设备上传目录（留空表示设备根目录）",
        default=current.device_upload_dir,
    )
    mpremote_binary = _ask_text(
        "请输入 mpremote 命令名", default=current.mpremote_binary
    )

    return AppConfig(
        serial_port=serial_port,
        ignore_file=ignore_file.strip() or current.ignore_file,
        runtime_dir=runtime_dir.strip() or current.runtime_dir,
        source_dir=source_dir.strip() or current.source_dir,
        device_upload_dir=device_upload_dir.strip(),
        mpremote_binary=mpremote_binary.strip() or current.mpremote_binary,
        sync=SyncConfig(
            mode=mode if mode in {"incremental", "full"} else current.sync.mode
        ),
    )


def _select_port(current_port: str | None, scanner: PortScanner) -> str | None:
    """@brief 根据扫描结果和输入选择端口。"""

    ports = _scan_ports(scanner)
    default_port = current_port or ""

    if ports:
        choices = [*ports, MANUAL_PORT_CHOICE]
        default_choice = current_port if current_port in ports else ports[0]
        selected = _ask_select("请选择默认设备端口", choices, default=default_choice)
        if selected != MANUAL_PORT_CHOICE:
            return selected

    manual = _ask_text("请输入默认设备端口（可留空）", default=default_port)
    return manual.strip() or None


def _scan_ports(scanner: PortScanner) -> list[str]:
    """@brief 执行端口扫描并去重。"""

    try:
        ports = scanner.list_ports()
    except Exception:  # noqa: BLE001
        return []

    deduped: list[str] = []
    for port in ports:
        if port not in deduped:
            deduped.append(port)
    return deduped


def _ask_select(message: str, choices: list[str], default: str) -> str:
    """@brief questionary 单选输入。"""

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return default

    try:
        import questionary

        value = questionary.select(message, choices=choices, default=default).ask()
        if isinstance(value, str) and value:
            return value
    except Exception:  # noqa: BLE001
        pass
    return default


def _ask_text(message: str, default: str = "") -> str:
    """@brief questionary 文本输入。"""

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return default

    try:
        import questionary

        value = questionary.text(message, default=default).ask()
        if value is not None:
            return str(value)
    except Exception:  # noqa: BLE001
        pass
    return default
