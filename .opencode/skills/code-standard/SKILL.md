---
name: code-standard
description: Use when creating or modifying code, architecture, comments, logging, or persistent file behavior in this project.
---

# code-standard

## Overview

本项目代码标准面向开源质量，强调高内聚低耦合、可维护文档化注释、可观测日志体系与可移植持久化策略。

核心约束：公共接口需要完整 Doxygen 风格注释；静态可持久化文件只能写入程序运行目录；日志必须同时支持标准输出与持久化切片。

## When to Use

- 新增或修改 Python 模块、函数、类、命令入口。
- 调整模块边界、依赖关系、目录结构。
- 新增配置、缓存、日志、运行时数据库等持久化行为。
- 新增或重构日志输出机制。

## Checklist

- [ ] 公共函数、类、模块提供完整 Doxygen 风格注释。
- [ ] 设计满足高内聚低耦合，避免跨层直接依赖。
- [ ] 静态可持久化文件（日志、配置、运行时数据）仅落到程序运行目录。
- [ ] 日志系统同时支持 stdout 输出与可持久化日志切片。
- [ ] 项目语言为中文时，代码注释使用中文。
- [ ] 技术栈优先使用 `python`、`questionary`、`rich`。

## Quick Reference

- Doxygen 注释最小模板：

```python
"""
@brief 简要说明
@param name 参数说明
@return 返回值说明
"""
```

- 运行目录建议：以当前执行目录为根，统一挂载 `logs/`、`data/`、`config/`。
- 日志最小能力：控制台可读 + 按大小/时间切片 + 可配置保留策略。

## Common Rationalizations

| 借口 | 为什么不成立 |
|---|---|
| "注释后面补" | 公共接口无注释会立刻降低可维护性与可用性。 |
| "先写到系统目录更通用" | 违反项目持久化约束，也可能触发权限问题。 |
| "先只打 stdout，切片后补" | 无持久化日志会导致问题难以追溯。 |
| "英文注释更国际化" | 当前项目语言明确为中文，需保持一致。 |

## Red Flags

- 新增公共 API 但未写 Doxygen 注释。
- 写入路径出现系统目录（如 `/var`、`/etc`、系统用户目录）作为默认持久化位置。
- 日志方案只保留控制台输出，无落盘切片。
- 中文项目中出现大段英文注释。

## Common Mistakes

- 在业务层直接调用底层实现细节，导致耦合上升。
- 仅给函数名写注释，不描述参数/返回值/行为边界。
- 把配置文件散落到多个不一致路径。
- 日志没有统一格式，问题定位成本高。
