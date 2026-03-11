# CLI 短参数同义设计文档

## 背景

当前 `mpy-cli` 的子命令参数以长选项为主，可读性较好，但在高频命令行使用场景下输入偏长。用户希望为每个命令的每个参数补充单字符短选项，同一语义可以同时支持长短两种写法。

## 目标

- 为所有现有子命令参数增加单字符短选项同义。
- 保持现有长选项行为完全兼容。
- 允许短选项在不同子命令内复用，不强求全局唯一。
- 保持 `README.md`、CLI 帮助输出与测试同步。

## 方案对比

### 方案 A（推荐）按参数名直觉分配，子命令内解决冲突

- 优先使用参数名首字母，例如 `--mode -> -m`、`--port -> -p`。
- 若同一子命令内冲突，再为冲突参数选次优字母。
- 优点：大多数参数一眼可猜，记忆成本最低。
- 缺点：少量参数需要非首字母，如 `--no-interactive -> -n`。

### 方案 B 统一按参数类别分配

- 路径类、布尔类、模式类分别使用固定字母集合。
- 优点：风格整齐。
- 缺点：不如按参数名直接映射直观，用户仍需额外记规则。

### 方案 C 仅为高频参数补短选项

- 减少冲突与文档维护成本。
- 缺点：不满足“每个命令的每个参数都增加短选项”的需求。

最终采用方案 A。

## 命令设计

### `init`

```bash
mpy-cli init [-f|--force] [-n|--no-interactive]
```

### `list`

```bash
mpy-cli list [-w|--workers N] [-t|--probe-timeout SECONDS] [-s|--scan-mode MODE] [-r|--reset]
```

### `plan` / `deploy`

```bash
mpy-cli plan [-m|--mode {incremental,full}] [-b|--base BASE] [-p|--port PORT] [-n|--no-interactive] [-y|--yes]
mpy-cli deploy [-m|--mode {incremental,full}] [-b|--base BASE] [-p|--port PORT] [-n|--no-interactive] [-y|--yes]
```

### `upload`

```bash
mpy-cli upload [-l|--local PATH] [-r|--remote PATH] [-p|--port PORT] [-n|--no-interactive] [-y|--yes]
```

### `run`

```bash
mpy-cli run [-f|--path PATH] [-p|--port PORT] [-n|--no-interactive] [-y|--yes]
```

### `delete`

```bash
mpy-cli delete [-f|--path PATH] [-p|--port PORT] [-n|--no-interactive] [-y|--yes]
```

### `tree`

```bash
mpy-cli tree [-a|--path PATH] [-p|--port PORT] [-n|--no-interactive]
```

- `tree` 内 `--path` 与 `--port` 均可能争用 `-p`。
- 为保证高频串口参数的一致性，保留 `--port -> -p`。
- `tree --path` 退让为 `-a`，取自 p`a`th 中次优可用字符，虽然不如 `-p` 直觉，但可避免同一子命令歧义。

## 架构与影响面

1. 在 `mpy_cli/cli.py` 的 `build_parser()` 中为每个 `add_argument()` 增加短选项别名。
2. 参数 `dest`、默认值、行为分支不变，仅扩展 `argparse` 接受的输入形式。
3. 在 `tests/test_cli.py` 中新增回归测试，覆盖典型短选项解析结果。
4. 更新 `README.md` 的命令示例与参数总览。
5. 如 `tests/test_docs_and_ci.py` 对 README/参数文本有同步校验，需要一并更新。

## 错误处理

- 不引入新的业务错误码。
- 若短选项冲突，问题应在解析器构建阶段暴露，因此实现时需确保同一子命令内唯一。
- 长选项保持兼容，避免破坏现有脚本或用户习惯。

## 测试策略

- 在 `tests/test_cli.py` 中增加短选项解析测试：
  - `plan/deploy` 的 `-m/-b/-p/-n/-y`
  - `list` 的 `-w/-t/-s/-r`
  - `upload` 的 `-l/-r/-p/-n/-y`
  - `run/delete/tree` 的冲突参数映射
- 运行 `tests/test_docs_and_ci.py`，确保 README 与 CLI 定义同步。
- 运行全量测试，确认短选项扩展没有影响既有行为。

## 验收标准

- 每个现有 CLI 参数都存在一个可用的单字符短选项。
- 长选项与既有行为保持兼容。
- 同一子命令内不存在短选项冲突。
- README、帮助输出、测试全部同步通过。
