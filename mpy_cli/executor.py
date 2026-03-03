"""Deployment plan executor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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


class ExecutorLogger(Protocol):
    """@brief 执行器日志接口。"""

    def info(self, message: str, *args) -> None:  # noqa: ANN401
        """@brief 输出 info 日志。"""

    def error(self, message: str, *args) -> None:  # noqa: ANN401
        """@brief 输出 error 日志。"""


class DeployExecutor:
    """@brief 部署执行器。"""

    def __init__(self, backend: object, logger: ExecutorLogger | None = None) -> None:
        """@brief 初始化执行器。

        @param backend 设备后端对象，需实现 wipe/upload/delete 接口。
        @param logger 可选日志器。
        """

        self.backend = backend
        self.logger = logger

    def execute(self, plan: DeployPlan, port: str) -> ExecutionReport:
        """@brief 执行部署计划。"""

        success_count = 0
        failures: list[ExecutionFailure] = []
        total = len(plan.operations)

        for index, operation in enumerate(plan.operations, start=1):
            self._log_start(index=index, total=total, operation=operation)
            try:
                self._apply_operation(operation=operation, port=port)
                success_count += 1
                self._log_success(index=index, total=total, operation=operation)
            except Exception as exc:  # noqa: BLE001
                failures.append(ExecutionFailure(operation=operation, error=str(exc)))
                self._log_failure(
                    index=index, total=total, operation=operation, error=exc
                )
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

    def _log_start(self, index: int, total: int, operation: PlanOperation) -> None:
        """@brief 记录操作开始日志。"""

        if self.logger is None:
            return
        self.logger.info(
            "开始%s [%s/%s]: %s",
            self._verb(operation),
            index,
            total,
            self._target(operation),
        )

    def _log_success(self, index: int, total: int, operation: PlanOperation) -> None:
        """@brief 记录操作成功日志。"""

        if self.logger is None:
            return
        self.logger.info(
            "完成%s [%s/%s]: %s",
            self._verb(operation),
            index,
            total,
            self._target(operation),
        )

    def _log_failure(
        self,
        index: int,
        total: int,
        operation: PlanOperation,
        error: Exception,
    ) -> None:
        """@brief 记录操作失败日志。"""

        if self.logger is None:
            return
        self.logger.error(
            "%s失败 [%s/%s]: %s | %s",
            self._verb(operation),
            index,
            total,
            self._target(operation),
            str(error),
        )

    def _verb(self, operation: PlanOperation) -> str:
        """@brief 返回操作动词。"""

        if operation.op_type == "upload":
            return "上传"
        if operation.op_type == "delete":
            return "删除"
        if operation.op_type == "wipe":
            return "擦除"
        return operation.op_type

    def _target(self, operation: PlanOperation) -> str:
        """@brief 返回操作目标描述。"""

        if operation.op_type == "upload":
            return f"{operation.local_path} -> :{operation.remote_path}"
        if operation.op_type == "delete":
            return f":{operation.remote_path}"
        if operation.op_type == "wipe":
            return "设备文件系统"
        return operation.reason
