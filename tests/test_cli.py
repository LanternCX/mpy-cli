"""CLI command tests."""

from dataclasses import dataclass
from pathlib import Path

from mpy_cli.config import AppConfig, SyncConfig
from mpy_cli.cli import _resolve_port, build_parser, main
from mpy_cli.executor import ExecutionReport
from mpy_cli.gitdiff import ChangeEntry


def _run_main(argv: list[str]) -> int:
    """@brief 运行 main 并将 argparse 的退出转换为返回码。"""

    try:
        return main(argv)
    except SystemExit as exc:
        return int(exc.code)


@dataclass
class FakeScanner:
    """@brief 测试用端口扫描器。"""

    ports: list[str]
    called: bool = False

    def list_ports(self) -> list[str]:
        """@brief 返回预设端口列表。"""

        self.called = True
        return self.ports


def test_init_command_creates_config_and_ignore(tmp_path: Path, monkeypatch) -> None:
    """@brief init command should create config, ignore, and runtime dir."""
    monkeypatch.chdir(tmp_path)

    code = main(["init"])

    assert code == 0
    assert (tmp_path / ".mpy-cli.toml").exists()
    assert (tmp_path / ".mpyignore").exists()
    assert (tmp_path / ".mpy-cli").exists()


def test_plan_command_accepts_short_options() -> None:
    """@brief plan 应支持 mode/base/port/no-interactive/yes 的短选项。"""

    parser = build_parser()

    args = parser.parse_args(
        ["plan", "-m", "full", "-b", "HEAD~1", "-p", "COM3", "-n", "-y"]
    )

    assert args.command == "plan"
    assert args.mode == "full"
    assert args.base == "HEAD~1"
    assert args.port == "COM3"
    assert args.no_interactive is True
    assert args.yes is True


def test_cli_short_options_cover_all_approved_mappings() -> None:
    """@brief 代表性子命令应支持已批准的短选项映射。"""

    parser = build_parser()

    init_args = parser.parse_args(["init", "-f", "-n"])
    assert init_args.command == "init"
    assert init_args.force is True
    assert init_args.no_interactive is True

    list_args = parser.parse_args(
        ["list", "-w", "4", "-t", "1.5", "-s", "full-only", "-r"]
    )
    assert list_args.command == "list"
    assert list_args.workers == 4
    assert list_args.probe_timeout == 1.5
    assert list_args.scan_mode == "full-only"
    assert list_args.reset is True

    upload_args = parser.parse_args(
        ["upload", "-l", "main.py", "-r", ":main.py", "-p", "COM3", "-n", "-y"]
    )
    assert upload_args.command == "upload"
    assert upload_args.local == "main.py"
    assert upload_args.remote == ":main.py"
    assert upload_args.port == "COM3"
    assert upload_args.no_interactive is True
    assert upload_args.yes is True

    run_args = parser.parse_args(["run", "-f", "boot.py", "-p", "COM3", "-n", "-y"])
    assert run_args.command == "run"
    assert run_args.path == "boot.py"
    assert run_args.port == "COM3"
    assert run_args.no_interactive is True
    assert run_args.yes is True

    delete_args = parser.parse_args(
        ["delete", "-f", "old.py", "-p", "COM3", "-n", "-y"]
    )
    assert delete_args.command == "delete"
    assert delete_args.path == "old.py"
    assert delete_args.port == "COM3"
    assert delete_args.no_interactive is True
    assert delete_args.yes is True


def test_tree_command_accepts_path_short_option_a() -> None:
    """@brief tree 应为 path 使用 -a 短选项以避免与其他冲突。"""

    parser = build_parser()

    args = parser.parse_args(["tree", "-a", "lib", "-p", "COM3", "-n"])

    assert args.command == "tree"
    assert args.path == "lib"
    assert args.port == "COM3"
    assert args.no_interactive is True


