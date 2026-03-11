# using-git-worktrees 覆盖 RED 基线证据

## 基线场景

### 场景 1：设计完成后准备进入实现

- 触发条件：上游流程进入实现阶段，并提到需要使用 `using-git-worktrees`。
- 基线违例：代理沿用 superpowers 自带技能，准备创建 `.worktrees/<branch>`。
- 失败原因：与本项目“默认在当前开发分支工作，不主动创建 worktree”的 Git 规则冲突。

### 场景 2：用户直接点名 `using-git-worktrees`

- 触发条件：用户要求“按 using-superpowers 新建一个 using-git-worktrees”。
- 基线违例：代理把 superpowers 同名技能当成权威实现，继续保留目录选择、ignore 校验、worktree 创建等步骤。
- 失败原因：无法实现项目级覆盖，也无法阻断内置 worktree 工作流。

### 场景 3：执行计划或子任务前需要“隔离工作区”

- 触发条件：实现计划或执行型技能将 worktree 视为默认前置条件。
- 基线违例：代理以“隔离更安全”“流程要求”为由自动切到 worktree 流程。
- 失败原因：会绕过本项目 `.opencode/skills/git-workflow/SKILL.md` 中“默认不使用 superpowers worktree 工作流”的硬约束。

## 无项目覆盖技能时的基线违例（RED）

| Scenario | Baseline Violation | Evidence | Why It Fails |
|---|---|---|---|
| 设计后进入实现 | 自动建议创建 `.worktrees/...` | "I'm using the using-git-worktrees skill to set up an isolated workspace." | 把内置 worktree 流程当默认值，违反项目 Git 规则。 |
| 用户直接点名同名技能 | 继续执行目录选择和 `git worktree add` 逻辑 | "Follow this priority order... Create worktree with new branch" | 命中了错误技能语义，无法实现项目覆盖。 |
| 上游流程要求 worktree | 以“流程需要”为由忽略项目约束 | "Context: This should be run in a dedicated worktree" | 上游默认值压过项目规则，缺少本地拦截技能。 |

## 需要阻断的典型借口

- "先建个 worktree 更安全。"
- "上游技能要求先建隔离工作区。"
- "用户没有明确禁止，所以沿用 superpowers 默认流程。"
- "同名技能已经存在，不需要项目内再覆盖。"

## GREEN 目标

- 本项目存在同名 `.opencode/skills/using-git-worktrees/SKILL.md`。
- 命中 `using-git-worktrees` 时，禁止默认创建任何 worktree。
- 代理必须明确声明：不要使用 superpowers 自带 git worktrees 工作流。
- 后续 Git 行为必须重定向到 `.opencode/skills/git-workflow/SKILL.md`。
