# run 命令功能设计文档

## 背景

当前 `mpy-cli` 已支持 `plan/deploy/upload`，但缺少“直接执行设备端已存在脚本”的入口。
在调试场景中，用户经常希望指定设备目标目录下的某个文件直接运行，而不触发上传流程。

## 目标

- 新增 `mpy-cli run` 子命令。
- 支持通过 `--path` 指定设备端目标文件。
- `--path` 语义为相对 `device_upload_dir`，与现有 `upload --remote` 规则一致。
- 复用现有端口解析与执行前确认体验。

## 非目标

- 不在本次支持“先上传再执行”。
- 不新增批量执行、多文件通配等能力。
- 不改动 `plan/deploy/upload` 现有语义。

## 命令设计

```bash
mpy-cli run [--path PATH] [--port PORT] [--no-interactive] [--yes]
```

- `--path`：设备目标文件路径（相对 `device_upload_dir`）。
- `--port`：设备串口。
- `--no-interactive`：禁用交互提问；缺少 `--path` 时直接报错。
- `--yes`：跳过执行前确认。

## 交互流程

1. 加载配置并解析端口（沿用现有优先级：`--port` > 配置 > 扫描/手输）。
2. 解析 `--path`：
   - 有值：直接使用。
   - 无值且交互模式：提示输入。
   - 无值且非交互：报错退出。
3. 计算最终设备路径：`device_upload_dir + path`。
4. 打印执行预览并确认（`--yes` 可跳过）。
5. 执行设备端脚本并输出结果。

## 执行架构

- `mpy_cli/cli.py`
  - 新增 `run` 子命令解析与 `_cmd_run` 流程。
  - 复用 `_resolve_port()` 与 `_join_upload_target()`。
- `mpy_cli/backend/mpremote.py`
  - 新增 `build_run_command()` 与 `run_file()`。
  - 通过 `mpremote connect <port> resume exec <script>` 在设备端执行目标文件。

## 设备端脚本语义

- 优先尝试用户给定路径。
- 若设备存在 `/flash`，额外尝试 `/flash/<path>` 兜底。
- 使用 `open + compile + exec` 执行脚本，并设置：
  - `__name__ = "__main__"`
  - `__file__ = <resolved path>`

## 错误处理与返回码

- 参数缺失、配置错误、端口缺失、用户取消：返回 `1`。
- 设备执行失败（文件不存在、运行时报错、命令失败）：返回 `2`。
- 执行成功：返回 `0`。

## 测试策略

- `tests/test_cli.py`
  - `run` 非交互缺少 `--path` 报错。
  - 交互模式支持输入 `--path`。
  - `--path` 会按 `device_upload_dir` 拼接。
  - 执行失败返回 `2`，成功返回 `0`。
- `tests/test_mpremote_backend.py`
  - `build_run_command()` 命令拼装正确。
  - `run_file()` 调用正确命令。
- `tests/test_docs_and_ci.py`
  - README 包含 `mpy-cli run` 与 `--path`。

## 验收标准

- 用户可以执行 `mpy-cli run --path <target.py>`。
- 当配置 `device_upload_dir` 时，`--path` 作为相对路径拼接执行。
- 有清晰预览与确认，`--yes` 可跳过。
- 新增测试通过，且不影响现有功能。
