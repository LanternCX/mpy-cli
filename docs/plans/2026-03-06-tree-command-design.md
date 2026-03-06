# tree 命令功能设计文档

## 背景

当前 `mpy-cli` 已支持 `upload/run/delete`，但缺少“查看设备端目录结构”的能力。用户在部署前后无法快速确认设备上的目录层级，尤其在设置了 `device_upload_dir` 后，不容易判断目标目录是否符合预期。

## 目标

- 新增 `mpy-cli tree` 子命令。
- 默认读取设备端 `device_upload_dir` 对应目录树。
- 支持通过 `--path` 指定相对 `device_upload_dir` 的子目录。
- 输出采用类似 `tree` 的文本结构，便于快速阅读。

## 命令设计

```bash
mpy-cli tree [--path PATH] [--port PORT] [--no-interactive]
```

- `--path`：设备目标目录，语义为相对 `device_upload_dir`；为空时读取 `device_upload_dir` 根。
- `--port`：指定设备串口。
- `--no-interactive`：禁用交互提问；无 `--port` 时按既有规则处理。

## 方案对比

### 方案 A（推荐）主机递归 + 设备单层目录读取

- 每次请求设备一个目录的直接子项（文件/目录），主机侧递归构建树并打印。
- 优点：结构清晰，错误定位直接，便于测试。
- 缺点：深层目录会产生多次设备往返。

### 方案 B 设备端一次性递归回传

- 在设备端执行完整递归脚本，直接输出最终树文本。
- 优点：设备往返少。
- 缺点：设备脚本复杂，兼容性与可测试性较差。

最终采用方案 A。

## 架构与数据流

1. CLI 解析 `tree` 子命令参数。
2. 复用 `_resolve_port()` 解析端口。
3. 按 `device_upload_dir` + `--path` 计算目标设备目录。
4. `MpremoteBackend` 提供“单层目录读取”能力，返回结构化条目（名称 + 是否目录）。
5. CLI 递归请求并生成树形文本输出。

## 错误处理

- 配置错误、端口缺失、`mpremote` 不可用：返回 `1`。
- 目录读取失败（目录不存在、权限问题、设备异常）：返回 `2`。

## 测试策略

- `tests/test_mpremote_backend.py`
  - 校验目录读取命令构建。
  - 校验目录读取输出解析（`D\tname` / `F\tname`）。
- `tests/test_cli.py`
  - 校验 `tree` 命令在 `device_upload_dir` 语义下拼接目标路径。
  - 校验 `tree` 读取失败时返回退出码 `2`。
- `tests/test_docs_and_ci.py` + `README.md`
  - 保持命令列表和参数说明同步。

## 验收标准

- 可执行 `mpy-cli tree --path <dir>` 查看设备目录树。
- 未传 `--path` 时默认查看 `device_upload_dir` 根目录。
- 输出有稳定树结构，目录优先排序。
- 新增测试通过，不影响现有命令行为。
