"""CLI command tests."""

from dataclasses import dataclass
from pathlib import Path

from mpy_cli.config import AppConfig, SyncConfig
from mpy_cli.cli import _resolve_port, main
from mpy_cli.executor import ExecutionReport
from mpy_cli.gitdiff import ChangeEntry


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

    def fake_collect_git_changes(repo_path: Path) -> list[ChangeEntry]:
        captured_repo_path["value"] = repo_path
        return []

    monkeypatch.setattr("mpy_cli.cli.load_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr("mpy_cli.cli.collect_git_changes", fake_collect_git_changes)

    code = main(["plan", "--no-interactive", "--mode", "incremental", "--port", "COM3"])

    assert code == 0
    assert captured_repo_path["value"] == source_root.resolve()


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

    def fake_collect_git_changes(_repo_path: Path) -> list[ChangeEntry]:
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
