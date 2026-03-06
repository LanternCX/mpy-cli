"""Command line interface for mpy-cli."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Protocol, Sequence

from mpy_cli.backend.mpremote import (
    CommandExecutionError,
    MpremoteBackend,
    RemoteDirEntry,
)
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
from mpy_cli.planner import DeployPlan, PlanOperation, build_plan
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
    if args.command == "upload":
        return _cmd_upload(args)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "delete":
        return _cmd_delete(args)
    if args.command == "tree":
        return _cmd_tree(args)

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

    upload_parser = subparsers.add_parser("upload", help="手动单文件上传")
    upload_parser.add_argument("--local", help="本地文件路径")
    upload_parser.add_argument("--remote", help="设备目标路径")
    upload_parser.add_argument("--port", help="设备串口，例如 /dev/ttyACM0")
    upload_parser.add_argument("--yes", action="store_true", help="跳过交互确认")
    upload_parser.add_argument(
        "--no-interactive", action="store_true", help="禁用 questionary 交互"
    )

    run_parser = subparsers.add_parser("run", help="执行设备端脚本")
    run_parser.add_argument("--path", help="设备目标文件路径")
    run_parser.add_argument("--port", help="设备串口，例如 /dev/ttyACM0")
    run_parser.add_argument("--yes", action="store_true", help="跳过交互确认")
    run_parser.add_argument(
        "--no-interactive", action="store_true", help="禁用 questionary 交互"
    )

    delete_parser = subparsers.add_parser("delete", help="删除设备端文件或目录")
    delete_parser.add_argument("--path", help="设备目标路径")
    delete_parser.add_argument("--port", help="设备串口，例如 /dev/ttyACM0")
    delete_parser.add_argument("--yes", action="store_true", help="跳过交互确认")
    delete_parser.add_argument(
        "--no-interactive", action="store_true", help="禁用 questionary 交互"
    )

    tree_parser = subparsers.add_parser("tree", help="读取设备端目录树")
    tree_parser.add_argument("--path", help="设备目标目录路径")
    tree_parser.add_argument("--port", help="设备串口，例如 /dev/ttyACM0")
    tree_parser.add_argument(
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

    project_root = Path.cwd().resolve()
    source_root = _resolve_source_root(
        project_root=project_root, source_dir=cfg.source_dir
    )
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
            changes = collect_git_changes(source_root)
            local_files = []
    except GitDiffError as exc:
        print(f"Git 变更读取失败: {exc}")
        return 1

    plan = build_plan(
        mode=mode,
        local_files=local_files,
        changes=changes,
        matcher=matcher,
        remote_base_dir=cfg.device_upload_dir,
    )
    _print_plan(plan)

    if args.command == "plan":
        return 0

    if not args.yes:
        if not _ask_confirm("确认执行部署？"):
            print("已取消部署")
            return 1
        if mode == "full" and not _ask_confirm(
            "全量模式将清空目标上传目录，确认继续？"
        ):
            print("已取消全量部署")
            return 1

    try:
        backend.ensure_available()
    except CommandExecutionError as exc:
        print(str(exc))
        return 1

    execution_plan = plan
    if mode == "incremental":
        execution_plan = _resolve_incremental_upload_local_paths(
            plan=plan,
            source_root=source_root,
        )

    report = DeployExecutor(backend=backend, logger=logger).execute(
        plan=execution_plan,
        port=port,
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


def _cmd_upload(args: argparse.Namespace) -> int:
    """@brief 执行 upload 子命令。"""

    try:
        cfg = load_config(Path(".mpy-cli.toml"))
    except ConfigError as exc:
        print(f"配置错误: {exc}")
        print("请先运行 `mpy-cli init`")
        return 1

    runtime_paths = ensure_runtime_layout(Path(cfg.runtime_dir))
    logger = setup_logging(runtime_paths.root)

    interactive = not args.no_interactive
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

    local_path = (args.local or "").strip()
    if not local_path:
        if not interactive:
            print("非交互模式下必须通过 --local 指定本地文件路径")
            return 1
        local_path = _ask_text(
            "请输入本地文件路径（例如 seekfree_demo/E01_demo.py）"
        ).strip()

    if not local_path:
        print("本地文件路径不能为空")
        return 1

    default_remote_path = _derive_upload_default_remote_path(
        local_path=local_path,
        project_root=Path.cwd().resolve(),
        source_dir=cfg.source_dir,
    )
    if args.remote is not None and args.remote.strip():
        remote_path = args.remote.strip()
    elif interactive:
        remote_path = _ask_text(
            "请输入设备目标路径（回车使用默认推导路径）",
            default=default_remote_path,
        ).strip()
        if not remote_path:
            remote_path = default_remote_path
    else:
        print("非交互模式下必须通过 --remote 指定设备目标路径")
        return 1

    if not remote_path:
        print("设备目标路径不能为空")
        return 1

    local_file = Path(local_path)
    if not local_file.is_file():
        print(f"本地文件不存在或不是文件: {local_path}")
        return 1

    final_remote_path = _join_upload_target(cfg.device_upload_dir, remote_path)

    print("上传预览：")
    print(f"- 端口: {port}")
    print(f"- 本地: {local_path}")
    print(f"- 远端: :{final_remote_path}")

    if not args.yes and not _ask_confirm("确认执行上传？"):
        print("已取消上传")
        return 1

    try:
        backend.ensure_available()
    except CommandExecutionError as exc:
        print(str(exc))
        return 1

    plan = DeployPlan(
        mode="incremental",
        operations=[
            PlanOperation(
                op_type="upload",
                local_path=local_path,
                remote_path=final_remote_path,
                reason="manual-upload",
            )
        ],
    )
    report = DeployExecutor(backend=backend, logger=logger).execute(
        plan=plan, port=port
    )

    if report.failure_count:
        print("上传失败：")
        for failure in report.failures:
            print(
                f"- {failure.operation.op_type} {failure.operation.remote_path}: {failure.error}"
            )
        return 2

    print("上传成功")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    """@brief 执行 run 子命令。"""

    try:
        cfg = load_config(Path(".mpy-cli.toml"))
    except ConfigError as exc:
        print(f"配置错误: {exc}")
        print("请先运行 `mpy-cli init`")
        return 1

    runtime_paths = ensure_runtime_layout(Path(cfg.runtime_dir))
    logger = setup_logging(runtime_paths.root)

    interactive = not args.no_interactive
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

    target_path = (args.path or "").strip()
    if not target_path:
        if not interactive:
            print("非交互模式下必须通过 --path 指定设备目标文件路径")
            return 1
        target_path = _ask_text(
            "请输入设备目标文件路径（相对 device_upload_dir）"
        ).strip()

    if not target_path:
        print("设备目标文件路径不能为空")
        return 1

    final_remote_path = _join_upload_target(cfg.device_upload_dir, target_path)
    if not final_remote_path:
        print("设备目标文件路径不能为空")
        return 1

    print("执行预览：")
    print(f"- 端口: {port}")
    print(f"- 路径: {target_path}")
    print(f"- 远端: :{final_remote_path}")

    if not args.yes and not _ask_confirm("确认执行脚本？"):
        print("已取消执行")
        return 1

    try:
        backend.ensure_available()
    except CommandExecutionError as exc:
        print(str(exc))
        return 1

    try:
        result = backend.run_file(port=port, remote_path=final_remote_path)
    except Exception as exc:  # noqa: BLE001
        print(f"执行失败: {exc}")
        return 2

    if result is not None:
        stdout = getattr(result, "stdout", "")
        stderr = getattr(result, "stderr", "")
        if isinstance(stdout, str) and stdout.strip():
            print(stdout.rstrip())
        if isinstance(stderr, str) and stderr.strip():
            print(stderr.rstrip())

    logger.info("run 执行完成: %s", final_remote_path)
    print("执行成功")
    return 0


def _cmd_delete(args: argparse.Namespace) -> int:
    """@brief 执行 delete 子命令。"""

    try:
        cfg = load_config(Path(".mpy-cli.toml"))
    except ConfigError as exc:
        print(f"配置错误: {exc}")
        print("请先运行 `mpy-cli init`")
        return 1

    runtime_paths = ensure_runtime_layout(Path(cfg.runtime_dir))
    logger = setup_logging(runtime_paths.root)

    interactive = not args.no_interactive
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

    target_path = (args.path or "").strip()
    if not target_path:
        if not interactive:
            print("非交互模式下必须通过 --path 指定设备目标路径")
            return 1
        target_path = _ask_text("请输入设备目标路径（相对 device_upload_dir）").strip()

    if not target_path:
        print("设备目标路径不能为空")
        return 1

    final_remote_path = _join_upload_target(cfg.device_upload_dir, target_path)
    if not final_remote_path:
        print("设备目标路径不能为空")
        return 1

    print("删除预览：")
    print(f"- 端口: {port}")
    print(f"- 路径: {target_path}")
    print(f"- 远端: :{final_remote_path}")

    if not args.yes and not _ask_confirm("确认执行删除？"):
        print("已取消删除")
        return 1

    try:
        backend.ensure_available()
    except CommandExecutionError as exc:
        print(str(exc))
        return 1

    try:
        backend.delete_path(port=port, remote_path=final_remote_path)
    except Exception as exc:  # noqa: BLE001
        print(f"删除失败: {exc}")
        return 2

    logger.info("delete 执行完成: %s", final_remote_path)
    print("删除成功")
    return 0


def _cmd_tree(args: argparse.Namespace) -> int:
    """@brief 执行 tree 子命令。"""

    try:
        cfg = load_config(Path(".mpy-cli.toml"))
    except ConfigError as exc:
        print(f"配置错误: {exc}")
        print("请先运行 `mpy-cli init`")
        return 1

    runtime_paths = ensure_runtime_layout(Path(cfg.runtime_dir))
    logger = setup_logging(runtime_paths.root)

    interactive = not args.no_interactive
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

    target_path = (args.path or "").strip()
    final_remote_path = _join_upload_target(cfg.device_upload_dir, target_path)

    try:
        backend.ensure_available()
    except CommandExecutionError as exc:
        print(str(exc))
        return 1

    try:
        print(final_remote_path or "/")
        lines = _render_remote_tree_lines(
            backend=backend,
            port=port,
            remote_path=final_remote_path,
            prefix="",
        )
        for line in lines:
            print(line)
    except Exception as exc:  # noqa: BLE001
        print(f"读取目录失败: {exc}")
        return 2

    logger.info("tree 执行完成: %s", final_remote_path or "/")
    return 0


def _render_remote_tree_lines(
    backend: MpremoteBackend,
    port: str,
    remote_path: str,
    prefix: str,
) -> list[str]:
    """@brief 递归渲染设备目录树。"""

    entries: list[RemoteDirEntry] = backend.list_dir(port=port, remote_path=remote_path)
    ordered_entries = sorted(entries, key=lambda item: (not item.is_dir, item.name))

    lines: list[str] = []
    for index, entry in enumerate(ordered_entries):
        is_last = index == len(ordered_entries) - 1
        branch = "└── " if is_last else "├── "
        suffix = "/" if entry.is_dir else ""
        lines.append(f"{prefix}{branch}{entry.name}{suffix}")

        if entry.is_dir:
            child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
            child_path = _join_upload_target(remote_path, entry.name)
            lines.extend(
                _render_remote_tree_lines(
                    backend=backend,
                    port=port,
                    remote_path=child_path,
                    prefix=child_prefix,
                )
            )

    return lines


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


def _resolve_source_root(project_root: Path, source_dir: str) -> Path:
    """@brief 解析配置 source_dir 对应的本地目录绝对路径。"""

    source_path = Path(source_dir)
    if source_path.is_absolute():
        return source_path.resolve()
    return (project_root / source_path).resolve()


def _derive_upload_default_remote_path(
    local_path: str,
    project_root: Path,
    source_dir: str,
) -> str:
    """@brief 计算 upload 交互默认设备路径。"""

    normalized_local_path = local_path.strip().replace("\\", "/")
    source_root = _resolve_source_root(project_root=project_root, source_dir=source_dir)

    local_file = Path(normalized_local_path)
    if local_file.is_absolute():
        resolved_local_file = local_file.resolve()
    else:
        resolved_local_file = (project_root / local_file).resolve()

    try:
        return resolved_local_file.relative_to(source_root).as_posix()
    except ValueError:
        return normalized_local_path


def _resolve_incremental_upload_local_paths(
    plan: DeployPlan,
    source_root: Path,
) -> DeployPlan:
    """@brief 将增量上传的 local_path 解析为 source_dir 下的绝对路径。"""

    normalized_source_root = source_root.resolve()
    operations: list[PlanOperation] = []

    for operation in plan.operations:
        if operation.op_type != "upload" or operation.local_path is None:
            operations.append(operation)
            continue

        resolved_local_path = _resolve_incremental_local_path(
            local_path=operation.local_path,
            source_root=normalized_source_root,
        )
        operations.append(
            PlanOperation(
                op_type=operation.op_type,
                local_path=resolved_local_path,
                remote_path=operation.remote_path,
                reason=operation.reason,
            )
        )

    return DeployPlan(mode=plan.mode, operations=operations)


def _resolve_incremental_local_path(
    local_path: str,
    source_root: Path,
) -> str:
    """@brief 计算增量上传操作对应的本地绝对文件路径。"""

    normalized_path = local_path.strip().replace("\\", "/").lstrip("/")
    resolved_path = (source_root / normalized_path).resolve()
    return resolved_path.as_posix()


def _join_upload_target(remote_base_dir: str, remote_path: str) -> str:
    """@brief 计算 upload 命令最终设备目标路径。"""

    normalized_base = remote_base_dir.strip().replace("\\", "/").strip("/")
    normalized_path = remote_path.strip().replace("\\", "/").lstrip("/")

    if not normalized_base:
        return normalized_path
    if not normalized_path:
        return normalized_base
    return f"{normalized_base}/{normalized_path}"


def _ask_text(message: str, default: str = "") -> str:
    """@brief questionary 文本输入封装。"""

    try:
        import questionary

        value = questionary.text(message, default=default).ask()
        if value:
            return str(value)
    except Exception:  # noqa: BLE001
        pass
    return default


def _ask_confirm(message: str) -> bool:
    """@brief questionary 确认输入封装。"""

    try:
        import questionary

        value = questionary.confirm(message, default=False).ask()
        return bool(value)
    except Exception:  # noqa: BLE001
        answer = input(f"{message} [y/N]: ").strip().lower()
        return answer in {"y", "yes"}