def test_list_command_prints_all_detected_devices_without_config(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    """@brief list 应可在无配置文件时输出全部探测到的设备。"""

    monkeypatch.chdir(tmp_path)

    @dataclass
    class FakeDevice:
        port: str
        implementation: str
        version: str
        platform: str
        machine: str

    class FakeBackend:
        """@brief list 测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["/dev/ttyACM0", "COM3"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            if not ports:
                return []
            assert ports == ["/dev/ttyACM0", "COM3"]
            return [
                FakeDevice(
                    port="/dev/ttyACM0",
                    implementation="MicroPython",
                    version="1.24.1",
                    platform="esp32",
                    machine="ESP32 Generic",
                ),
                FakeDevice(
                    port="COM3",
                    implementation="MicroPython",
                    version="1.23.0",
                    platform="rp2",
                    machine="Raspberry Pi Pico",
                ),
            ]

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = _run_main(["list"])

    assert code == 0
    output = capsys.readouterr().out
    assert "发现 2 个可用设备" in output
    assert "/dev/ttyACM0" in output
    assert "COM3" in output
    assert "ESP32 Generic" in output
    assert "Raspberry Pi Pico" in output


def test_list_command_reports_no_detected_devices(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    """@brief list 未探测到设备时应给出明确提示。"""

    monkeypatch.chdir(tmp_path)

    class FakeBackend:
        """@brief list 空结果测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return []

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            assert ports == []
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = _run_main(["list"])

    assert code == 0
    output = capsys.readouterr().out
    assert "未探测到可用的 MicroPython 设备" in output


def test_list_command_passes_workers_and_probe_timeout_to_backend(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief list 应将并发和超时参数透传给 backend。"""

    monkeypatch.chdir(tmp_path)
    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief list 参数透传测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["COM3"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            captured["ports"] = ports
            captured["workers"] = workers
            captured["probe_timeout"] = probe_timeout
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = _run_main(["list", "--workers", "4", "--probe-timeout", "1.5"])

    assert code == 0
    assert captured == {"ports": ["COM3"], "workers": 4, "probe_timeout": 1.5}


def test_list_command_uses_default_probe_timeout_of_one_second(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief list 默认应使用 1.0 秒探测超时。"""

    monkeypatch.chdir(tmp_path)
    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief list 默认超时测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["COM3"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            captured["workers"] = workers
            captured["probe_timeout"] = probe_timeout
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = _run_main(["list"])

    assert code == 0
    assert captured == {"workers": 8, "probe_timeout": 1.0}


def test_list_command_known_first_uses_cached_available_ports_then_falls_back(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief known-first 应先探测缓存且当前可用端口，失败后回退全量探测。"""

    monkeypatch.chdir(tmp_path)
    probed_ports: list[list[str]] = []
    saved_ports: dict[str, object] = {}

    class FakeBackend:
        """@brief list 缓存优先测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["COM3", "COM7"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            probed_ports.append(list(ports or []))
            if ports == ["COM3"]:
                return []
            return [
                type(
                    "FakeDevice",
                    (),
                    {
                        "port": "COM7",
                        "implementation": "MicroPython",
                        "version": "1.20.0",
                        "platform": "rp2",
                        "machine": "Pico",
                    },
                )()
            ]

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr(
        "mpy_cli.cli.list_successful_scanned_ports",
        lambda _db_path: ["COM3", "COM9"],
    )
    monkeypatch.setattr(
        "mpy_cli.cli.upsert_scanned_ports",
        lambda db_path, ports: saved_ports.update({"db_path": db_path, "ports": ports}),
    )
    monkeypatch.setattr(
        "mpy_cli.cli.mark_scanned_port_successes",
        lambda db_path, ports: saved_ports.update(
            {"success_db_path": db_path, "success_ports": ports}
        ),
    )

    code = _run_main(["list"])

    assert code == 0
    assert probed_ports == [["COM3"], ["COM7"]]
    assert saved_ports["ports"] == ["COM3", "COM7"]
    assert saved_ports["success_ports"] == ["COM7"]


def test_list_command_known_first_without_available_known_ports_scans_current_once(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief known-first 在无可用缓存端口时不应重复探测当前端口。"""

    monkeypatch.chdir(tmp_path)
    probed_ports: list[list[str]] = []

    class FakeBackend:
        """@brief list 空缓存命中测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["COM3", "COM7"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            probed_ports.append(list(ports or []))
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr(
        "mpy_cli.cli.list_successful_scanned_ports",
        lambda _db_path: ["COM9"],
    )
    monkeypatch.setattr(
        "mpy_cli.cli.upsert_scanned_ports", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        "mpy_cli.cli.mark_scanned_port_successes", lambda *_args, **_kwargs: None
    )

    code = _run_main(["list"])

    assert code == 0
    assert probed_ports == [["COM3", "COM7"]]


def test_list_command_scan_mode_full_only_probes_all_current_ports(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief full-only 模式应直接探测当前所有可用端口。"""

    monkeypatch.chdir(tmp_path)
    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief list scan-mode 测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["COM3", "COM7"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            captured["ports"] = ports
            captured["workers"] = workers
            captured["probe_timeout"] = probe_timeout
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr(
        "mpy_cli.cli.list_successful_scanned_ports",
        lambda _db_path: ["COM9"],
    )
    monkeypatch.setattr(
        "mpy_cli.cli.upsert_scanned_ports", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        "mpy_cli.cli.mark_scanned_port_successes", lambda *_args, **_kwargs: None
    )

    code = _run_main(
        [
            "list",
            "--scan-mode",
            "full-only",
            "--workers",
            "4",
            "--probe-timeout",
            "1.5",
        ]
    )

    assert code == 0
    assert captured == {
        "ports": ["COM3", "COM7"],
        "workers": 4,
        "probe_timeout": 1.5,
    }


def test_list_command_reset_clears_cache_before_scanning(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief reset 应先清空缓存，再执行新一轮扫描。"""

    monkeypatch.chdir(tmp_path)
    calls: list[tuple[str, object]] = []

    class FakeBackend:
        """@brief list reset 测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            calls.append(("list_ports", None))
            return ["COM3"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            calls.append(("list_devices", list(ports or [])))
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr(
        "mpy_cli.cli.clear_scan_records",
        lambda _db_path: calls.append(("clear", None)),
    )
    monkeypatch.setattr(
        "mpy_cli.cli.list_successful_scanned_ports",
        lambda _db_path: calls.append(("list_successful", None)) or [],
    )
    monkeypatch.setattr(
        "mpy_cli.cli.upsert_scanned_ports",
        lambda _db_path, ports: calls.append(("upsert", list(ports))),
    )
    monkeypatch.setattr(
        "mpy_cli.cli.mark_scanned_port_successes",
        lambda _db_path, ports: calls.append(("mark_success", list(ports))),
    )

    code = _run_main(["list", "--reset"])

    assert code == 0
    assert calls == [
        ("clear", None),
        ("list_successful", None),
        ("list_ports", None),
        ("upsert", ["COM3"]),
        ("list_devices", ["COM3"]),
        ("mark_success", []),
    ]


def test_list_command_rejects_legacy_reset_scan_records_flag() -> None:
    """@brief list 应仅保留精简后的 --reset 参数。"""

    code = _run_main(["list", "--reset-scan-records"])

    assert code == 2


def test_list_command_known_first_ignores_history_without_success(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief known-first 第一阶段只应使用成功缓存，不应使用全部扫描历史。"""

    monkeypatch.chdir(tmp_path)
    probed_ports: list[list[str]] = []

    class FakeBackend:
        """@brief list 成功缓存优先测试后端。"""

        def __init__(self, binary: str = "mpremote", logger=None) -> None:  # noqa: ANN001
            self.binary = binary
            self.logger = logger

        def ensure_available(self) -> None:
            return

        def list_ports(self) -> list[str]:
            return ["COM3", "COM7", "COM8"]

        def list_devices(
            self,
            ports: list[str] | None = None,
            workers: int = 8,
            probe_timeout: float = 1.0,
        ):  # noqa: ANN201
            probed_ports.append(list(ports or []))
            return []

    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr(
        "mpy_cli.cli.list_successful_scanned_ports",
        lambda _db_path: ["COM7"],
    )
    monkeypatch.setattr(
        "mpy_cli.cli.upsert_scanned_ports", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        "mpy_cli.cli.mark_scanned_port_successes", lambda *_args, **_kwargs: None
    )

    code = _run_main(["list"])

    assert code == 0
    assert probed_ports == [["COM7"], ["COM3", "COM8"]]


def test_resolve_port_uses_scanned_choice_in_interactive(monkeypatch) -> None:  # noqa: ANN001
    """@brief 交互模式下无端口时应扫描并选择。"""

    scanner = FakeScanner(ports=["/dev/ttyACM0", "/dev/ttyUSB0"])
    monkeypatch.setattr(
        "mpy_cli.cli._ask_select", lambda *_args, **_kwargs: "/dev/ttyUSB0"
    )

    selected = _resolve_port(
        arg_port=None,
        config_port=None,
        interactive=True,
        scanner=scanner,
    )

    assert scanner.called is True
    assert selected == "/dev/ttyUSB0"


def test_resolve_port_falls_back_to_manual_input_when_scan_empty(monkeypatch) -> None:  # noqa: ANN001
    """@brief 扫描无结果时应回退到手动输入。"""

    scanner = FakeScanner(ports=[])
    monkeypatch.setattr("mpy_cli.cli._ask_text", lambda *_args, **_kwargs: "COM3")

    selected = _resolve_port(
        arg_port=None,
        config_port=None,
        interactive=True,
        scanner=scanner,
    )

    assert scanner.called is True
    assert selected == "COM3"


def test_resolve_port_non_interactive_without_port_returns_none() -> None:
    """@brief 非交互模式下无端口时应保持 None。"""

    scanner = FakeScanner(ports=["/dev/ttyACM0"])

    selected = _resolve_port(
        arg_port=None,
        config_port=None,
        interactive=False,
        scanner=scanner,
    )

    assert scanner.called is False
    assert selected is None


def test_config_command_updates_existing_config(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """@brief config 子命令应通过向导更新配置文件。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    updated = AppConfig(
        serial_port="COM5",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="apps/demo",
        sync=SyncConfig(mode="full"),
    )

    monkeypatch.setattr(
        "mpy_cli.cli.run_config_wizard", lambda *_args, **_kwargs: updated
    )

    code = main(["config"])

    assert code == 0
    content = (tmp_path / ".mpy-cli.toml").read_text(encoding="utf-8")
    assert "COM5" in content
    assert "mode = 'full'" in content
    assert "device_upload_dir = 'apps/demo'" in content


def test_upload_non_interactive_requires_local_and_remote(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief upload 非交互模式缺少路径参数时应报错。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    code = main(["upload", "--no-interactive", "--port", "COM3", "--yes"])

    assert code == 1


def test_run_non_interactive_requires_path(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """@brief run 非交互模式缺少 path 参数时应报错。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    code = main(["run", "--no-interactive", "--port", "COM3", "--yes"])

    assert code == 1


def test_delete_non_interactive_requires_path(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """@brief delete 非交互模式缺少 path 参数时应报错。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    code = main(["delete", "--no-interactive", "--port", "COM3", "--yes"])

    assert code == 1


def test_delete_executes_remote_path_with_device_upload_prefix(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief delete 应按 device_upload_dir 拼接设备目标路径。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="apps/demo",
        sync=SyncConfig(mode="incremental"),
    )

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief delete 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            captured["ensure_available"] = True

        def delete_path(self, port: str, remote_path: str):  # noqa: ANN201
            captured["port"] = port
            captured["remote_path"] = remote_path
            return None

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(
        [
            "delete",
            "--no-interactive",
            "--yes",
            "--port",
            "COM3",
            "--path",
            "obsolete.py",
        ]
    )

    assert code == 0
    assert captured["ensure_available"] is True
    assert captured["port"] == "COM3"
    assert captured["remote_path"] == "apps/demo/obsolete.py"


def test_delete_returns_failure_code_when_backend_delete_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief delete 执行失败时应返回失败退出码。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    class FakeBackend:
        """@brief delete 失败路径测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

        def delete_path(self, port: str, remote_path: str):  # noqa: ANN201
            raise RuntimeError("boom")

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(
        [
            "delete",
            "--no-interactive",
            "--yes",
            "--port",
            "COM3",
            "--path",
            "obsolete.py",
        ]
    )

    assert code == 2


def test_run_executes_remote_file_with_device_upload_prefix(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief run 应按 device_upload_dir 拼接设备目标路径。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="apps/demo",
        sync=SyncConfig(mode="incremental"),
    )

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief run 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            captured["ensure_available"] = True

        def run_file(self, port: str, remote_path: str):  # noqa: ANN201
            captured["port"] = port
            captured["remote_path"] = remote_path
            return None

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(
        [
            "run",
            "--no-interactive",
            "--yes",
            "--port",
            "COM3",
            "--path",
            "main.py",
        ]
    )

    assert code == 0
    assert captured["ensure_available"] is True
    assert captured["port"] == "COM3"
    assert captured["remote_path"] == "apps/demo/main.py"


def test_run_returns_failure_code_when_backend_run_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief run 执行失败时应返回失败退出码。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    class FakeBackend:
        """@brief run 失败路径测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

        def run_file(self, port: str, remote_path: str):  # noqa: ANN201
            raise RuntimeError("boom")

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(
        [
            "run",
            "--no-interactive",
            "--yes",
            "--port",
            "COM3",
            "--path",
            "main.py",
        ]
    )

    assert code == 2


def test_upload_interactive_defaults_remote_to_local_path(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief upload 交互模式下远端路径默认应与本地输入一致。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    local_file = tmp_path / "seekfree_demo" / "E01_demo.py"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text("print('ok')\n", encoding="utf-8")

    asked_defaults: list[str] = []

    def fake_ask_text(message: str, default: str = "") -> str:
        if "本地文件路径" in message:
            return "seekfree_demo/E01_demo.py"
        if "设备目标路径" in message:
            asked_defaults.append(default)
            return default
        return default

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief upload 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

    class FakeExecutor:
        """@brief upload 测试执行器。"""

        def __init__(self, backend: object, logger: object | None = None) -> None:
            self.backend = backend
            self.logger = logger

        def execute(self, plan, port: str) -> ExecutionReport:  # noqa: ANN001
            captured["plan"] = plan
            captured["port"] = port
            return ExecutionReport(success_count=1, failure_count=0, failures=[])

    monkeypatch.setattr("mpy_cli.cli._ask_text", fake_ask_text)
    monkeypatch.setattr("mpy_cli.cli._ask_confirm", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr("mpy_cli.cli.DeployExecutor", FakeExecutor)

    code = main(["upload", "--port", "COM3"])

    assert code == 0
    assert asked_defaults == ["seekfree_demo/E01_demo.py"]

    plan = captured["plan"]
    operation = plan.operations[0]
    assert operation.local_path == "seekfree_demo/E01_demo.py"
    assert operation.remote_path == "seekfree_demo/E01_demo.py"
    assert captured["port"] == "COM3"


def test_upload_interactive_allows_custom_remote_path(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief upload 交互模式应允许手动修改远端路径。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    local_file = tmp_path / "seekfree_demo" / "E01_demo.py"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text("print('ok')\n", encoding="utf-8")

    def fake_ask_text(message: str, default: str = "") -> str:
        if "本地文件路径" in message:
            return "seekfree_demo/E01_demo.py"
        if "设备目标路径" in message:
            return "apps/custom.py"
        return default

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief upload 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

    class FakeExecutor:
        """@brief upload 测试执行器。"""

        def __init__(self, backend: object, logger: object | None = None) -> None:
            self.backend = backend
            self.logger = logger

        def execute(self, plan, port: str) -> ExecutionReport:  # noqa: ANN001
            captured["plan"] = plan
            captured["port"] = port
            return ExecutionReport(success_count=1, failure_count=0, failures=[])

    monkeypatch.setattr("mpy_cli.cli._ask_text", fake_ask_text)
    monkeypatch.setattr("mpy_cli.cli._ask_confirm", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr("mpy_cli.cli.DeployExecutor", FakeExecutor)

    code = main(["upload", "--port", "COM3"])

    assert code == 0
    plan = captured["plan"]
    operation = plan.operations[0]
    assert operation.local_path == "seekfree_demo/E01_demo.py"
    assert operation.remote_path == "apps/custom.py"


def test_upload_interactive_defaults_remote_to_source_relative_path(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief source_dir 非根目录时 upload 默认远端应为相对 source_dir 路径。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    local_file = tmp_path / "app_src" / "seekfree_demo" / "E01_demo.py"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text("print('ok')\n", encoding="utf-8")

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="app_src",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    asked_defaults: list[str] = []

    def fake_ask_text(message: str, default: str = "") -> str:
        if "本地文件路径" in message:
            return "app_src/seekfree_demo/E01_demo.py"
        if "设备目标路径" in message:
            asked_defaults.append(default)
            return default
        return default

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief upload 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

    class FakeExecutor:
        """@brief upload 测试执行器。"""

        def __init__(self, backend: object, logger: object | None = None) -> None:
            self.backend = backend
            self.logger = logger

        def execute(self, plan, port: str) -> ExecutionReport:  # noqa: ANN001
            captured["plan"] = plan
            captured["port"] = port
            return ExecutionReport(success_count=1, failure_count=0, failures=[])

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli._ask_text", fake_ask_text)
    monkeypatch.setattr("mpy_cli.cli._ask_confirm", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr("mpy_cli.cli.DeployExecutor", FakeExecutor)

    code = main(["upload", "--port", "COM3"])

    assert code == 0
    assert asked_defaults == ["seekfree_demo/E01_demo.py"]
    plan = captured["plan"]
    operation = plan.operations[0]
    assert operation.remote_path == "seekfree_demo/E01_demo.py"


def test_upload_interactive_defaults_remote_to_local_when_outside_source_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief 本地文件不在 source_dir 下时 upload 默认远端应回退为本地路径。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    local_file = tmp_path / "external" / "E01_demo.py"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text("print('ok')\n", encoding="utf-8")

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="app_src",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    asked_defaults: list[str] = []

    def fake_ask_text(message: str, default: str = "") -> str:
        if "本地文件路径" in message:
            return "external/E01_demo.py"
        if "设备目标路径" in message:
            asked_defaults.append(default)
            return default
        return default

    class FakeBackend:
        """@brief upload 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

    class FakeExecutor:
        """@brief upload 测试执行器。"""

        def __init__(self, backend: object, logger: object | None = None) -> None:
            self.backend = backend
            self.logger = logger

        def execute(self, plan, port: str) -> ExecutionReport:  # noqa: ANN001
            return ExecutionReport(success_count=1, failure_count=0, failures=[])

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli._ask_text", fake_ask_text)
    monkeypatch.setattr("mpy_cli.cli._ask_confirm", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr("mpy_cli.cli.DeployExecutor", FakeExecutor)

    code = main(["upload", "--port", "COM3"])

    assert code == 0
    assert asked_defaults == ["external/E01_demo.py"]


def test_upload_rejects_nonexistent_local_file(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """@brief upload 本地文件不存在时应报错。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    code = main(
        [
            "upload",
            "--no-interactive",
            "--yes",
            "--port",
            "COM3",
            "--local",
            "seekfree_demo/E01_demo.py",
            "--remote",
            "seekfree_demo/E01_demo.py",
        ]
    )

    assert code == 1


def test_plan_incremental_collects_changes_from_source_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief 增量模式应在 source_dir 目录收集 git diff。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    source_root = tmp_path / "app_src"
    source_root.mkdir(parents=True, exist_ok=True)

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="app_src",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    captured_repo_path: dict[str, Path] = {}

    def fake_collect_git_changes(
        repo_path: Path,
        base_ref: str = "HEAD",
    ) -> list[ChangeEntry]:
        captured_repo_path["value"] = repo_path
        captured_repo_path["base_ref"] = base_ref
        return []

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.collect_git_changes", fake_collect_git_changes)

    code = main(["plan", "--no-interactive", "--mode", "incremental", "--port", "COM3"])

    assert code == 0
    assert captured_repo_path["value"] == source_root.resolve()
    assert captured_repo_path["base_ref"] == "HEAD"


def test_plan_incremental_passes_base_ref_to_gitdiff(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief 增量 plan 传入 --base 时应透传到 gitdiff。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    source_root = tmp_path / "app_src"
    source_root.mkdir(parents=True, exist_ok=True)

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="app_src",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    captured: dict[str, object] = {}

    def fake_collect_git_changes(
        repo_path: Path, base_ref: str = "HEAD"
    ) -> list[ChangeEntry]:
        captured["repo_path"] = repo_path
        captured["base_ref"] = base_ref
        return []

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.collect_git_changes", fake_collect_git_changes)

    code = main(
        [
            "plan",
            "--no-interactive",
            "--mode",
            "incremental",
            "--base",
            "abc123",
            "--port",
            "COM3",
        ]
    )

    assert code == 0
    assert captured["repo_path"] == source_root.resolve()
    assert captured["base_ref"] == "abc123"


def test_deploy_incremental_resolves_upload_local_path_from_source_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief 增量部署上传操作应使用 source_dir 下的本地文件路径。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    source_root = tmp_path / "app_src"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "main.py").write_text("print('ok')\n", encoding="utf-8")

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="app_src",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief deploy 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

    class FakeExecutor:
        """@brief deploy 测试执行器。"""

        def __init__(self, backend: object, logger: object | None = None) -> None:
            self.backend = backend
            self.logger = logger

        def execute(self, plan, port: str) -> ExecutionReport:  # noqa: ANN001
            captured["plan"] = plan
            captured["port"] = port
            return ExecutionReport(success_count=1, failure_count=0, failures=[])

    def fake_collect_git_changes(
        _repo_path: Path,
        base_ref: str = "HEAD",
    ) -> list[ChangeEntry]:
        captured["base_ref"] = base_ref
        return [ChangeEntry(status="M", src_path=None, dst_path="main.py")]

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.collect_git_changes", fake_collect_git_changes)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr("mpy_cli.cli.DeployExecutor", FakeExecutor)

    code = main(
        [
            "deploy",
            "--no-interactive",
            "--yes",
            "--mode",
            "incremental",
            "--port",
            "COM3",
        ]
    )

    assert code == 0
    plan = captured["plan"]
    operation = plan.operations[0]
    assert operation.local_path == (source_root / "main.py").resolve().as_posix()
    assert operation.remote_path == "main.py"
    assert captured["port"] == "COM3"
    assert captured["base_ref"] == "HEAD"


def test_deploy_incremental_passes_base_ref_to_gitdiff(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief 增量 deploy 传入 --base 时应透传到 gitdiff。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    source_root = tmp_path / "app_src"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "main.py").write_text("print('ok')\n", encoding="utf-8")

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir="app_src",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    captured: dict[str, object] = {}

    class FakeBackend:
        """@brief deploy 基准参数透传测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

    class FakeExecutor:
        """@brief deploy 基准参数透传测试执行器。"""

        def __init__(self, backend: object, logger: object | None = None) -> None:
            self.backend = backend
            self.logger = logger

        def execute(self, plan, port: str) -> ExecutionReport:  # noqa: ANN001
            captured["plan"] = plan
            captured["port"] = port
            return ExecutionReport(success_count=1, failure_count=0, failures=[])

    def fake_collect_git_changes(
        repo_path: Path, base_ref: str = "HEAD"
    ) -> list[ChangeEntry]:
        captured["repo_path"] = repo_path
        captured["base_ref"] = base_ref
        return [ChangeEntry(status="M", src_path=None, dst_path="main.py")]

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.collect_git_changes", fake_collect_git_changes)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)
    monkeypatch.setattr("mpy_cli.cli.DeployExecutor", FakeExecutor)

    code = main(
        [
            "deploy",
            "--no-interactive",
            "--yes",
            "--mode",
            "incremental",
            "--base",
            "abc123",
            "--port",
            "COM3",
        ]
    )

    assert code == 0
    assert captured["repo_path"] == source_root.resolve()
    assert captured["base_ref"] == "abc123"
    assert captured["port"] == "COM3"


def test_plan_full_rejects_base_ref(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    """@brief full 模式传入 --base 时应直接失败。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)

    code = _run_main(
        [
            "plan",
            "--no-interactive",
            "--mode",
            "full",
            "--base",
            "abc123",
            "--port",
            "COM3",
        ]
    )

    assert code == 1
    assert "--base 仅支持 incremental 模式" in capsys.readouterr().out


def test_tree_executes_remote_list_with_device_upload_prefix(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief tree 应按 device_upload_dir 与 path 组合目标目录。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="apps/demo",
        sync=SyncConfig(mode="incremental"),
    )

    captured: dict[str, object] = {}

    class FakeEntry:
        def __init__(self, name: str, is_dir: bool) -> None:
            self.name = name
            self.is_dir = is_dir

    class FakeBackend:
        """@brief tree 测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            captured["ensure_available"] = True

        def list_dir(self, port: str, remote_path: str):  # noqa: ANN201
            captured["port"] = port
            captured["remote_path"] = remote_path
            return [FakeEntry(name="main.py", is_dir=False)]

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(
        [
            "tree",
            "--no-interactive",
            "--port",
            "COM3",
            "--path",
            "services",
        ]
    )

    assert code == 0
    assert captured["ensure_available"] is True
    assert captured["port"] == "COM3"
    assert captured["remote_path"] == "apps/demo/services"


def test_tree_returns_failure_code_when_backend_list_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief tree 读取设备目录失败时应返回失败退出码。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="",
        sync=SyncConfig(mode="incremental"),
    )

    class FakeBackend:
        """@brief tree 失败路径测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

        def list_dir(self, port: str, remote_path: str):  # noqa: ANN201
            raise RuntimeError("boom")

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(["tree", "--no-interactive", "--port", "COM3"])

    assert code == 2


def test_tree_prints_nested_structure_in_tree_style(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:  # noqa: ANN001
    """@brief tree 输出应包含稳定的树形层级结构。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    config = AppConfig(
        serial_port="COM3",
        ignore_file=".mpyignore",
        runtime_dir=".mpy-cli",
        source_dir=".",
        mpremote_binary="mpremote",
        device_upload_dir="apps/demo",
        sync=SyncConfig(mode="incremental"),
    )

    class FakeEntry:
        def __init__(self, name: str, is_dir: bool) -> None:
            self.name = name
            self.is_dir = is_dir

    mapping = {
        "apps/demo": [
            FakeEntry(name="z.py", is_dir=False),
            FakeEntry(name="a_dir", is_dir=True),
        ],
        "apps/demo/a_dir": [FakeEntry(name="inner.py", is_dir=False)],
    }

    class FakeBackend:
        """@brief tree 树形输出测试后端。"""

        def __init__(self, binary: str = "mpremote") -> None:
            self.binary = binary

        def ensure_available(self) -> None:
            return

        def list_dir(self, port: str, remote_path: str):  # noqa: ANN201
            return mapping.get(remote_path, [])

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.MpremoteBackend", FakeBackend)

    code = main(["tree", "--no-interactive", "--port", "COM3"])

    assert code == 0
    output = capsys.readouterr().out
    assert "apps/demo" in output
    assert "├── a_dir/" in output
    assert "│   └── inner.py" in output
    assert "└── z.py" in output
