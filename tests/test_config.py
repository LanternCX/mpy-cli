"""Configuration tests."""

from pathlib import Path

import pytest

from mpy_cli.config import (
    AppConfig,
    ConfigError,
    SyncConfig,
    init_config,
    load_config,
    save_config,
)


def test_init_config_creates_defaults(tmp_path: Path) -> None:
    """@brief Ensure init writes default config values."""
    config_path = tmp_path / ".mpy-cli.toml"

    init_config(config_path)
    cfg = load_config(config_path)

    assert cfg.sync.mode == "incremental"
    assert cfg.ignore_file == ".mpyignore"
    assert cfg.runtime_dir == ".mpy-cli"
    assert cfg.device_upload_dir == ""


def test_load_config_rejects_invalid_sync_mode(tmp_path: Path) -> None:
    """@brief Ensure invalid sync mode triggers validation error."""
    config_path = tmp_path / ".mpy-cli.toml"
    config_path.write_text(
        """
serial_port = "/dev/ttyACM0"
ignore_file = ".mpyignore"
runtime_dir = ".mpy-cli"

[sync]
mode = "unknown"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(config_path)


def test_save_config_round_trip(tmp_path: Path) -> None:
    """@brief 保存后的配置应可无损读取。"""

    config_path = tmp_path / ".mpy-cli.toml"
    original = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="src",
        mpremote_binary="mpremote",
        device_upload_dir="apps/demo",
        sync=SyncConfig(mode="full"),
    )

    save_config(config_path, original)
    loaded = load_config(config_path)

    assert loaded == original
