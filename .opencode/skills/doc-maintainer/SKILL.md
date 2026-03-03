---
name: doc-maintainer
description: Use when creating or updating README, user guides, developer guides, deployment docs, or documentation structure in this project.
---

# doc-maintainer

## Overview

本项目文档要求区分用户文档与开发文档，并保持根文档作为统一入口。

核心约束：根文档必须包含项目介绍与快速开始，并提供跳转到开发文档和部署配置文档的链接；中文项目文档统一使用中文。

## When to Use

- 新增或修改根文档（README 等）时。
- 新增或修改 `docs/` 下的用户/开发/部署文档时。
- 新增功能后需要补齐使用说明或开发约束时。

## Checklist

- [ ] 用户文档与开发文档明确分层。
- [ ] 根文档包含项目介绍与快速开始。
- [ ] 根文档包含到开发文档、部署配置文档的跳转链接。
- [ ] 开发文档包含：架构说明、代码风格、Git 工作流、Agent 使用规范。
- [ ] Agent 规范明确指向项目目录 `.opencode/skills`。
- [ ] 项目语言为中文时，文档统一中文表达。

## Quick Reference

- 文档分层建议：
  - 根文档：项目入口与导航
  - 用户文档：安装、使用、常见问题
  - 开发文档：架构、规范、贡献流程
  - 部署文档：环境、打包、发布
- 开发文档最小章节：
  - 架构说明
  - 代码风格
  - Git 工作流
  - Agent 规范（`.opencode/skills`）

## Common Rationalizations

| 借口 | 为什么不成立 |
|---|---|
| "先改 README 就够了" | 只改入口不改分层文档会造成信息断层。 |
| "快速开始先不写" | 缺少首条路径会直接影响用户上手效率。 |
| "开发规范以后再补" | 团队协作会因缺规则而产生不一致改动。 |
| "中英混写更省事" | 中文项目要求中文文档，必须保持一致。 |

## Red Flags

- 根文档没有快速开始章节。
- 根文档没有指向开发文档或部署文档的链接。
- 开发文档缺失架构/代码风格/git workflow/agent 任一章节。
- 文档目录无法区分用户视角和开发视角。

## Common Mistakes

- 新功能发布后只更新命令示例，不更新行为说明。
- 开发文档只写代码细节，不写协作规范。
- 链接路径使用临时相对路径，后续移动后失效。
- 文档更新与代码改动不同步，导致内容过期。
