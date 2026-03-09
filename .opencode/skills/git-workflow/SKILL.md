---
name: git-workflow
description: Use when performing any git branch, commit, merge, tag, or release action in this project.
---

# git-workflow

## Overview

本项目 Git 流程必须使用 Git Flow 思路（`main` + `dev`），并严格执行 Angular Commit 规范。

核心约束：默认直接在当前开发分支工作，不主动创建 worktree 或新分支；每次 `git commit` 前必须先得到用户确认，且每次提交都必须追加固定 co-author 尾部。

## When to Use

- 任何分支创建、切换、合并、提交、打 Tag、发版相关操作。
- 任何需要输出提交信息（commit message）的操作。
- 任何需要在当前工作区执行 Git 命令的操作。

## Checklist

- [ ] 分支策略遵循 Git Flow：开发在 `dev`，稳定在 `main`。
- [ ] 默认直接在当前分支工作；未获用户明确要求时，不创建 `.worktrees/`、`worktrees/` 或外部 worktree。
- [ ] 未获用户明确要求时，不主动创建、切换或重建功能分支。
- [ ] 若仓库尚无初始提交（unborn 分支），先完成一次初始化提交，再校验 `main`/`dev` 双分支。
- [ ] 若 `dev` 分支不存在，先创建 `dev` 再开发。
- [ ] 每次 commit 前必须先给用户提交确认单并等待确认。
- [ ] 未获用户确认时，禁止为了“保存进度”或“方便回滚”而自动 commit。
- [ ] commit message 必须符合 Angular Commit 规范（如 `feat: ...`、`fix: ...`）。
- [ ] 每次 commit 都追加以下尾部：
  `Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>`
- [ ] 禁止使用 superpowers 内置 git-workflow，必须使用本项目技能规则。

## Quick Reference

- 提交确认单模板：
  - 目标分支：`dev` 或 `main`
  - 变更文件列表：逐项列出
  - 提交信息：Angular Commit 格式
  - co-author：固定尾部已包含
- Angular Commit 常用类型：`feat`、`fix`、`docs`、`refactor`、`test`、`chore`
- 默认开发分支：`dev`
- 默认工作方式：直接在当前开发分支修改，不使用 superpowers worktree 工作流

## Common Rationalizations

| 借口 | 为什么不成立 |
|---|---|
| "这次改动很小，先提了再说" | 任何 commit 都必须先确认，改动大小不影响流程约束。 |
| "co-author 可选，这次省略" | 本项目明确要求每次提交都带固定 co-author。 |
| "先用一句 update 方便" | 非 Angular Commit 会破坏提交历史可读性与自动化流程。 |
| "直接在 main 上改更快" | 与 Git Flow 冲突，会增加主干风险。 |
| "先建个 .worktrees 更安全" | 本项目默认不使用 superpowers worktree 工作流，除非用户明确要求隔离工作区。 |

## Red Flags

- 出现 "先 commit 后确认" 的念头时必须立即停止。
- 出现 "先建 worktree 再做" 的默认动作时必须立即停止。
- 出现非 Angular Commit 信息时必须重写。
- 准备提交但未附 co-author 尾部时必须中止。
- 准备调用内置 git-workflow 时必须改用本技能。

## Common Mistakes

- 忘记切换到 `dev` 就开始开发。
- 在未获用户要求时擅自创建 worktree 或额外分支。
- 提交前只看代码不出提交确认单。
- 提交信息写成自然语言句子，缺少类型前缀。
- 只在首个提交加 co-author，后续提交遗漏。
