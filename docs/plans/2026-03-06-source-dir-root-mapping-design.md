# source_dir 远端根映射统一设计文档

## 背景

当前 `source_dir` 在不同路径链路中的语义不一致：

- full 扫描阶段会在部分场景保留 `source_dir` 前缀（例如 `src/main.py`）。
- incremental 阶段会先在 `source_dir` 内收集变更，再补回 `source_dir` 前缀参与后续规划。
- `upload` 交互默认远端路径直接等于本地输入，不体现 `source_dir` 语义。

这会导致用户在设置 `source_dir = "src"` 时，仍需理解并处理 `src/` 前缀，违背“源码根映射远端根”的直觉。

## 目标

- 统一整个仓库路径设计语言：`source_dir` 仅表示本地源码根。
- `plan/deploy` 的 full 与 incremental 模式均以 `source_dir` 为远端路径基准。
- `.mpyignore` 匹配目标统一为“相对 `source_dir` 路径”。
- `upload` 交互默认远端路径按 `source_dir` 推导，行为与统一语义一致。

## 非目标

- 不改动 `device_upload_dir` 的职责（仍作为远端前缀）。
- 不改动 `upload --remote` 的显式输入优先级（用户显式值保持原样使用）。
- 不引入兼容开关或双语义并存模式。

## 方案对比

### 方案 A（选型）：全链路强一致语义

- 定义 `source_dir` 为本地根，所有自动计算出的远端相对路径均相对 `source_dir`。
- `.mpyignore` 匹配同样基于相对 `source_dir` 路径。
- 优点：规则单一、心智负担最低、模式间不切换语义。

### 方案 B：仅改 `plan/deploy`

- 仅统一部署链路，`upload` 与文档保持旧习惯。
- 优点：改动面较小。
- 缺点：命令间语义分裂，长期维护成本高。

### 方案 C：新增兼容开关

- 提供新旧语义切换。
- 优点：迁移平滑。
- 缺点：复杂度与测试矩阵上升，不符合当前 YAGNI。

## 统一语义定义

- `source_root`：`source_dir` 解析后的本地绝对目录。
- `source-relative path`：文件相对 `source_root` 的 POSIX 路径。
- `remote-relative path`：默认等于 `source-relative path`。
- `final remote path`：`join(device_upload_dir, remote-relative path)`。

示例：

- `source_dir = "src"`，本地 `src/main.py` -> `remote-relative = "main.py"`。
- `device_upload_dir = "apps/demo"` -> 最终远端 `:apps/demo/main.py`。

## 命令行为约束

### `plan/deploy` full

- 扫描文件时，远端路径统一采用 `source-relative path`。
- 不再在远端路径中保留 `source_dir` 前缀。

### `plan/deploy` incremental

- `collect_git_changes(source_root)` 返回的变更路径直接视为 `source-relative path`。
- 不再补齐或剥离 `source_dir` 前缀。
- 增量上传本地绝对路径由 `source_root / source-relative path` 得到。

### `upload`

- 当未显式提供 `--remote` 且处于交互模式时：
  - 默认远端路径优先尝试将本地路径转为 `source-relative path`；
  - 若本地路径不在 `source_root` 下，则回退为原输入本地路径。
- 当显式提供 `--remote` 时，不改动现有优先级与语义。

### `run/delete`

- 继续保持 `--path` 相对 `device_upload_dir` 的语义，不受本次设计影响。

## `.mpyignore` 语义

- 忽略规则匹配对象统一为 `source-relative path`。
- 若 `source_dir = "src"`，则规则应写为 `main.py`、`pkg/`、`*.pyc` 等。
- 不再推荐在规则中写 `src/...` 前缀。

## 兼容性与迁移

- 该变更对 `source_dir != "."` 的项目属于行为调整。
- 迁移建议：
  1. 检查 `.mpyignore` 中是否有 `src/` 类前缀规则。
  2. 改写为相对 `source_dir` 的规则。
  3. 先执行 `mpy-cli plan` 验证远端路径预览，再执行部署。

## 代码影响范围

- `mpy_cli/scanner.py`：统一远端路径映射到 `source_root`。
- `mpy_cli/cli.py`：移除增量前缀补齐/剥离链路；调整 upload 默认远端路径推导。
- `tests/test_scanner.py`、`tests/test_cli.py`：补充与修正统一语义测试。
- `README.md`、`tests/test_docs_and_ci.py`：补齐文档与文档一致性断言。

## 测试策略

- `tests/test_scanner.py`
  - `source_dir="app_src"` 时，`app_src/main.py` 的远端应为 `main.py`。
- `tests/test_cli.py`
  - incremental 模式远端路径不包含 `source_dir` 前缀。
  - incremental 的本地路径仍正确解析到 `source_root` 绝对路径。
  - upload 交互默认远端路径按 `source-relative` 推导。
- `tests/test_docs_and_ci.py`
  - README 包含 `source_dir` 统一语义说明。

## 验收标准

- 设置 `source_dir = "src"` 后，`src/main.py` 上传目标为 `:main.py`（或带 `device_upload_dir` 前缀）。
- full 与 incremental 两种模式结果一致，不出现 `src/` 远端前缀。
- `.mpyignore` 规则以 `source-relative path` 生效。
- README 与测试覆盖新的统一语义。
