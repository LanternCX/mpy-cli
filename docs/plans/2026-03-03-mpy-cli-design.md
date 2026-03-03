# mpy-cli 设计文档

## 1. 目标

- 面向 MicroPython 开发场景提供命令行部署工具，解决 Thonny 逐文件烧录效率低的问题。
- 使用 `questionary` 提供交互式配置与执行确认。
- 支持两种同步模式：
  - `full`：清空设备文件系统后全量上传。
  - `incremental`：基于 `git diff` 文件集做增量上传/删除。
- 提供 `.mpyignore` 机制控制上传文件。
- 持久化文件统一写入项目运行目录（`.mpy-cli/`），不写系统目录。

## 2. 关键约束

- 技术栈：`python`、`questionary`、`rich`。
- 项目语言为中文，注释与文档使用中文。
- 代码采用高内聚低耦合分层架构。
- 日志系统同时支持标准输出与可持久化日志切片。
- 增量模式直接使用 `git diff` 文件集，不依赖上次部署 commit 状态。

## 3. 架构设计

### 3.1 模块划分

- `mpy_cli/cli.py`：命令入口，负责参数解析与交互流程。
- `mpy_cli/config.py`：配置读写与校验（`.mpy-cli.toml`）。
- `mpy_cli/ignore.py`：`.mpyignore` 规则解析与匹配。
- `mpy_cli/gitdiff.py`：读取并解析 Git 变更文件。
- `mpy_cli/planner.py`：生成部署计划（上传/删除/擦除）。
- `mpy_cli/backend/mpremote.py`：封装 `mpremote` 调用。
- `mpy_cli/executor.py`：按计划执行设备侧操作。
- `mpy_cli/runtime.py`：运行目录初始化（日志、数据库、状态文件）。
- `mpy_cli/logging.py`：Rich 控制台日志 + RotatingFileHandler 文件日志。

### 3.2 数据模型

- `SyncMode`：`full` / `incremental`。
- `ChangeEntry`：`status` + `src_path` + `dst_path`（重命名场景）。
- `PlanOperation`：`wipe` / `upload` / `delete`。
- `DeployPlan`：操作列表、统计信息、风险提示（是否包含 wipe）。

## 4. 执行流程

### 4.1 初始化

1. `mpy-cli init` 生成：
   - `.mpy-cli.toml`
   - `.mpyignore`
   - `.mpy-cli/` 运行目录（含日志目录与运行时数据库）
2. 若文件已存在，仅补齐缺失项，保持幂等。

### 4.2 计划生成

1. 读取配置并选择模式（配置默认 + 交互可覆盖）。
2. 解析本地候选文件并应用 `.mpyignore`。
3. 根据模式生成计划：
   - `full`：`wipe` + 全量 `upload`
   - `incremental`：
     - `git diff --name-status` 获取 A/M/R/D 文件
     - `git ls-files --others --exclude-standard` 获取未跟踪文件
     - A/M/R + untracked => `upload`
     - D => `delete`
4. 使用 Rich 展示计划摘要与明细。

### 4.3 执行

1. `mpy-cli deploy` 进入交互确认。
2. 若包含 `wipe`，必须二次确认。
3. 逐项执行计划并实时输出日志。
4. 执行结果写入 `.mpy-cli/data/runtime.db` 与日志文件。

## 5. 错误处理策略

- `mpremote` 不存在：明确提示安装命令并退出。
- 设备连接失败：提示串口占用/权限问题并退出。
- 单文件上传失败：记录失败项，执行完后统一汇总。
- wipe 失败：立即中止后续操作，防止半状态扩散。
- Git 命令不可用或目录非仓库：增量模式报错并给出修复建议。

## 6. 测试策略（TDD）

- `tests/test_config.py`：配置默认值、模式合法性、文件读写。
- `tests/test_ignore.py`：忽略规则、取反规则、目录规则。
- `tests/test_gitdiff.py`：A/M/R/D/untracked 解析行为。
- `tests/test_planner.py`：full/incremental 计划生成正确性。
- `tests/test_mpremote_backend.py`：命令拼装与错误映射。
- `tests/test_executor.py`：执行顺序（wipe 优先）与失败汇总。

## 7. CI 与发布设计

- Tag push 触发 GitHub Actions：
  - 运行测试（若项目存在测试）。
  - 构建 4 平台发布包：
    - `mac-arm64`（tar.gz）
    - `linux-arm64`（tar.gz）
    - `linux-x64`（tar.gz）
    - `windows-x64`（zip）
  - 自动创建 draft release 并上传产物。
- 发布包内包含静态文件：默认配置模板、运行时数据库模板。

## 8. 里程碑

1. 完成基础骨架与配置系统。
2. 完成 `.mpyignore` 与 `git diff` 增量计划器。
3. 完成 `mpremote` 后端与执行器。
4. 完成交互式 CLI 与日志系统。
5. 完成测试、文档、CI 发布流程。
