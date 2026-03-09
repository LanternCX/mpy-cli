# list 命令性能优化设计文档

## 背景

当前 `mpy-cli list` 虽然已支持并发 probe，但仍会对 `mpremote connect list` 返回的全部端口执行探测。实际机器上常混有蓝牙、音频、调试串口等无关端口，导致 `list` 在多端口环境下仍然较慢。

## 目标

- 保持 `mpy-cli list` 返回“所有可用设备”的语义不变。
- 优先利用历史已见端口降低常规扫描时间。
- 增加可观测日志，便于定位慢端口、超时端口与整体耗时。
- 为慢或卡住的端口增加超时保护，避免拖慢整体结果。
- 兼容 macOS / Linux / Windows 的端口命名，不依赖 `/dev` 路径硬编码。

## 命令设计

```bash
mpy-cli list [--workers N] [--probe-timeout SECONDS] [--scan-mode MODE] [--reset-scan-records]
```

- `--workers`：并发探测线程数，控制同时 probe 的端口数量。
- `--probe-timeout`：单端口探测超时秒数。
- `--scan-mode`：控制缓存端口与全量端口的探测策略。
- `--reset-scan-records`：清空之前的扫描记录后，立即执行一次新的 `list`。

## 方案对比

### 方案 A（推荐）历史端口优先 + 可用端口交集 + 失败回退全扫

- 在 `runtime.db` 中持久化历史扫描到的端口名。
- 每次先读取历史端口，再调用 `mpremote connect list` 获取当前可用端口。
- 默认仅探测“历史端口 ∩ 当前可用端口”；若没有发现设备，再对当前可用端口做一次全量 probe。
- 优点：默认路径快，且不会盲 probe 已失效的旧端口；兼容 Windows `COM*` 与 Unix `/dev/*`。
- 缺点：需要新增运行时表与扫描模式控制。

### 方案 B 固定端口名白名单过滤

- 仅探测名称包含 `usbmodem`、`ttyACM`、`COM` 等模式的端口。
- 优点：实现简单。
- 缺点：规则脆弱，跨平台/不同驱动下易漏设备。

### 方案 C 仅依赖并发和超时

- 不增加缓存层，继续对全部当前端口 probe。
- 优点：逻辑最直观。
- 缺点：对端口多且杂的机器仍然偏慢。

最终采用方案 A。

## 架构与数据流

1. CLI 解析 `list` 的并发、超时与 `scan-mode` 参数。
2. `runtime.db` 新增 `scanned_ports` 表，记录历史见过的端口名、时间戳，以及“上一次扫描成功结果”快照。
3. CLI 先读取历史端口，再调用 `backend.list_ports()` 获取当前可用端口。
4. 以“上一次扫描成功端口 ∩ 当前可用端口”作为默认首批 probe 目标；需要时回退到当前可用端口全集。
5. `MpremoteBackend` 使用线程池并发 probe 指定端口列表。
6. CLI 将本次 `list_ports()` 返回的端口 upsert 回 `scanned_ports`，并用本次成功探测结果覆盖成功快照，再统一打印可用设备列表。

## 日志设计

- 记录整体扫描开始、结束、历史端口数、当前可用端口数、成功数、失败数与总耗时。
- 记录单端口 probe 开始、结束、耗时与失败原因。
- 记录是否触发从 `known-first` 回退到全量 probe。
- 记录是否执行了 `--reset-scan-records`。
- 日志仅写入现有运行目录日志体系，不新增额外持久化位置。

## 错误处理

- `mpremote` 缺失：退出码 `1`。
- 端口列表获取失败：退出码 `2`。
- 单端口 probe 超时或失败：不影响整体退出码，仅跳过该设备并写日志。
- 历史端口不存在于当前可用端口列表时，不执行 probe。
- 执行 `--reset-scan-records` 时，应先清空扫描历史和成功快照，再开始本次扫描。

## 测试策略

- `tests/test_runtime.py`
  - 验证 `scanned_ports` 表会随运行目录初始化创建。
  - 验证端口 upsert / list 行为。
  - 验证成功快照只保留上一次扫描成功结果。
- `tests/test_mpremote_backend.py`
  - 验证 `list_devices()` 能对指定端口列表执行并发 probe。
  - 验证单端口失败或超时时不阻断其他端口。
- `tests/test_cli.py`
  - 验证 `list --workers --probe-timeout --scan-mode` 会透传到 backend/调度层。
  - 验证 `known-first` 默认只 probe 上一次成功且当前可用的端口，并在无命中时回退全扫。
  - 验证 `--reset-scan-records` 会先清空记录，再执行扫描。
- `tests/test_docs_and_ci.py` + `README.md`
  - 保持命令参数说明与默认行为同步。

## 验收标准

- `mpy-cli list` 默认优先 probe 上一次扫描成功且当前可用的端口。
- 历史端口若都未命中，会自动回退到当前可用端口全集。
- 不会 probe 已缓存但当前不可用的旧端口。
- 成功缓存只保留上一次扫描成功结果，而不是历史成功并集。
- 超时端口不会拖慢全部结果。
- 日志可定位慢端口与整体扫描耗时。
- 默认行为兼容已有 `list` 输出语义。
