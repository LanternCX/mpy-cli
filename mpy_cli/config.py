"""Configuration loading and initialization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback.
    import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_CONFIG_TEXT = """# mpy-cli 配置文件
serial_port = ""
ignore_file = ".mpyignore"
runtime_dir = ".mpy-cli"
source_dir = "."
mpremote_binary = "mpremote"

[sync]
mode = "incremental"
"""


class ConfigError(ValueError):
    """@brief 配置错误异常类型。"""


@dataclass(frozen=True)
class SyncConfig:
    """@brief 同步配置模型。

    @param mode 同步模式，支持 full/incremental。
    """

    mode: Literal["full", "incremental"] = "incremental"


@dataclass(frozen=True)
class AppConfig:
    """@brief 应用配置模型。"""

    serial_port: str | None
    ignore_file: str
    runtime_dir: str
    source_dir: str
    mpremote_binary: str
    sync: SyncConfig


def init_config(config_path: Path, overwrite: bool = False) -> None:
    """@brief 初始化配置文件。

    @param config_path 配置文件路径。
    @param overwrite 是否覆盖已有配置。
    """

    if config_path.exists() and not overwrite:
        return
    config_path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")


def default_config() -> AppConfig:
    """@brief 返回默认应用配置。"""

    return AppConfig(
        serial_port=None,
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        sync=SyncConfig(mode="incremental"),
    )


def load_config(config_path: Path) -> AppConfig:
    """@brief 读取并校验配置。

    @param config_path 配置文件路径。
    @return 解析后的应用配置。
    """

    if not config_path.exists():
        raise ConfigError(f"配置文件不存在: {config_path}")

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    mode = _read_sync_mode(data)
    serial_port = _read_str(data, "serial_port", default="").strip() or None

    return AppConfig(
        serial_port=serial_port,
        ignore_file=_read_str(data, "ignore_file", default=".mpyignore"),
        runtime_dir=_read_str(data, "runtime_dir", default=".mpy-cli"),
        source_dir=_read_str(data, "source_dir", default="."),
        mpremote_binary=_read_str(data, "mpremote_binary", default="mpremote"),
        sync=SyncConfig(mode=mode),
    )


def save_config(config_path: Path, config: AppConfig) -> None:
    """@brief 将配置对象写回 TOML 文件。"""

    serial_port = config.serial_port or ""
    text = (
        "# mpy-cli 配置文件\n"
        f"serial_port = {serial_port!r}\n"
        f"ignore_file = {config.ignore_file!r}\n"
        f"runtime_dir = {config.runtime_dir!r}\n"
        f"source_dir = {config.source_dir!r}\n"
        f"mpremote_binary = {config.mpremote_binary!r}\n\n"
        "[sync]\n"
        f"mode = {config.sync.mode!r}\n"
    )
    config_path.write_text(text, encoding="utf-8")


def _read_sync_mode(data: dict) -> Literal["full", "incremental"]:
    """@brief 读取并校验同步模式。"""

    sync_block = data.get("sync", {})
    if not isinstance(sync_block, dict):
        raise ConfigError("[sync] 配置块格式错误")

    raw_mode = sync_block.get("mode", "incremental")
    if raw_mode not in {"full", "incremental"}:
        raise ConfigError(f"不支持的同步模式: {raw_mode}")
    return raw_mode


def _read_str(data: dict, key: str, default: str) -> str:
    """@brief 读取字符串字段。"""

    value = data.get(key, default)
    if not isinstance(value, str):
        raise ConfigError(f"配置项 {key} 必须为字符串")
    return value
