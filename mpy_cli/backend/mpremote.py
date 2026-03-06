"""mpremote backend adapter."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class CommandExecutionError(RuntimeError):
    """@brief 外部命令执行失败异常。"""


@dataclass(frozen=True)
class CommandResult:
    """@brief 命令执行结果。"""

    command: list[str]
    stdout: str
    stderr: str
    returncode: int


class MpremoteBackend:
    """@brief `mpremote` 后端适配器。"""

    def __init__(
        self,
        binary: str = "mpremote",
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        resolver: Callable[[str], str | None] = shutil.which,
    ) -> None:
        """@brief 初始化后端。

        @param binary mpremote 可执行文件名。
        @param runner 子进程执行器。
        @param resolver 可执行文件探测器。
        """

        self.binary = binary
        self._runner = runner
        self._resolver = resolver

    def ensure_available(self) -> None:
        """@brief 确保 mpremote 可执行文件存在。"""

        if self._resolver(self.binary) is None:
            raise CommandExecutionError(
                f"未找到 `{self.binary}`，请先安装 mpremote（例如: pip install mpremote）"
            )

    def build_upload_command(self, port: str, local: Path, remote: str) -> list[str]:
        """@brief 构建上传命令。"""

        return [
            self.binary,
            "connect",
            port,
            "resume",
            "fs",
            "cp",
            local.as_posix(),
            f":{remote}",
        ]

    def build_delete_command(self, port: str, remote: str) -> list[str]:
        """@brief 构建设备删除命令。"""

        return [
            self.binary,
            "connect",
            port,
            "resume",
            "fs",
            "rm",
            f":{remote}",
        ]

    def build_delete_tree_command(self, port: str, remote: str) -> list[str]:
        """@brief 构建设备递归删除命令。"""

        script = _build_remote_delete_script(remote)
        return [self.binary, "connect", port, "resume", "exec", script]

    def build_run_command(self, port: str, remote: str) -> list[str]:
        """@brief 构建设备脚本执行命令。"""

        script = _build_remote_run_script(remote)
        return [self.binary, "connect", port, "resume", "exec", script]

    def build_wipe_command(self, port: str, target_dir: str | None = None) -> list[str]:
        """@brief 构建设备目录清空命令。"""

        normalized_target_dir = _normalize_remote_dir(target_dir)

        wipe_script = (
            f"target_raw = {normalized_target_dir!r}\n"
            "import os\n"
            "def _clean(path):\n"
            "    for name in os.listdir(path):\n"
            "        current = path + '/' + name if path != '/' else '/' + name\n"
            "        try:\n"
            "            _clean(current)\n"
            "            os.rmdir(current)\n"
            "        except OSError:\n"
            "            try:\n"
            "                os.remove(current)\n"
            "            except OSError:\n"
            "                pass\n"
            "roots = []\n"
            "try:\n"
            "    roots = os.listdir('/')\n"
            "except OSError:\n"
            "    roots = []\n"
            "if target_raw:\n"
            "    if target_raw.startswith('/'):\n"
            "        target = target_raw\n"
            "    elif 'flash' in roots:\n"
            "        target = '/flash/' + target_raw\n"
            "    else:\n"
            "        target = '/' + target_raw\n"
            "    try:\n"
            "        _clean(target)\n"
            "    except OSError:\n"
            "        pass\n"
            "elif 'flash' in roots:\n"
            "    _clean('/flash')\n"
            "else:\n"
            "    _clean('/')\n"
        )
        return [self.binary, "connect", port, "resume", "exec", wipe_script]

    def list_ports(self) -> list[str]:
        """@brief 列出可用设备端口。"""

        result = self._run([self.binary, "connect", "list"])
        return parse_port_list_output(result.stdout)

    def upload_file(
        self, port: str, local_path: str, remote_path: str
    ) -> CommandResult:
        """@brief 上传文件到设备。"""

        self._ensure_remote_parent_dirs(port=port, remote_path=remote_path)

        cmd = self.build_upload_command(
            port=port, local=Path(local_path), remote=remote_path
        )
        return self._run(cmd)

    def delete_file(self, port: str, remote_path: str) -> CommandResult:
        """@brief 删除设备文件。"""

        cmd = self.build_delete_command(port=port, remote=remote_path)
        return self._run(cmd)

    def delete_path(self, port: str, remote_path: str) -> CommandResult:
        """@brief 删除设备路径（文件或目录）。"""

        cmd = self.build_delete_tree_command(port=port, remote=remote_path)
        return self._run(cmd)

    def wipe_root(self, port: str, target_dir: str | None = None) -> CommandResult:
        """@brief 清空设备目标目录文件。"""

        cmd = self.build_wipe_command(port=port, target_dir=target_dir)
        return self._run(cmd)

    def run_file(self, port: str, remote_path: str) -> CommandResult:
        """@brief 执行设备端目标脚本文件。"""

        cmd = self.build_run_command(port=port, remote=remote_path)
        return self._run(cmd)

    def _run(self, command: list[str]) -> CommandResult:
        """@brief 执行外部命令。"""

        completed = self._runner(command, capture_output=True, text=True, check=False)
        result = CommandResult(
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )

        if completed.returncode != 0:
            message = (
                completed.stderr.strip() or completed.stdout.strip() or "命令执行失败"
            )
            raise CommandExecutionError(message)
        return result

    def _ensure_remote_parent_dirs(self, port: str, remote_path: str) -> None:
        """@brief 确保远端父目录存在。"""

        parts = [part for part in remote_path.split("/")[:-1] if part]
        if not parts:
            return

        current: list[str] = []
        for part in parts:
            current.append(part)
            target = "/".join(current)
            command = [
                self.binary,
                "connect",
                port,
                "resume",
                "fs",
                "mkdir",
                f":{target}",
            ]
            self._run_allow_file_exists(command)

    def _run_allow_file_exists(self, command: list[str]) -> CommandResult:
        """@brief 执行命令并忽略目录已存在错误。"""

        completed = self._runner(command, capture_output=True, text=True, check=False)
        result = CommandResult(
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )

        if completed.returncode == 0:
            return result

        message = completed.stderr.strip() or completed.stdout.strip() or "命令执行失败"
        if "File exists" in message:
            return result
        raise CommandExecutionError(message)


def parse_port_list_output(output: str) -> list[str]:
    """@brief 解析 `mpremote connect list` 输出。"""

    ports: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        token = line.split()[0].rstrip(":")
        if not _looks_like_port(token):
            continue
        if token not in ports:
            ports.append(token)
    return ports


def _looks_like_port(token: str) -> bool:
    """@brief 判断 token 是否像设备端口。"""

    upper = token.upper()
    return (
        token.startswith("/dev/") or token.startswith("tty") or upper.startswith("COM")
    )


def _normalize_remote_dir(target_dir: str | None) -> str:
    """@brief 归一化设备目录路径，保留绝对路径语义。"""

    if target_dir is None:
        return ""

    raw = target_dir.strip().replace("\\", "/")
    if raw in {"", ".", "/"}:
        return ""

    is_absolute = raw.startswith("/")
    parts = [part for part in raw.split("/") if part and part != "."]
    if not parts:
        return ""

    normalized = "/".join(parts)
    if is_absolute:
        return f"/{normalized}"
    return normalized


def _normalize_remote_file(remote_path: str) -> str:
    """@brief 归一化设备脚本路径。"""

    raw = remote_path.strip().replace("\\", "/").lstrip(":")
    if raw in {"", ".", "/"}:
        return ""

    is_absolute = raw.startswith("/")
    parts = [part for part in raw.split("/") if part and part != "."]
    if not parts:
        return ""

    normalized = "/".join(parts)
    if is_absolute:
        return f"/{normalized}"
    return normalized


def _build_remote_run_script(remote_path: str) -> str:
    """@brief 生成设备端脚本执行片段。"""

    normalized_remote_path = _normalize_remote_file(remote_path)
    return (
        f"target_raw = {normalized_remote_path!r}\n"
        "import os\n"
        "if not target_raw:\n"
        "    raise OSError('empty target path')\n"
        "roots = []\n"
        "try:\n"
        "    roots = os.listdir('/')\n"
        "except OSError:\n"
        "    roots = []\n"
        "candidates = []\n"
        "if target_raw.startswith('/'):\n"
        "    candidates.append(target_raw)\n"
        "else:\n"
        "    candidates.append('/' + target_raw)\n"
        "    if 'flash' in roots:\n"
        "        candidates.append('/flash/' + target_raw)\n"
        "resolved = None\n"
        "for candidate in candidates:\n"
        "    try:\n"
        "        with open(candidate, 'r') as f:\n"
        "            source = f.read()\n"
        "        resolved = candidate\n"
        "        break\n"
        "    except OSError:\n"
        "        pass\n"
        "if resolved is None:\n"
        "    raise OSError('target file not found: ' + target_raw)\n"
        "globals_dict = {'__name__': '__main__', '__file__': resolved}\n"
        "exec(compile(source, resolved, 'exec'), globals_dict, globals_dict)\n"
    )


def _build_remote_delete_script(remote_path: str) -> str:
    """@brief 生成设备端删除片段。"""

    normalized_remote_path = _normalize_remote_file(remote_path)
    return (
        f"target_raw = {normalized_remote_path!r}\n"
        "import os\n"
        "if not target_raw:\n"
        "    raise OSError('empty target path')\n"
        "roots = []\n"
        "try:\n"
        "    roots = os.listdir('/')\n"
        "except OSError:\n"
        "    roots = []\n"
        "candidates = []\n"
        "if target_raw.startswith('/'):\n"
        "    candidates.append(target_raw)\n"
        "else:\n"
        "    candidates.append('/' + target_raw)\n"
        "    if 'flash' in roots:\n"
        "        candidates.append('/flash/' + target_raw)\n"
        "protected_dirs = {'/', '/flash'}\n"
        "def _remove_tree(path):\n"
        "    try:\n"
        "        names = os.listdir(path)\n"
        "    except OSError:\n"
        "        os.remove(path)\n"
        "        return\n"
        "    for name in names:\n"
        "        child = path + '/' + name if path != '/' else '/' + name\n"
        "        _remove_tree(child)\n"
        "    if path in protected_dirs:\n"
        "        return\n"
        "    os.rmdir(path)\n"
        "resolved = None\n"
        "for candidate in candidates:\n"
        "    try:\n"
        "        _remove_tree(candidate)\n"
        "        resolved = candidate\n"
        "        break\n"
        "    except OSError:\n"
        "        pass\n"
        "if resolved is None:\n"
        "    raise OSError('target path not found: ' + target_raw)\n"
    )
