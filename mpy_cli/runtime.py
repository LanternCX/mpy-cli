"""Runtime directory and state management."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    """@brief 运行目录路径集合。"""

    root: Path
    logs_dir: Path
    data_dir: Path
    db_path: Path


def ensure_runtime_layout(runtime_dir: Path) -> RuntimePaths:
    """@brief 初始化运行目录结构。

    @param runtime_dir 项目运行目录。
    @return 运行目录路径集合。
    """

    logs_dir = runtime_dir / "logs"
    data_dir = runtime_dir / "data"
    db_path = data_dir / "runtime.db"

    logs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    _ensure_runtime_db(db_path)

    return RuntimePaths(
        root=runtime_dir, logs_dir=logs_dir, data_dir=data_dir, db_path=db_path
    )


def _ensure_runtime_db(db_path: Path) -> None:
    """@brief 初始化运行时数据库。"""

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deploy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT
            )
            """
        )
        conn.commit()
