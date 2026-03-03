# OpenCode 项目技能建设 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `.opencode/skills/` 下创建并验证 `git-workflow`、`code-standard`、`doc-maintainer` 三个项目技能，覆盖 `docs/init-prompt.md` 的对应约束。

**Architecture:** 使用 `@superpowers:writing-skills` 的 RED -> GREEN -> REFACTOR 流程串行落地三个技能：先记录无技能时的失败证据，再写最小可用技能，再补齐反借口条款并复测。

**Tech Stack:** Markdown、Git、`@superpowers:writing-skills`、`@superpowers:test-driven-development`、`@superpowers:executing-plans`。

---

### 任务 1：记录 RED 基线失败证据

**文件：**
- 创建：`docs/plans/2026-03-03-opencode-skills-red-evidence.md`
- 修改：`docs/plans/2026-03-03-opencode-skills.md`
- 验证：`docs/plans/2026-03-03-opencode-skills-red-evidence.md`

**步骤 1：编写失败用例**

```markdown
## git-workflow RED
1. 未经用户确认直接 commit
2. commit message 非 Angular Commit
3. commit 缺少固定 Co-authored-by

## code-standard RED
1. 公共 API 无 Doxygen 注释
2. 持久化写入系统目录
3. 中文项目使用英文注释

## doc-maintainer RED
1. 只更新 README
2. 根文档缺快速开始
3. 开发文档缺架构/风格/git/agent 章节
```

**步骤 2：运行验证并确认失败**

执行：使用子代理按上述场景模拟“无项目技能”行为并记录原话。
预期：每个技能至少出现 1 条失败行为。

**步骤 3：编写最小实现**

```markdown
| Skill | Scenario | Baseline Violation | Evidence | Why It Fails |
|---|---|---|---|---|
```

**步骤 4：运行验证并确认通过**

执行：自查 RED 文档是否每个技能 >=3 场景、>=3 失败证据。
预期：PASS。

**步骤 5：提交**

```bash
# 1) 先输出提交确认单并等待用户确认（必须）
# 2) 用户确认后执行：
git add docs/plans/2026-03-03-opencode-skills.md docs/plans/2026-03-03-opencode-skills-red-evidence.md
git commit -m "docs(plan): add RED baseline evidence for project skills" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### 任务 2：实现 `git-workflow` 技能

**文件：**
- 创建：`.opencode/skills/git-workflow/SKILL.md`
- 修改：`docs/plans/2026-03-03-opencode-skills-red-evidence.md`
- 验证：`.opencode/skills/git-workflow/SKILL.md`

**步骤 1：编写失败用例**

```markdown
前置条件：用户要求执行 commit
期望：代理必须先请求用户确认，再允许 commit
并且：commit message 必须为 Angular Commit
并且：commit 必须附固定 Co-authored-by
```

**步骤 2：运行验证并确认失败**

执行：对照 RED 证据确认当前基线不满足上述约束。
预期：FAIL（存在未确认提交、格式不合规、缺尾部）。

**步骤 3：编写最小实现**

```markdown
---
name: git-workflow
description: Use when performing any git branch, commit, merge, tag, or release action in this project.
---

## Checklist
- [ ] 使用 main/dev 的 Git Flow。
- [ ] 每次 commit 前先征求用户确认。
- [ ] commit message 使用 Angular Commit。
- [ ] 每次 commit 都包含固定 Co-authored-by。
- [ ] 禁用 superpowers 内置 git-workflow。
```

**步骤 4：运行验证并确认通过**

执行：复测任务 1 同类场景。
预期：PASS（不再出现绕过确认与规范缺失）。

**步骤 5：提交**

```bash
# 1) 先输出提交确认单并等待用户确认（必须）
# 2) 用户确认后执行：
git add .opencode/skills/git-workflow/SKILL.md docs/plans/2026-03-03-opencode-skills-red-evidence.md
git commit -m "feat(skill): add project git-workflow rules" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### 任务 3：实现 `code-standard` 技能

**文件：**
- 创建：`.opencode/skills/code-standard/SKILL.md`
- 修改：`docs/plans/2026-03-03-opencode-skills-red-evidence.md`
- 验证：`.opencode/skills/code-standard/SKILL.md`

**步骤 1：编写失败用例**

```markdown
前置条件：新增公共 Python API
期望：必须有完整 Doxygen 风格注释

前置条件：增加日志/配置持久化
期望：仅允许程序运行目录

前置条件：项目语言为中文
期望：注释必须使用中文
```

**步骤 2：运行验证并确认失败**

执行：对照 RED 证据确认存在注释、路径、语言一致性问题。
预期：FAIL。

**步骤 3：编写最小实现**

