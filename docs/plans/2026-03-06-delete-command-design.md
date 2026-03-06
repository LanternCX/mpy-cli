# delete 命令功能设计文档

## 背景

当前 `mpy-cli` 已支持 `upload` 与 `run`，但缺少“手动删除设备端目标路径”的命令。
在调试与迭代过程中，用户常需要清理设备上的单个文件或目录；仅依赖 `deploy` 的增量删除路径不够直接。

## 目标

- 新增 `mpy-cli delete` 子命令。
- 支持删除单个文件与整个目录。
- 目录删除默认采用递归删除。
- `--path` 语义与 `run` 保持一致：相对 `device_upload_dir`。
- 复用现有端口解析、执行预览与确认体验。

## 非目标

- 不新增批量删除、多路径删除、通配符删除。
- 不修改 `plan/deploy/upload/run` 既有语义。
- 不引入设备端回收站或可恢复机制。

## 方案对比

### 方案 A（选型）：统一使用 `resume exec` 递归删除脚本

- CLI 只接收路径，不区分文件/目录。
- 由设备端脚本自动判断文件或目录并执行删除。
- 优点：行为统一、边界更可控、与 `run` 的实现风格一致。

### 方案 B：先 `fs rm`，失败后回退到递归脚本

- 文件场景命令更短。
- 缺点：需要依赖错误信息决定回退，稳定性与可维护性较差。

### 方案 C：用户显式声明类型（如 `--dir`）

- 实现逻辑直观。
- 缺点：增加使用负担，不符合“类似 run 给路径即可执行”的体验。

## 命令设计

```bash
mpy-cli delete [--path PATH] [--port PORT] [--no-interactive] [--yes]
```

- `--path`：设备目标路径（相对 `device_upload_dir`）。
- `--port`：指定设备端口。
- `--no-interactive`：禁用交互提问；缺少 `--path` 时直接报错。
- `--yes`：跳过删除前确认。

## 交互流程

1. 加载配置并解析端口（优先级沿用现有规则：`--port` > 配置 > 扫描/手输）。
2. 解析 `--path`：
   - 有值：直接使用。
   - 无值且交互模式：提示输入。
   - 无值且非交互模式：报错并退出。
3. 拼接最终设备路径：`device_upload_dir + path`。
4. 打印删除预览并确认（`--yes` 可跳过）。
5. 调用后端执行统一删除逻辑。

## 执行架构

- `mpy_cli/cli.py`
  - 新增 `delete` 子命令解析与 `_cmd_delete()`。
  - 复用 `_resolve_port()` 与 `_join_upload_target()`。
- `mpy_cli/backend/mpremote.py`
  - 新增 `build_delete_tree_command()` 与 `delete_path()`。
  - 使用 `mpremote connect <port> resume exec <script>` 在设备端执行删除。

## 设备端脚本语义

- 归一化输入路径，过滤空路径。
- 路径解析策略与 `run` 对齐：
  - 绝对路径优先直接尝试。
  - 相对路径尝试 `/<path>`，若存在 `/flash` 再尝试 `/flash/<path>`。
- 删除逻辑：
  - 若目标是文件：`os.remove()`。
  - 若目标是目录：递归删除子文件/子目录后 `os.rmdir()` 删除目录本身。
- 若所有候选路径均不存在，抛出明确错误。

## 错误处理与返回码

- 配置错误、端口缺失、非交互缺少参数、用户取消：返回 `1`。
- 后端删除失败（目标不存在、权限问题、命令失败等）：返回 `2`。
- 删除成功：返回 `0`。

## 测试策略

- `tests/test_cli.py`
  - `delete` 非交互缺少 `--path` 时返回 `1`。
  - `delete` 按 `device_upload_dir` 拼接最终远端路径。
  - 后端抛错时返回 `2`，成功时返回 `0`。
- `tests/test_mpremote_backend.py`
  - `build_delete_tree_command()` 构建为 `resume exec` 命令。
  - 脚本包含文件删除与目录递归删除逻辑。
- `tests/test_docs_and_ci.py`
  - README 中包含 `mpy-cli delete` 与对应参数说明。

## 验收标准

- 用户可执行 `mpy-cli delete --path <target>` 删除文件。
- 当 `--path` 指向目录时，默认递归删除整个目录。
- 配置了 `device_upload_dir` 时，`--path` 作为相对路径拼接。
- 具备预览与确认流程，`--yes` 可跳过确认。
- 新增测试通过，且不影响现有命令行为。
