# 手动单文件上传功能设计文档

## 背景

当前 `mpy-cli` 仅支持 `plan/deploy` 的计划式同步流程。对于临时上传单个脚本文件（例如 `seekfree_demo/E01_demo.py`）的场景，用户需要依赖 Git 变更或全量同步，成本较高。

本设计新增独立 `upload` 命令，支持手动输入本地文件路径，并在交互中确认/修改设备目标路径。

## 目标

- 新增 `mpy-cli upload` 子命令，用于单文件上传。
- 交互模式下仅通过手动输入本地文件路径，不做文件列表扫描。
- 目标路径默认与本地输入路径一致（如 `demo/demo.py` -> 默认目标 `demo/demo.py`），允许手动修改。
- 执行前显示上传预览并二次确认。
- 复用现有执行链（`DeployExecutor` + `MpremoteBackend`），保持日志与错误行为一致。

## 非目标

- 不改变 `plan/deploy` 的现有语义与流程。
- 不在本次支持多文件批量上传。
- 不新增额外运行时持久化文件。

## 交互与参数设计

### 命令形态

```bash
mpy-cli upload [--local LOCAL] [--remote REMOTE] [--port PORT] [--no-interactive] [--yes]
```

### 参数含义

- `--local`：本地文件路径。
- `--remote`：设备相对目标路径。
- `--port`：设备端口。
- `--no-interactive`：禁用交互提问；缺参数时直接报错。
- `--yes`：跳过执行前确认。

### 交互流程（无对应参数时）

1. 解析端口（沿用现有优先级：`--port` > 配置 > 扫描/手输）。
2. 提示输入本地文件路径。
3. 以本地输入路径作为默认值，提示输入设备目标路径（可直接回车）。
4. 打印预览：端口、本地路径、最终设备路径。
5. 确认后执行上传。

## 路径与执行语义

- `--remote` 或交互输入的目标路径统一作为“设备相对路径”。
- 最终远端路径由 `device_upload_dir + remote_path` 拼接得到，与现有 `deploy` 规则一致。
- 例：
  - `device_upload_dir = ""`，`remote = "seekfree_demo/E01_demo.py"` -> `:seekfree_demo/E01_demo.py`
  - `device_upload_dir = "apps/demo"`，`remote = "seekfree_demo/E01_demo.py"` -> `:apps/demo/seekfree_demo/E01_demo.py`

## 校验与错误处理

- 本地路径必须存在且为普通文件，否则提示并返回失败码。
- 目标路径去空白后不能为空。
- 非交互模式下缺失 `--local`、`--remote` 或 `--port`（且配置无法补足）时直接报错。
- 保持 `mpremote` 不可用与执行失败的现有报错风格。

## 实现边界

- `mpy_cli/cli.py`：新增 `upload` 命令解析和 `_cmd_upload` 流程。
- `mpy_cli/planner.py`：仅复用 `PlanOperation/DeployPlan` 数据结构，不新增新操作类型。
- `mpy_cli/executor.py`：无需改动核心逻辑，复用既有 `upload` 分支执行。

## 测试策略（TDD）

- `tests/test_cli.py`
  - `upload` 在交互模式下可读取本地路径并生成默认远端路径。
  - `upload` 可接受手动修改后的远端路径。
  - 非交互模式缺失必要参数时报错。
  - 本地路径不存在时报错。
- `tests/test_docs_and_ci.py`
  - README 参数总览新增 `mpy-cli upload` 与相关参数。

## 验收标准

- 用户可通过 `mpy-cli upload` 独立上传单文件。
- 用户输入 `seekfree_demo/E01_demo.py` 后，远端默认同路径并可改写。
- 上传前有清晰预览与确认（`--yes` 可跳过）。
- 新增测试通过且不破坏现有 `plan/deploy` 流程。
