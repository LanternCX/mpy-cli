"""mpremote backend tests."""

import subprocess
from pathlib import Path

from mpy_cli.backend.mpremote import MpremoteBackend, parse_port_list_output


def test_upload_builds_expected_command() -> None:
    """@brief Upload command should match mpremote fs cp syntax."""
    backend = MpremoteBackend(binary="mpremote")

    cmd = backend.build_upload_command(
        port="/dev/ttyACM0",
        local=Path("main.py"),
        remote="main.py",
    )

    assert cmd == [
        "mpremote",
        "connect",
        "/dev/ttyACM0",
        "resume",
        "fs",
        "cp",
        "main.py",
        ":main.py",
    ]


def test_delete_builds_expected_command() -> None:
    """@brief Delete command should target remote path."""
    backend = MpremoteBackend(binary="mpremote")

    cmd = backend.build_delete_command(port="/dev/ttyACM0", remote="obsolete.py")

    assert cmd == [
        "mpremote",
        "connect",
        "/dev/ttyACM0",
        "resume",
        "fs",
        "rm",
        ":obsolete.py",
    ]


def test_run_builds_expected_command() -> None:
    """@brief run 命令应构建为 mpremote resume exec 调用。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_run_command(
        port="/dev/ttyACM0",
        remote="apps/demo/main.py",
    )

    assert cmd[0:4] == ["mpremote", "connect", "/dev/ttyACM0", "resume"]
    assert cmd[4] == "exec"
    assert "apps/demo/main.py" in cmd[5]


def test_run_file_invokes_exec_command() -> None:
    """@brief run_file 应调用 exec 命令执行目标脚本。"""

    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok\n",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    backend.run_file(port="/dev/ttyACM0", remote_path="apps/demo/main.py")

    assert called
    assert called[0][0:5] == ["mpremote", "connect", "/dev/ttyACM0", "resume", "exec"]


def test_delete_tree_builds_expected_command() -> None:
    """@brief delete 命令应构建为 mpremote resume exec 调用。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_delete_tree_command(
        port="/dev/ttyACM0",
        remote="apps/demo",
    )

    assert cmd[0:4] == ["mpremote", "connect", "/dev/ttyACM0", "resume"]
    assert cmd[4] == "exec"
    assert "apps/demo" in cmd[5]


def test_delete_path_invokes_exec_command() -> None:
    """@brief delete_path 应调用 exec 命令执行删除。"""

    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    backend.delete_path(port="/dev/ttyACM0", remote_path="apps/demo")

    assert called
    assert called[0][0:5] == ["mpremote", "connect", "/dev/ttyACM0", "resume", "exec"]


def test_wipe_builds_expected_command_with_resume() -> None:
    """@brief wipe 命令应通过 resume 模式进入执行。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_wipe_command(port="/dev/ttyACM0")

    assert cmd[0:4] == ["mpremote", "connect", "/dev/ttyACM0", "resume"]
    assert cmd[4] == "exec"


def test_wipe_script_targets_flash_contents_not_flash_mountpoint() -> None:
    """@brief wipe 脚本应清空 /flash 内容而非删除 /flash 挂载点。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_wipe_command(port="/dev/ttyACM0")

    script = cmd[5]
    assert "_clean('/flash')" in script
    assert "_rm('/')" not in script


def test_wipe_script_scopes_cleanup_to_target_dir_when_provided() -> None:
    """@brief 指定 target_dir 时应仅清空该目录。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_wipe_command(port="/dev/ttyACM0", target_dir="apps/demo")

    script = cmd[5]
    assert "target_raw = 'apps/demo'" in script
    assert "_clean(target)" in script
    assert "target = '/flash/' + target_raw" in script


def test_parse_port_list_output_extracts_known_port_tokens() -> None:
    """@brief 端口解析应提取常见串口标识并保持顺序。"""

    output = """
Available ports:
/dev/ttyACM0 USB Serial
COM3 CP210x
not-a-port line
""".strip()

    assert parse_port_list_output(output) == ["/dev/ttyACM0", "COM3"]


def test_list_ports_invokes_connect_list_command() -> None:
    """@brief list_ports 应调用 `mpremote connect list`。"""

    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="/dev/ttyACM0 USB Serial\n",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    ports = backend.list_ports()

    assert called == [["mpremote", "connect", "list"]]
    assert ports == ["/dev/ttyACM0"]


def test_upload_file_creates_remote_parent_dirs_before_copy() -> None:
    """@brief 上传嵌套路径前应先创建远端父目录。"""

    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    backend.upload_file(
        port="/dev/ttyACM0",
        local_path="/tmp/local.py",
        remote_path="services/commands/cmd.py",
    )

    assert called[0] == [
        "mpremote",
        "connect",
        "/dev/ttyACM0",
        "resume",
        "fs",
        "mkdir",
        ":services",
    ]
    assert called[1] == [
        "mpremote",
        "connect",
        "/dev/ttyACM0",
        "resume",
        "fs",
        "mkdir",
        ":services/commands",
    ]
    assert called[2][-4:] == ["fs", "cp", "/tmp/local.py", ":services/commands/cmd.py"]


def test_list_dir_builds_expected_exec_command() -> None:
    """@brief list_dir 应构建为 mpremote resume exec 调用。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_list_dir_command(
        port="/dev/ttyACM0",
        remote="apps/demo",
    )

    assert cmd[0:4] == ["mpremote", "connect", "/dev/ttyACM0", "resume"]
    assert cmd[4] == "exec"
    assert "apps/demo" in cmd[5]


def test_list_dir_parses_typed_entries() -> None:
    """@brief list_dir 应将 D/F 标记输出解析为结构化目录条目。"""

    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="D\tapps\nF\tmain.py\n",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    entries = backend.list_dir(port="/dev/ttyACM0", remote_path="apps/demo")

    assert called
    assert called[0][0:5] == ["mpremote", "connect", "/dev/ttyACM0", "resume", "exec"]
    assert [entry.name for entry in entries] == ["apps", "main.py"]
    assert [entry.is_dir for entry in entries] == [True, False]
