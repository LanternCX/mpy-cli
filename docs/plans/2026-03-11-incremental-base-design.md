# incremental 基准提交对比设计文档

## 背景

当前 `incremental` 模式固定以 `HEAD` 为基准收集 Git 变更，再叠加当前未跟踪文件。这意味着用户只能对比“当前工作区 vs HEAD”，无法指定更早的基准提交来生成部署增量。

这会限制以下常见场景：

- 需要基于某次已知稳定提交重新计算部署增量。
- 需要把一个功能分支自某个基准提交以来的所有变更一次性部署到设备。
- 需要在保留当前工作区未提交改动的同时，扩大增量比较范围。

## 目标

- 为 `plan` 与 `deploy` 新增 `--base` 参数。
- 在 `incremental` 模式下支持“指定基准提交 vs 当前工作区”的增量计算。
- 未传 `--base` 时保持现有行为不变。
- 保持未跟踪文件仍被纳入增量集合。
- 在 CLI、README 与测试中同步体现新参数语义。

## 非目标

- 不将基准提交持久化到配置文件。
- 不改变 `full` 模式行为。
- 不引入多基准、提交范围表达式校验器或额外交互向导。

## 方案对比

### 方案 A（选型）：新增可选 CLI 参数 `--base`

- 在 `plan/deploy` 上新增 `--base <commit-ish>`。
- `incremental` 模式下将其传递到 Git 变更收集层。
- 未传时默认仍使用 `HEAD`。
- 优点：改动面小、兼容现有脚本、心智模型直接。

### 方案 B：把基准提交写入配置文件

- 在 `.mpy-cli.toml` 中增加类似 `sync.base`。
- 优点：适合固定项目流程。
- 缺点：临时需求反而更麻烦，且容易产生过期配置。

### 方案 C：新增独立命令或模式

- 例如 `plan-base`、`deploy-base` 或 `--mode range`。
- 优点：概念上可更显式。
- 缺点：命令面膨胀，不符合当前需求规模。

## 选型

采用方案 A。

原因：用户只需要一个轻量参数完成临时基准切换；当前代码结构已经把 Git 变更收集集中在 `mpy_cli/gitdiff.py`，适合通过一个可选参数扩展，而不需要改动配置模型或规划器接口。

## 统一语义定义

- `--base`：一个 Git `commit-ish`，可为完整 hash、短 hash、tag 或分支名。
- 当执行 `mpy-cli plan --mode incremental --base <ref>` 或 `mpy-cli deploy --mode incremental --base <ref>` 时：
  - 变更集合 = `ref` 相对当前工作区的 Git 路径变更 + 当前未跟踪文件。
- 当未传 `--base` 时：
  - 变更集合 = `HEAD` 相对当前工作区的 Git 路径变更 + 当前未跟踪文件。

## 命令行为约束

### `plan/deploy` incremental

- 允许传入 `--base`。
- `collect_git_changes()` 需要支持接收 `base_ref`。
- `source_dir` 作用域保持不变，仍在 `source_root` 目录内收集相对路径。

### `plan/deploy` full

- 不使用 `--base`。
- 若用户显式传入 `--base` 且模式为 `full`，CLI 应直接报错并返回失败退出码，避免参数静默失效。

## 数据流设计

1. CLI 解析 `--base`。
2. `_cmd_plan_or_deploy()` 在 `mode == "incremental"` 时读取该值。
3. CLI 调用 `collect_git_changes(source_root, base_ref=args.base or "HEAD")`。
4. `gitdiff` 层执行参数化的 `git diff --name-status --relative <base_ref> -- .`。
5. 继续用 `git ls-files --others --exclude-standard -- .` 收集未跟踪文件。
6. `planner` 无需理解 `--base`，仅消费已有 `ChangeEntry` 列表。

## 错误处理

- `--base` 无法被 Git 解析时，`git diff` 返回错误；CLI 延续当前错误出口，输出 `Git 变更读取失败: <git stderr>`。
- `full` 模式下使用 `--base` 时，直接输出面向用户的参数错误信息，例如“`--base` 仅支持 incremental 模式”。
- 若 `incremental` 模式未传 `--base`，不新增任何交互或提示。

## 代码影响范围

- `mpy_cli/cli.py`
  - 为 `plan/deploy` 增加 `--base` 参数。
  - 增量模式下向 `collect_git_changes()` 传递 `base_ref`。
  - 在 `full` 模式拒绝 `--base`。
- `mpy_cli/gitdiff.py`
  - 扩展 `collect_git_changes()` 签名与内部 Git 命令构造。
- `tests/test_gitdiff.py`
  - 新增基准参数透传测试。
- `tests/test_cli.py`
  - 新增 `--base` 透传测试与 `full + --base` 失败测试。
- `README.md`
  - 更新 `plan/deploy` 参数说明与示例。
- `tests/test_docs_and_ci.py`
  - 如文档断言需要，补充对 `--base` 的覆盖。

## 测试策略

- `tests/test_gitdiff.py`
  - 验证默认基准仍为 `HEAD`。
  - 验证自定义 `base_ref="abc123"` 时 Git 参数正确。
- `tests/test_cli.py`
  - 验证 `plan --mode incremental --base abc123` 会把 `abc123` 传给 `collect_git_changes()`。
  - 验证 `deploy --mode incremental --base abc123` 也会透传。
  - 验证 `--mode full --base abc123` 返回失败。
- `tests/test_docs_and_ci.py`
  - 验证 README 中 `plan/deploy` 参数列表包含 `--base`。

## 验收标准

- `mpy-cli plan --mode incremental --base abc123` 使用 `abc123` 作为增量基准。
- `mpy-cli deploy --mode incremental --base abc123` 使用 `abc123` 作为增量基准。
- 未传 `--base` 时行为与当前版本一致。
- `full` 模式下传 `--base` 会明确失败，而不是静默忽略。
- README、CLI 帮助与测试全部同步覆盖该参数语义。
