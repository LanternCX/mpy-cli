"""Deployment plan executor."""

from __future__ import annotations

from dataclasses import dataclass

from mpy_cli.planner import DeployPlan, PlanOperation


@dataclass(frozen=True)
class ExecutionFailure:
    """@brief 执行失败记录。"""

    operation: PlanOperation
    error: str


@dataclass(frozen=True)
class ExecutionReport:
    """@brief 执行结果统计。"""

    success_count: int
    failure_count: int
    failures: list[ExecutionFailure]


class DeployExecutor:
    """@brief 部署执行器。"""

    def __init__(self, backend: object) -> None:
        """@brief 初始化执行器。

        @param backend 设备后端对象，需实现 wipe/upload/delete 接口。
        """

        self.backend = backend

    def execute(self, plan: DeployPlan, port: str) -> ExecutionReport:
        """@brief 执行部署计划。"""

        success_count = 0
        failures: list[ExecutionFailure] = []

        for operation in plan.operations:
            try:
                self._apply_operation(operation=operation, port=port)
                success_count += 1
            except Exception as exc:  # noqa: BLE001
                failures.append(ExecutionFailure(operation=operation, error=str(exc)))
                if operation.op_type == "wipe":
                    break

        return ExecutionReport(
            success_count=success_count,
            failure_count=len(failures),
            failures=failures,
        )

    def _apply_operation(self, operation: PlanOperation, port: str) -> None:
        """@brief 分发单条操作到后端。"""

        if operation.op_type == "wipe":
            self.backend.wipe_root(port)
            return

        if operation.op_type == "upload":
            if operation.local_path is None or operation.remote_path is None:
                raise ValueError("upload 操作缺少路径参数")
            self.backend.upload_file(port, operation.local_path, operation.remote_path)
            return

        if operation.op_type == "delete":
            if operation.remote_path is None:
                raise ValueError("delete 操作缺少远端路径")
            self.backend.delete_file(port, operation.remote_path)
            return

        raise ValueError(f"未知操作类型: {operation.op_type}")
