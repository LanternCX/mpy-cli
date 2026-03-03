"""Execution engine tests."""

from dataclasses import dataclass

from mpy_cli.executor import DeployExecutor
from mpy_cli.planner import DeployPlan, PlanOperation


@dataclass
class FakeBackend:
    """@brief Fake backend collecting operations for tests."""

    calls: list[tuple[str, str | None, str | None]]
    fail_wipe: bool = False

    def wipe_root(self, port: str) -> None:
        """@brief Record wipe call and optionally fail."""
        self.calls.append(("wipe", port, None))
        if self.fail_wipe:
            raise RuntimeError("wipe failed")

    def upload_file(self, port: str, local_path: str, remote_path: str) -> None:
        """@brief Record upload call."""
        self.calls.append(("upload", local_path, remote_path))

    def delete_file(self, port: str, remote_path: str) -> None:
        """@brief Record delete call."""
        self.calls.append(("delete", None, remote_path))


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
