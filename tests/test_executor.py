"""Execution engine tests."""

from dataclasses import dataclass

from mpy_cli.executor import DeployExecutor
from mpy_cli.planner import DeployPlan, PlanOperation


@dataclass
class FakeBackend:
    """@brief Fake backend collecting operations for tests."""

    calls: list[tuple[str, str | None, str | None]]
    fail_wipe: bool = False

    def wipe_root(self, port: str, target_dir: str | None = None) -> None:
        """@brief Record wipe call and optionally fail."""
        self.calls.append(("wipe", port, target_dir))
        if self.fail_wipe:
            raise RuntimeError("wipe failed")

    def upload_file(self, port: str, local_path: str, remote_path: str) -> None:
        """@brief Record upload call."""
        self.calls.append(("upload", local_path, remote_path))

    def delete_file(self, port: str, remote_path: str) -> None:
        """@brief Record delete call."""
        self.calls.append(("delete", None, remote_path))


@dataclass
class FakeLogger:
    """@brief 简单日志收集器。"""

    info_messages: list[str]
    error_messages: list[str]

    def info(self, message: str, *args) -> None:  # noqa: ANN001
        """@brief 收集 info 日志。"""

        self.info_messages.append(message % args if args else message)

    def error(self, message: str, *args) -> None:  # noqa: ANN001
        """@brief 收集 error 日志。"""

        self.error_messages.append(message % args if args else message)


def test_executor_stops_after_wipe_failure() -> None:
    """@brief Wipe failure should abort subsequent operations."""
    backend = FakeBackend(calls=[], fail_wipe=True)
    executor = DeployExecutor(backend=backend)
    plan = DeployPlan(
        mode="full",
        operations=[
            PlanOperation(
                op_type="wipe", local_path=None, remote_path=None, reason="full"
            ),
            PlanOperation(
                op_type="upload",
                local_path="main.py",
                remote_path="main.py",
                reason="full",
            ),
        ],
    )

    report = executor.execute(plan=plan, port="/dev/ttyACM0")

    assert report.success_count == 0
    assert report.failure_count == 1
    assert len(backend.calls) == 1


def test_executor_logs_progress_for_each_operation() -> None:
    """@brief 执行器应记录逐操作日志，包含单文件上传信息。"""

    backend = FakeBackend(calls=[])
    logger = FakeLogger(info_messages=[], error_messages=[])
    executor = DeployExecutor(backend=backend, logger=logger)
    plan = DeployPlan(
        mode="full",
        operations=[
            PlanOperation(
                op_type="wipe", local_path=None, remote_path=None, reason="full"
            ),
            PlanOperation(
                op_type="upload",
                local_path="main.py",
                remote_path="main.py",
                reason="full",
            ),
            PlanOperation(
                op_type="delete", local_path=None, remote_path="old.py", reason="full"
            ),
        ],
    )

    report = executor.execute(plan=plan, port="/dev/ttyACM0")

    assert report.failure_count == 0
    assert any("开始上传" in msg and "main.py" in msg for msg in logger.info_messages)
    assert any("完成上传" in msg and "main.py" in msg for msg in logger.info_messages)


def test_executor_passes_wipe_target_dir_to_backend() -> None:
    """@brief wipe 操作应将计划中的目标目录传给后端。"""

    backend = FakeBackend(calls=[])
    executor = DeployExecutor(backend=backend)
    plan = DeployPlan(
        mode="full",
        operations=[
            PlanOperation(
                op_type="wipe",
                local_path=None,
                remote_path="apps/demo",
                reason="full",
            )
        ],
    )

    report = executor.execute(plan=plan, port="/dev/ttyACM0")

    assert report.failure_count == 0
    assert backend.calls == [("wipe", "/dev/ttyACM0", "apps/demo")]
