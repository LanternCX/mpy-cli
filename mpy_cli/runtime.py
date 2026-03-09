"""Runtime directory and state management."""

from __future__ import annotations

import sqlite3
from datetime import datetime
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


def list_scanned_ports(db_path: Path) -> list[str]:
    """@brief 按最近扫描时间返回已缓存端口列表。

    @param db_path 运行时数据库路径。
    @return 端口列表，最近扫描优先。
    """

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT port
            FROM scanned_ports
            ORDER BY last_seen_at DESC, port ASC
            """
        ).fetchall()
    return [str(row[0]) for row in rows]


def list_successful_scanned_ports(db_path: Path) -> list[str]:
    """@brief 按最近成功探测时间返回成功缓存端口列表。

    @param db_path 运行时数据库路径。
    @return 端口列表，最近成功优先。
    """

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT port
            FROM scanned_ports
            WHERE last_success_at IS NOT NULL
            ORDER BY last_success_at DESC, port ASC
            """
        ).fetchall()
    return [str(row[0]) for row in rows]


def upsert_scanned_ports(
    db_path: Path,
    ports: list[str],
    recorded_at: str | None = None,
) -> None:
    """@brief 写入或刷新已扫描端口缓存。

    @param db_path 运行时数据库路径。
    @param ports 本次扫描看到的端口列表。
    @param recorded_at 可选记录时间，用于测试注入。
    """

    normalized_ports = _normalize_ports(ports)
    if not normalized_ports:
        return

    timestamp = recorded_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(db_path) as conn:
        for port in normalized_ports:
            conn.execute(
                """
                INSERT OR IGNORE INTO scanned_ports (
                    port,
                    first_seen_at,
                    last_seen_at,
                    last_success_at
                )
                VALUES (?, ?, ?, NULL)
                """,
                (port, timestamp, timestamp),
            )
            conn.execute(
                "UPDATE scanned_ports SET last_seen_at = ? WHERE port = ?",
                (timestamp, port),
            )
        conn.commit()


def clear_scan_records(db_path: Path) -> None:
    """@brief 清空扫描历史与成功缓存。

    @param db_path 运行时数据库路径。
    """

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM scanned_ports")
        conn.commit()


def mark_scanned_port_successes(
    db_path: Path,
    ports: list[str],
    recorded_at: str | None = None,
) -> None:
    """@brief 标记端口为成功探测过。

    @param db_path 运行时数据库路径。
    @param ports 本次探测成功的端口列表。
    @param recorded_at 可选记录时间，用于测试注入。
    """

    normalized_ports = _normalize_ports(ports)
    timestamp = recorded_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE scanned_ports SET last_success_at = NULL")
        for port in normalized_ports:
            conn.execute(
                """
                INSERT OR IGNORE INTO scanned_ports (
                    port,
                    first_seen_at,
                    last_seen_at,
                    last_success_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (port, timestamp, timestamp, timestamp),
            )
            conn.execute(
                """
                UPDATE scanned_ports
                SET last_seen_at = ?, last_success_at = ?
                WHERE port = ?
                """,
                (timestamp, timestamp, port),
            )
        conn.commit()


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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scanned_ports (
                port TEXT PRIMARY KEY,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                last_success_at TEXT
            )
            """
        )
        _ensure_scanned_ports_columns(conn)
        conn.commit()


def _normalize_ports(ports: list[str]) -> list[str]:
    """@brief 去重并归一化端口列表。"""

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_port in ports:
        port = raw_port.strip()
        if not port or port in seen:
            continue
        seen.add(port)
        normalized.append(port)
    return normalized


def _ensure_scanned_ports_columns(conn: sqlite3.Connection) -> None:
    """@brief 为旧版 scanned_ports 表补齐缺失字段。"""

    rows = conn.execute("PRAGMA table_info(scanned_ports)").fetchall()
    columns = {str(row[1]) for row in rows}
    if "last_success_at" not in columns:
        conn.execute("ALTER TABLE scanned_ports ADD COLUMN last_success_at TEXT")
