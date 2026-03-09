"""mpremote backend adapter."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import shutil
import subprocess
from time import perf_counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol


class CommandExecutionError(RuntimeError):
    """@brief 外部命令执行失败异常。"""


class CommandTimeoutError(CommandExecutionError):
    """@brief 外部命令执行超时异常。"""


@dataclass(frozen=True)
class CommandResult:
    """@brief 命令执行结果。"""

    command: list[str]
    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True)
class RemoteDirEntry:
    """@brief 设备目录条目。"""

    name: str
    is_dir: bool


@dataclass(frozen=True)
class DetectedDevice:
    """@brief 探测到的设备信息。"""

    port: str
    implementation: str
    version: str
    platform: str
    machine: str


class BackendLogger(Protocol):
    """@brief 后端日志接口。"""

    def info(self, message: str, *args) -> None:  # noqa: ANN401
        """@brief 输出 info 日志。"""

    def warning(self, message: str, *args) -> None:  # noqa: ANN401
        """@brief 输出 warning 日志。"""


DEFAULT_LIST_WORKERS = 8
DEFAULT_PROBE_TIMEOUT = 1.0
MAX_LIST_WORKERS = 32


class MpremoteBackend:
    """@brief `mpremote` 后端适配器。"""

    def __init__(
        self,
        binary: str = "mpremote",
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        resolver: Callable[[str], str | None] = shutil.which,
        logger: BackendLogger | None = None,
    ) -> None:
        """@brief 初始化后端。

        @param binary mpremote 可执行文件名。
        @param runner 子进程执行器。
        @param resolver 可执行文件探测器。
        @param logger 可选日志器。
        """

        self.binary = binary
        self._runner = runner
        self._resolver = resolver
        self.logger = logger

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

    def build_list_dir_command(self, port: str, remote: str) -> list[str]:
        """@brief 构建设备目录读取命令。"""

        script = _build_remote_list_dir_script(remote)
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

    def list_devices(
        self,
        ports: list[str] | None = None,
        workers: int = DEFAULT_LIST_WORKERS,
        probe_timeout: float = DEFAULT_PROBE_TIMEOUT,
    ) -> list[DetectedDevice]:
        """@brief 探测当前可访问的 MicroPython 设备列表。"""

        candidate_ports = _normalize_probe_ports(
            self.list_ports() if ports is None else ports
        )
        if not candidate_ports:
            self._log_info("未扫描到可探测端口")
            return []

        normalized_workers = _normalize_list_workers(
            workers=workers,
            port_count=len(candidate_ports),
        )
        normalized_timeout = _normalize_probe_timeout(probe_timeout)
        started_at = perf_counter()
        self._log_info(
            "开始探测设备端口: count=%s workers=%s timeout=%.1fs",
            len(candidate_ports),
            normalized_workers,
            normalized_timeout,
        )

        results: dict[int, DetectedDevice] = {}
        futures: dict[Future[tuple[DetectedDevice, float]], tuple[int, str]] = {}
        with ThreadPoolExecutor(max_workers=normalized_workers) as executor:
            for index, port in enumerate(candidate_ports):
                self._log_info("开始探测端口: %s", port)
                future = executor.submit(
                    self._probe_device_timed, port, normalized_timeout
                )
                futures[future] = (index, port)

            for future in as_completed(futures):
                index, port = futures[future]
                try:
                    device, elapsed = future.result()
                except CommandTimeoutError as exc:
                    self._log_warning("探测超时: %s | %s", port, str(exc))
                except (CommandExecutionError, ValueError) as exc:
                    self._log_warning("探测失败: %s | %s", port, str(exc))
                else:
                    results[index] = device
                    self._log_info("探测完成: %s | %.3fs", port, elapsed)

        devices = [results[index] for index in sorted(results)]
        self._log_info(
            "设备探测完成: total=%s success=%s failure=%s elapsed=%.3fs",
            len(candidate_ports),
            len(devices),
            len(candidate_ports) - len(devices),
            perf_counter() - started_at,
        )
        return devices

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

    def list_dir(self, port: str, remote_path: str) -> list[RemoteDirEntry]:
        """@brief 读取设备端单层目录条目。"""

        cmd = self.build_list_dir_command(port=port, remote=remote_path)
        result = self._run(cmd)
        return parse_remote_dir_list_output(result.stdout)

    def _probe_device(self, port: str, timeout: float | None = None) -> DetectedDevice:
        """@brief 探测单个端口对应的设备信息。"""

        cmd = self._build_probe_device_command(port)
        result = self._run(cmd, timeout=timeout)
        return parse_device_probe_output(port=port, output=result.stdout)

    def _probe_device_timed(
        self,
        port: str,
        timeout: float,
    ) -> tuple[DetectedDevice, float]:
        """@brief 以耗时统计方式探测单个端口。"""

        started_at = perf_counter()
        device = self._probe_device(port=port, timeout=timeout)
        return device, perf_counter() - started_at

    def _build_probe_device_command(self, port: str) -> list[str]:
        """@brief 构建设备探测命令。"""

        script = _build_probe_device_script()
        return [self.binary, "connect", port, "resume", "exec", script]

    def _run(self, command: list[str], timeout: float | None = None) -> CommandResult:
        """@brief 执行外部命令。"""

        kwargs = {"capture_output": True, "text": True, "check": False}
        if timeout is not None:
            kwargs["timeout"] = timeout

        try:
            completed = self._runner(command, **kwargs)
        except subprocess.TimeoutExpired as exc:
            raise CommandTimeoutError(f"命令执行超时: {exc.timeout:.1f}s") from exc

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

    def _log_info(self, message: str, *args) -> None:  # noqa: ANN401
        """@brief 输出 info 日志。"""

        if self.logger is None:
            return
        self.logger.info(message, *args)

    def _log_warning(self, message: str, *args) -> None:  # noqa: ANN401
        """@brief 输出 warning 日志。"""

        if self.logger is None:
            return
        self.logger.warning(message, *args)

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


def parse_device_probe_output(port: str, output: str) -> DetectedDevice:
    """@brief 解析设备探测输出。"""

    values: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        cleaned_key = key.strip()
        cleaned_value = value.strip()
        if cleaned_key:
            values[cleaned_key] = cleaned_value

    implementation = values.get("I", "")
    if not implementation:
        raise ValueError(f"missing implementation for port {port}")

    platform = values.get("P", "")
    machine = values.get("M", "") or platform
    return DetectedDevice(
        port=port,
        implementation=implementation,
        version=values.get("V", ""),
        platform=platform,
        machine=machine,
    )


def _normalize_list_workers(workers: int, port_count: int) -> int:
    """@brief 归一化 list 探测线程数。"""

    if port_count <= 0:
        return 1
    return max(1, min(workers, port_count, MAX_LIST_WORKERS))


def _normalize_probe_timeout(probe_timeout: float) -> float:
    """@brief 归一化探测超时秒数。"""

    if probe_timeout <= 0:
        raise ValueError("probe timeout must be positive")
    return probe_timeout


def _normalize_probe_ports(ports: list[str]) -> list[str]:
    """@brief 去重并归一化待探测端口列表。"""

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_port in ports:
        port = raw_port.strip()
        if not port or port in seen:
            continue
        seen.add(port)
        normalized.append(port)
    return normalized


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


def _build_probe_device_script() -> str:
    """@brief 生成设备探测脚本片段。"""

    return (
        "import os\n"
        "import sys\n"
        "implementation = getattr(getattr(sys, 'implementation', None), 'name', '')\n"
        "version_info = getattr(getattr(sys, 'implementation', None), 'version', ())\n"
        "version = '.'.join(str(part) for part in version_info[:3])\n"
        "platform = getattr(sys, 'platform', '')\n"
        "machine = platform\n"
        "try:\n"
        "    machine = os.uname().machine\n"
        "except Exception:\n"
        "    machine = platform\n"
        "print('I\\t' + str(implementation))\n"
        "print('V\\t' + str(version))\n"
        "print('P\\t' + str(platform))\n"
        "print('M\\t' + str(machine))\n"
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


def _build_remote_list_dir_script(remote_path: str) -> str:
    """@brief 生成设备端目录单层读取片段。"""

    normalized_remote_path = _normalize_remote_file(remote_path)
    return (
        f"target_raw = {normalized_remote_path!r}\n"
        "import os\n"
        "roots = []\n"
        "try:\n"
        "    roots = os.listdir('/')\n"
        "except OSError:\n"
        "    roots = []\n"
        "candidates = []\n"
        "if not target_raw:\n"
        "    if 'flash' in roots:\n"
        "        candidates.append('/flash')\n"
        "    candidates.append('/')\n"
        "elif target_raw.startswith('/'):\n"
        "    candidates.append(target_raw)\n"
        "else:\n"
        "    candidates.append('/' + target_raw)\n"
        "    if 'flash' in roots:\n"
        "        candidates.append('/flash/' + target_raw)\n"
        "resolved = None\n"
        "names = []\n"
        "for candidate in candidates:\n"
        "    try:\n"
        "        names = os.listdir(candidate)\n"
        "        resolved = candidate\n"
        "        break\n"
        "    except OSError:\n"
        "        pass\n"
        "if resolved is None:\n"
        "    raise OSError('target path not found: ' + target_raw)\n"
        "try:\n"
        "    names.sort()\n"
        "except Exception:\n"
        "    pass\n"
        "for name in names:\n"
        "    current = resolved + '/' + name if resolved != '/' else '/' + name\n"
        "    try:\n"
        "        os.listdir(current)\n"
        "        print('D\\t' + name)\n"
        "    except OSError:\n"
        "        print('F\\t' + name)\n"
    )


def parse_remote_dir_list_output(output: str) -> list[RemoteDirEntry]:
    """@brief 解析设备目录读取输出。"""

    entries: list[RemoteDirEntry] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "\t" not in line:
            continue
        kind, name = line.split("\t", 1)
        cleaned_name = name.strip()
        if not cleaned_name:
            continue
        if kind not in {"D", "F"}:
            continue
        entries.append(RemoteDirEntry(name=cleaned_name, is_dir=(kind == "D")))
    return entries
