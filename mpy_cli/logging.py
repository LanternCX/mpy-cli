"""Logging setup for console and rotating files."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    runtime_dir: Path,
    level: int = logging.INFO,
    max_bytes: int = 1_048_576,
    backup_count: int = 5,
) -> logging.Logger:
    """@brief 初始化日志系统。

    @param runtime_dir 项目运行目录。
    @param level 日志等级。
    @param max_bytes 单文件最大字节数。
    @param backup_count 日志切片保留数量。
    @return 配置完成的 logger。
    """

    logger = logging.getLogger("mpy_cli")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False

    logs_dir = runtime_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "mpy-cli.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = _build_console_handler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def _build_console_handler() -> logging.Handler:
    """@brief 构建控制台日志处理器。"""

    try:
        from rich.logging import RichHandler

        return RichHandler(rich_tracebacks=True, show_path=False)
    except Exception:  # noqa: BLE001
        return logging.StreamHandler()
