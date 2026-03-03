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
            "fs",
            "cp",
            local.as_posix(),
            f":{remote}",
        ]

    def build_delete_command(self, port: str, remote: str) -> list[str]:
        """@brief 构建设备删除命令。"""

        return [self.binary, "connect", port, "fs", "rm", f":{remote}"]

    def build_wipe_command(self, port: str) -> list[str]:
        """@brief 构建设备根目录清空命令。"""

        wipe_script = (
            "import os\n"
            "def _rm(path):\n"
            "    for name in os.listdir(path):\n"
            "        current = path + '/' + name if path != '/' else '/' + name\n"
            "        try:\n"
            "            _rm(current)\n"
            "            os.rmdir(current)\n"
            "        except OSError:\n"
            "            os.remove(current)\n"
            "_rm('/')\n"
        )
        return [self.binary, "connect", port, "exec", wipe_script]

    def upload_file(
        self, port: str, local_path: str, remote_path: str
    ) -> CommandResult:
        """@brief 上传文件到设备。"""

        cmd = self.build_upload_command(
            port=port, local=Path(local_path), remote=remote_path
        )
        return self._run(cmd)

    def delete_file(self, port: str, remote_path: str) -> CommandResult:
        """@brief 删除设备文件。"""

        cmd = self.build_delete_command(port=port, remote=remote_path)
        return self._run(cmd)

    def wipe_root(self, port: str) -> CommandResult:
        """@brief 清空设备根目录文件。"""

        cmd = self.build_wipe_command(port=port)
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
