---
name: using-git-worktrees
description: Use when worktree setup is suggested in this repository, when a workflow references using-git-worktrees, or when Git actions must stay under the project-local git rules instead of the superpowers worktree flow.
---

# using-git-worktrees

## Overview

本技能在本项目中用于覆盖 superpowers 的同名技能，不用于创建 worktree。

核心约束：一旦命中 `using-git-worktrees`，必须停止使用 superpowers 自带 git worktrees 工作流，并立即转向 `.opencode/skills/git-workflow/SKILL.md`。

## When to Use

- 上游流程、设计文档或用户指令提到 `using-git-worktrees`。
- 代理准备因为“隔离更安全”而创建 `.worktrees/`、`worktrees/` 或仓库外 worktree。
- 某个技能把 worktree 当作默认前置步骤，但当前仓库需要遵守项目内 Git 规则。
- 需要判断本项目是否应该沿用 superpowers 自带 worktree 工作流。

## Checklist

- [ ] 本项目命中 `using-git-worktrees` 时，禁止进入 superpowers 自带 worktree 流程。
- [ ] 未获用户明确要求时，不创建 `.worktrees/`、`worktrees/` 或任何外部 worktree。
- [ ] 不执行目录选择、ignore 校验、`git worktree add`、切换到新工作区等内置步骤。
- [ ] 必须改为遵循 `.opencode/skills/git-workflow/SKILL.md`。
- [ ] 若后续需要 Git 分支、提交、合并、发版等操作，统一按项目 `git-workflow` 执行。
- [ ] 若用户明确要求隔离工作区，也不能回退到 superpowers 自带技能，仍需先以项目 `git-workflow` 为准判断如何执行。

## Quick Reference

| Situation | Action |
|---|---|
| 看到 `using-git-worktrees` | 视为项目覆盖入口，不是创建 worktree 的说明 |
| 准备创建 `.worktrees/` | 立即停止，改读 `.opencode/skills/git-workflow/SKILL.md` |
| 上游技能要求 dedicated worktree | 本项目中忽略该默认值，优先项目 Git 规则 |
| 用户明确要求隔离工作区 | 不调用 superpowers 内置流程，先按项目 `git-workflow` 约束处理 |

## Common Rationalizations

| 借口 | 为什么不成立 |
|---|---|
| "先建个 worktree 更安全" | 本项目默认直接在当前开发分支工作，安全性不能覆盖项目 Git 规则。 |
| "上游 brainstorming / executing-plans 要求先建 worktree" | 上游技能默认值不能压过项目同名覆盖技能。 |
| "用户没禁止，所以沿用 superpowers 默认流程" | 本项目已明确禁止把 superpowers worktree 工作流当默认值。 |
| "既然技能名一样，就按内置版本执行" | 同名正是为了在本项目内完成覆盖，必须优先遵循项目技能。 |
| "先把目录和 ignore 检查做了也无妨" | 这些步骤本身就是内置 worktree 流程的一部分，本项目中不应启动。 |

## Red Flags

- 准备创建 `.worktrees/`、`worktrees/` 或外部 worktree 目录。
- 准备执行 `git worktree add`。
- 准备引用 superpowers 自带 `using-git-worktrees` 作为当前仓库规则。
- 看到“dedicated worktree”就默认进入隔离工作区流程。
- 命中 `using-git-worktrees` 后没有立即切到 `.opencode/skills/git-workflow/SKILL.md`。

## Common Mistakes

- 把本技能误当作“如何创建 worktree”的执行文档。
- 只禁止创建目录，但仍保留内置 worktree 的判断与准备步骤。
- 口头上说遵守项目 Git 规则，实际仍按 superpowers 流程操作。
- 用户一提到隔离工作区，就跳过项目 `git-workflow` 的默认约束。
