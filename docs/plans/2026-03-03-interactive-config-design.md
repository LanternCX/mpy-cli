# 交互式配置向导设计文档

## 背景

当前配置流程依赖用户手动修改 `.mpy-cli.toml`，对首次使用者不友好，也容易出现格式错误和字段遗漏。

## 目标

- 提供交互式配置体验，减少直接编辑配置文件。
- 新增 `mpy-cli config` 命令，允许用户随时重配。
- `mpy-cli init` 在初始化后自动进入配置向导（支持关闭交互）。
- 配置向导复用端口扫描能力，优先从扫描结果选择端口。

## 非目标

- 不改变 `.mpy-cli.toml` 字段结构。
- 不改变 `plan/deploy` 的主流程语义。

## 方案

### 1) 模块拆分

- 新增 `mpy_cli/config_wizard.py`：
  - 负责交互提问、默认值回填、端口扫描选择。
  - 输出标准 `AppConfig` 对象。

- 扩展 `mpy_cli/config.py`：
  - 新增配置写回函数 `save_config()`。
  - 新增 `default_config()`，避免向导重复维护默认值。

- 扩展 `mpy_cli/cli.py`：
  - 新增 `config` 子命令。
  - `init` 增加 `--no-interactive`，默认进入向导。

### 2) 交互流程

- 端口：优先扫描设备端口并选择，支持“手动输入端口”。
- 同步模式：`incremental` / `full`。
- 其余字段：`ignore_file`、`runtime_dir`、`source_dir`、`mpremote_binary`。

### 3) 兼容策略

- `--port`、`--mode` 命令行参数继续具备最高优先级。
- 非交互模式行为保持原有严格策略。

## 测试策略

- `tests/test_config.py`：保存与读取回归测试。
- `tests/test_config_wizard.py`：端口扫描选择和手动输入路径。
- `tests/test_cli.py`：`init` 触发向导、`config` 重配写回。
- `tests/test_docs_and_ci.py`：README 说明更新。

## 验收标准

- 用户无需手动编辑 TOML 即可完成首次配置和后续重配。
- 配置写回后 `plan/deploy` 能直接使用新值。
- 测试全量通过。
