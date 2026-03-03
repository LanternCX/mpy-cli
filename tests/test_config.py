"""Configuration tests."""

from pathlib import Path

import pytest

from mpy_cli.config import ConfigError, init_config, load_config


def test_init_config_creates_defaults(tmp_path: Path) -> None:
    """@brief Ensure init writes default config values."""
    config_path = tmp_path / ".mpy-cli.toml"

    init_config(config_path)
    cfg = load_config(config_path)

    assert cfg.sync.mode == "incremental"
    assert cfg.ignore_file == ".mpyignore"
    assert cfg.runtime_dir == ".mpy-cli"


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
