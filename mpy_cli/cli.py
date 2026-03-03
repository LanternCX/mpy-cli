"""Command line interface for mpy-cli."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Protocol, Sequence

from mpy_cli.backend.mpremote import CommandExecutionError, MpremoteBackend
from mpy_cli.config import (
    ConfigError,
    default_config,
    init_config,
    load_config,
    save_config,
)
from mpy_cli.config_wizard import run_config_wizard
from mpy_cli.executor import DeployExecutor
from mpy_cli.gitdiff import GitDiffError, collect_git_changes
from mpy_cli.ignore import IgnoreMatcher, init_ignore
from mpy_cli.logging import setup_logging
from mpy_cli.planner import DeployPlan, build_plan
from mpy_cli.runtime import ensure_runtime_layout
from mpy_cli.scanner import list_local_files


class PortScanner(Protocol):
    """@brief 端口扫描接口协议。"""

    def list_ports(self) -> list[str]:
        """@brief 返回可用串口列表。"""


def main(argv: Sequence[str] | None = None) -> int:
    """@brief mpy-cli 主入口。

    @param argv 命令行参数。
    @return 进程退出码。
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _cmd_init(force=args.force, interactive=not args.no_interactive)
    if args.command == "config":
        return _cmd_config()
    if args.command in {"plan", "deploy"}:
        return _cmd_plan_or_deploy(args)

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    """@brief 构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        prog="mpy-cli", description="MicroPython 交互式部署工具"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化配置与运行目录")
    init_parser.add_argument("--force", action="store_true", help="覆盖已有初始化文件")
    init_parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="跳过初始化后的交互式配置向导",
    )

    subparsers.add_parser("config", help="通过交互向导更新配置")

    for name in ("plan", "deploy"):
        cmd = subparsers.add_parser(name, help=f"{name} 模式")
        cmd.add_argument("--mode", choices=["full", "incremental"], help="同步模式")
        cmd.add_argument("--port", help="设备串口，例如 /dev/ttyACM0")
        cmd.add_argument("--yes", action="store_true", help="跳过交互确认")
        cmd.add_argument(
            "--no-interactive", action="store_true", help="禁用 questionary 交互"
        )

    return parser


def _cmd_init(force: bool, interactive: bool) -> int:
    """@brief 执行 init 子命令。"""

    config_path = Path(".mpy-cli.toml")
    init_config(config_path, overwrite=force)
    init_ignore(Path(".mpyignore"), overwrite=force)
    ensure_runtime_layout(Path(".mpy-cli"))

    if interactive:
        try:
            current = load_config(config_path)
        except ConfigError:
            current = default_config()

        scanner = MpremoteBackend(binary=current.mpremote_binary)
        updated = run_config_wizard(current, scanner=scanner)
        save_config(config_path, updated)
        init_ignore(Path(updated.ignore_file))
        ensure_runtime_layout(Path(updated.runtime_dir))
        print("初始化完成并写入交互式配置")
        return 0

    print("初始化完成：.mpy-cli.toml / .mpyignore / .mpy-cli/")
    return 0


def _cmd_config() -> int:
    """@brief 执行配置向导子命令。"""

    config_path = Path(".mpy-cli.toml")
    init_config(config_path)

    try:
        current = load_config(config_path)
    except ConfigError:
        current = default_config()

    scanner = MpremoteBackend(binary=current.mpremote_binary)
    updated = run_config_wizard(current, scanner=scanner)
    save_config(config_path, updated)
    init_ignore(Path(updated.ignore_file))
    ensure_runtime_layout(Path(updated.runtime_dir))

    print("配置已更新，可直接执行 plan/deploy")
    return 0


def _cmd_plan_or_deploy(args: argparse.Namespace) -> int:
    """@brief 执行 plan/deploy 子命令。"""

    try:
        cfg = load_config(Path(".mpy-cli.toml"))
    except ConfigError as exc:
        print(f"配置错误: {exc}")
        print("请先运行 `mpy-cli init`")
        return 1

    runtime_paths = ensure_runtime_layout(Path(cfg.runtime_dir))
    logger = setup_logging(runtime_paths.root)

    interactive = not args.no_interactive
    mode = args.mode or cfg.sync.mode
    if interactive and not args.mode:
        mode = _ask_select(
            "请选择同步模式", ["incremental", "full"], default=cfg.sync.mode
        )

    backend = MpremoteBackend(binary=cfg.mpremote_binary)
    port = _resolve_port(
        arg_port=args.port,
        config_port=cfg.serial_port,
        interactive=interactive,
        scanner=backend,
    )

    if not port:
        print("缺少串口参数，请通过 --port 或配置文件提供")
        return 1

    project_root = Path.cwd()
    matcher = IgnoreMatcher.from_file(project_root / cfg.ignore_file)

    try:
        if mode == "full":
            local_files = list_local_files(
                project_root=project_root,
                source_dir=cfg.source_dir,
                runtime_dir=cfg.runtime_dir,
            )
            changes = []
        else:
            changes = collect_git_changes(project_root)
            local_files = []
    except GitDiffError as exc:
        print(f"Git 变更读取失败: {exc}")
        return 1

    plan = build_plan(
        mode=mode, local_files=local_files, changes=changes, matcher=matcher
    )
    _print_plan(plan)

    if args.command == "plan":
        return 0

    if not args.yes:
        if not _ask_confirm("确认执行部署？"):
            print("已取消部署")
            return 1
        if mode == "full" and not _ask_confirm("全量模式将清空设备根目录，确认继续？"):
            print("已取消全量部署")
            return 1

    try:
        backend.ensure_available()
    except CommandExecutionError as exc:
        print(str(exc))
        return 1

    report = DeployExecutor(backend=backend, logger=logger).execute(
        plan=plan, port=port
    )
    logger.info(
        "部署完成: success=%s failure=%s", report.success_count, report.failure_count
    )

    if report.failure_count:
        print("部署完成，但存在失败项：")
        for failure in report.failures:
            print(
                f"- {failure.operation.op_type} {failure.operation.remote_path}: {failure.error}"
            )
        return 2

    print("部署成功")
    return 0


def _print_plan(plan: DeployPlan) -> None:
    """@brief 输出部署计划摘要。"""

    wipe_count = sum(1 for op in plan.operations if op.op_type == "wipe")
    upload_count = sum(1 for op in plan.operations if op.op_type == "upload")
    delete_count = sum(1 for op in plan.operations if op.op_type == "delete")

    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title=f"部署计划 ({plan.mode})")
        table.add_column("类型")
        table.add_column("数量", justify="right")
        table.add_row("wipe", str(wipe_count))
        table.add_row("upload", str(upload_count))
        table.add_row("delete", str(delete_count))
        Console().print(table)
    except Exception:  # noqa: BLE001
        print(
            f"部署计划({plan.mode}) wipe={wipe_count} upload={upload_count} delete={delete_count}"
        )


def _resolve_port(
    arg_port: str | None,
    config_port: str | None,
    interactive: bool,
    scanner: PortScanner,
) -> str | None:
    """@brief 解析端口来源优先级。

    @param arg_port 命令行端口参数。
    @param config_port 配置文件端口。
    @param interactive 是否交互模式。
    @param scanner 端口扫描器。
    @return 最终端口，若无则返回 None。
    """

    if arg_port:
        return arg_port
    if config_port:
        return config_port
    if not interactive:
        return None

    scanned = _scan_and_select_port(scanner)
    if scanned:
        return scanned

    print("未扫描到可用设备端口，将回退到手动输入")
    manual = _ask_text("请输入设备串口（例如 /dev/ttyACM0 或 COM3）")
    return manual or None


def _scan_and_select_port(scanner: PortScanner) -> str | None:
    """@brief 扫描并选择端口。"""

    try:
        ports = scanner.list_ports()
    except Exception:  # noqa: BLE001
        return None

    if not ports:
        return None

    if len(ports) == 1:
        only_port = ports[0]
        if _ask_confirm(f"检测到端口 {only_port}，是否使用该端口？"):
            return only_port
        return None

    selected = _ask_select("扫描到多个设备端口，请选择", ports, default=ports[0])
    return selected or None


def _ask_select(message: str, choices: list[str], default: str) -> str:
    """@brief questionary 单选封装。"""

    try:
        import questionary

        value = questionary.select(message, choices=choices, default=default).ask()
        if value:
            return value
    except Exception:  # noqa: BLE001
        pass
    return default


def _ask_text(message: str) -> str:
    """@brief questionary 文本输入封装。"""

    try:
        import questionary

        value = questionary.text(message).ask()
        if value:
            return str(value)
    except Exception:  # noqa: BLE001
        pass
    return ""


def _ask_confirm(message: str) -> bool:
    """@brief questionary 确认输入封装。"""

    try:
        import questionary

        value = questionary.confirm(message, default=False).ask()
        return bool(value)
    except Exception:  # noqa: BLE001
        answer = input(f"{message} [y/N]: ").strip().lower()
        return answer in {"y", "yes"}