```markdown
---
name: code-standard
description: Use when creating or modifying code, architecture, comments, logging, or persistent file behavior in this project.
---

## Checklist
- [ ] 公共接口具备 Doxygen 风格注释。
- [ ] 高内聚低耦合。
- [ ] 持久化仅落程序运行目录。
- [ ] 日志具备 stdout + 切片持久化。
- [ ] 中文项目注释使用中文。
- [ ] 优先 python + questionary + rich。
```

**步骤 4：运行验证并确认通过**

执行：复测任务 1 同类场景。
预期：PASS。

**步骤 5：提交**

```bash
# 1) 先输出提交确认单并等待用户确认（必须）
# 2) 用户确认后执行：
git add .opencode/skills/code-standard/SKILL.md docs/plans/2026-03-03-opencode-skills-red-evidence.md
git commit -m "feat(skill): define code quality and architecture standards" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### 任务 4：实现 `doc-maintainer` 技能

**文件：**
- 创建：`.opencode/skills/doc-maintainer/SKILL.md`
- 修改：`docs/plans/2026-03-03-opencode-skills-red-evidence.md`
- 验证：`.opencode/skills/doc-maintainer/SKILL.md`

**步骤 1：编写失败用例**

```markdown
前置条件：文档更新
期望：用户文档与开发文档必须分层

前置条件：根文档更新
期望：必须包含项目介绍 + 快速开始 + 跳转链接

前置条件：开发文档
期望：必须包含架构/代码风格/git workflow/agent 规范
```

**步骤 2：运行验证并确认失败**

执行：对照 RED 证据确认存在分层缺失、入口缺失、章节缺失。
预期：FAIL。

**步骤 3：编写最小实现**

```markdown
---
name: doc-maintainer
description: Use when creating or updating README, user guides, developer guides, deployment docs, or documentation structure in this project.
---

## Checklist
- [ ] 用户文档与开发文档分层。
- [ ] 根文档含项目介绍与快速开始。
- [ ] 根文档含跳转到开发/部署文档链接。
- [ ] 开发文档含架构、风格、git workflow、agent 规范。
- [ ] Agent 规范明确 `.opencode/skills`。
```

**步骤 4：运行验证并确认通过**

执行：复测任务 1 同类场景。
预期：PASS。

**步骤 5：提交**

```bash
# 1) 先输出提交确认单并等待用户确认（必须）
# 2) 用户确认后执行：
git add .opencode/skills/doc-maintainer/SKILL.md docs/plans/2026-03-03-opencode-skills-red-evidence.md
git commit -m "feat(skill): add documentation maintenance rules" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### 任务 5：最终一致性验证

**文件：**
- 修改：`docs/plans/2026-03-03-opencode-skills-red-evidence.md`
- 验证：`.opencode/skills/git-workflow/SKILL.md`
- 验证：`.opencode/skills/code-standard/SKILL.md`
- 验证：`.opencode/skills/doc-maintainer/SKILL.md`

**步骤 1：编写失败用例**

```markdown
若任一技能缺少以下项则判定失败：
1. frontmatter 仅有 name/description
2. description 以 Use when 开头
3. 包含 Overview/When to Use/Checklist/Quick Reference/Common Rationalizations/Red Flags/Common Mistakes
```

**步骤 2：运行验证并确认失败**

执行：若结构校验脚本返回 FAIL。
预期：FAIL（仅在结构缺失时）。

**步骤 3：编写最小实现**

```python
from pathlib import Path

required = [
    '## Overview',
    '## When to Use',
    '## Checklist',
    '## Quick Reference',
    '## Common Rationalizations',
    '## Red Flags',
    '## Common Mistakes',
]

for p in Path('.opencode/skills').glob('*/SKILL.md'):
    text = p.read_text(encoding='utf-8')
    assert text.startswith('---\n')
    for sec in required:
        assert sec in text
```

**步骤 4：运行验证并确认通过**

执行：`python3 <structure-check-script>`
预期：PASS。

**步骤 5：提交**

```bash
# 1) 先输出提交确认单并等待用户确认（必须）
# 2) 用户确认后执行：
git add .opencode/skills docs/plans/2026-03-03-opencode-skills-red-evidence.md docs/plans/2026-03-03-opencode-skills.md
git commit -m "chore(skill): verify project skills and finalize plan" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

## 需求映射（防漂移）

- `git-workflow` 对应 `docs/init-prompt.md:5-9, 44, 56`
- `code-standard` 对应 `docs/init-prompt.md:15-23, 45, 56`
- `doc-maintainer` 对应 `docs/init-prompt.md:25-33, 56`
- 路径约束：`.opencode/skills` 对应 `docs/init-prompt.md:56`（高优先级）
