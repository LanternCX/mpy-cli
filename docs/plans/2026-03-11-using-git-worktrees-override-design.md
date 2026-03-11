# using-git-worktrees 项目覆盖设计文档

## 背景

当前环境已经存在 superpowers 自带的 `using-git-worktrees` 技能，其默认行为是在开始功能开发前创建隔离 worktree。这与本项目现有 `.opencode/skills/git-workflow/SKILL.md` 的约束冲突：本项目默认直接在当前开发分支工作，不主动创建 worktree，并要求所有 Git 行为统一遵循项目内 `git-workflow`。

用户希望“完全覆盖”原有 superpowers 的 `using-git-worktrees`，避免代理在本仓库里继续沿用内置 worktree 工作流。

## 目标

- 在项目内提供一个同名技能 `using-git-worktrees`，作为本仓库的优先规则入口。
- 当代理命中 `using-git-worktrees` 时，不再创建任何 `.worktrees/`、`worktrees/` 或外部 worktree。
- 将所有相关 Git 行为强制重定向到 `.opencode/skills/git-workflow/SKILL.md`。
- 明确禁止使用 superpowers 自带的 git worktrees 工作流。

## 方案对比

### 方案 A（推荐）项目内同名覆盖 + 重定向

- 在 `.opencode/skills/using-git-worktrees/SKILL.md` 新建同名技能。
- 技能内容不执行 worktree 创建，而是声明本项目里该入口仅用于拦截并改走项目内 `git-workflow`。
- 优点：覆盖语义最强，调用名称不变，兼容已有“触发旧技能名”的习惯。
- 缺点：需要在文案中明确这是“覆盖入口”而非“实现入口”，避免读者误解。

### 方案 B 新建别名技能

- 新建 `usign-git-worktrees` 或其他别名技能，并在内容里指向 `git-workflow`。
- 优点：实现简单。
- 缺点：无法覆盖旧入口；当代理命中 `using-git-worktrees` 时仍可能走到 superpowers 版本。

### 方案 C 仅强化 `git-workflow`

- 不新建同名技能，只在 `.opencode/skills/git-workflow/SKILL.md` 中继续强调禁用 worktree。
- 优点：文件更少。
- 缺点：无法拦截对 `using-git-worktrees` 的直接调用，不满足“完全覆盖”。

最终采用方案 A。

## 技能设计

### 技能位置与命名

- 新文件路径：`.opencode/skills/using-git-worktrees/SKILL.md`
- 技能名：`using-git-worktrees`
- 该命名与 superpowers 保持一致，以实现项目内同名覆盖。

### 技能职责

该技能不是创建工作区的执行说明，而是项目级覆盖入口，职责只有三项：

1. 拦截在本仓库中对 `using-git-worktrees` 的调用。
2. 明确声明本项目默认不使用 superpowers 自带 worktree 工作流。
3. 将后续 Git 行为重定向到 `.opencode/skills/git-workflow/SKILL.md`。

### 行为约束

- 禁止默认创建 `.worktrees/`、`worktrees/` 或任何仓库外 worktree 目录。
- 禁止因为“隔离更安全”“准备开工”“要执行计划”而自动进入 worktree 流程。
- 若用户没有明确要求隔离工作区，则必须留在当前工作区，并继续遵守项目 `git-workflow`。
- 即便上游 superpowers 技能提到了 `using-git-worktrees`，在本项目中也必须优先遵循项目技能。

## 文案结构

新技能文档建议包含以下部分：

- `Overview`：说明这是项目覆盖技能，不是 worktree 创建技能。
- `When to Use`：描述触发条件，例如准备开始实现、上游流程要求 worktree、用户提到 `using-git-worktrees`。
- `Checklist`：列出禁止创建 worktree、必须转向 `git-workflow` 等硬约束。
- `Quick Reference`：给出“命中该技能时应该做什么”的简表。
- `Common Rationalizations`：覆盖“先建 worktree 更安全”“上游技能要求这样做”等典型借口。
- `Red Flags`：看到要创建 worktree、引用 superpowers 流程、绕开项目 `git-workflow` 时立即停止。

## 与现有技能的关系

- `.opencode/skills/git-workflow/SKILL.md` 仍然是本项目唯一的 Git 执行规范来源。
- 新建的 `.opencode/skills/using-git-worktrees/SKILL.md` 只负责覆盖入口与重定向，不重复定义完整的分支/提交规则。
- 如有必要，可在 `git-workflow` 中补一条交叉引用，明确“凡命中 `using-git-worktrees` 也应回到本技能”。

## 错误处理

- 如果代理准备调用 superpowers 自带 worktree 流程，应立即停止并切回项目技能。
- 如果用户明确要求使用 worktree，则应先遵循项目 `git-workflow` 的默认约束，再根据用户指令执行，不把 superpowers 流程当默认值。
- 如果项目内同名技能未被发现，应视为技能覆盖配置不完整，需要补齐项目技能文件并重新尝试。

## 测试策略

- 记录一组 RED 基线：在没有项目覆盖技能时，代理会自然选择 superpowers worktree 流程。
- 新技能写入后，复测同样场景，验证代理会：
  - 拒绝默认创建 worktree
  - 明确说明本项目禁用 superpowers worktree 工作流
  - 转向 `.opencode/skills/git-workflow/SKILL.md`
- 检查技能 frontmatter 是否符合 `writing-skills` 约束：命名合法、`description` 只描述触发条件、便于检索。

## 验收标准

- 项目内存在同名技能 `.opencode/skills/using-git-worktrees/SKILL.md`。
- 技能正文明确声明本项目不使用 superpowers 自带 git worktrees 工作流。
- 技能正文明确要求改用 `.opencode/skills/git-workflow/SKILL.md`。
- 技能内容不再包含创建 worktree、选择目录、验证 `.gitignore`、运行基线测试等旧流程指令。
- 相关设计与实施计划文档已落到 `docs/plans/`。
