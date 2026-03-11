# using-git-worktrees Override Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Override the superpowers `using-git-worktrees` behavior inside this repository so that any hit on that skill redirects to the project-local `git-workflow` rules instead of creating a worktree.

**Architecture:** Add a project-local skill at `.opencode/skills/using-git-worktrees/SKILL.md` with the same name as the superpowers skill. Keep that new skill intentionally narrow: it acts as a blocker and redirector, while `.opencode/skills/git-workflow/SKILL.md` remains the single source of truth for Git behavior in this repository. Capture RED/GREEN evidence in `docs/plans/` so the override is justified and testable as a skill-writing change.

**Tech Stack:** Markdown skill docs, OpenCode skills, repository-local documentation.

---

### Task 1: Capture failing baseline evidence for the current superpowers behavior

**Files:**
- Create: `docs/plans/2026-03-11-using-git-worktrees-override-red-evidence.md`
- Read: `.opencode/skills/git-workflow/SKILL.md`
- Read: `~/.config/opencode/skills/superpowers/using-git-worktrees/SKILL.md`

**Step 1: Write the failing test**

Create a short evidence note that defines at least two pressure scenarios where an agent is likely to reach for the built-in worktree flow, for example:

```markdown
## Scenario 1
User asks to start implementation after design approval.
Expected bad baseline: agent follows superpowers `using-git-worktrees` and proposes creating `.worktrees/...`.

## Scenario 2
User asks to use `using-git-worktrees` explicitly.
Expected bad baseline: agent treats the built-in skill as authoritative and does not redirect to project `git-workflow`.
```

**Step 2: Run test to verify it fails**

Run the scenarios manually or with a subagent without the new project-local override present.

Expected: the baseline behavior still prefers the superpowers worktree workflow, which demonstrates the need for an override skill.

**Step 3: Write minimal implementation**

Document the observed failure modes verbatim in `docs/plans/2026-03-11-using-git-worktrees-override-red-evidence.md`, including the rationalizations that need to be blocked.

**Step 4: Run test to verify it passes**

Re-read the evidence note and confirm it clearly captures why the override is required.

**Step 5: Commit**

```bash
git add docs/plans/2026-03-11-using-git-worktrees-override-red-evidence.md
git commit -m "docs(skills): capture worktree override red evidence"
```

### Task 2: Add the project-local override skill

**Files:**
- Create: `.opencode/skills/using-git-worktrees/SKILL.md`
- Modify: `.opencode/skills/git-workflow/SKILL.md`

**Step 1: Write the failing test**

Define the expected override behavior directly in the new skill draft checklist:

```markdown
- Hitting `using-git-worktrees` in this repo must not create a worktree.
- The agent must explicitly redirect to `.opencode/skills/git-workflow/SKILL.md`.
- The skill must explicitly forbid the superpowers built-in worktree workflow.
```

Also add one assertion to `git-workflow` saying this repository's `using-git-worktrees` entry is a redirect, not a workspace-creation workflow.

**Step 2: Run test to verify it fails**

Compare the draft requirements against the current repository state.

Expected: FAIL because `.opencode/skills/using-git-worktrees/SKILL.md` does not exist yet and `git-workflow` does not explicitly cross-reference the new override entry.

**Step 3: Write minimal implementation**

Create `.opencode/skills/using-git-worktrees/SKILL.md` with content shaped like this:

```markdown
---
name: using-git-worktrees
description: Use when worktree setup is suggested in this repository, when a workflow requests using-git-worktrees, or when Git work should stay under the project-local git rules instead of the superpowers worktree flow.
---

# using-git-worktrees

## Overview

本技能在本项目中用于覆盖 superpowers 的同名技能。
命中该技能时，禁止进入内置 git worktrees 工作流，必须改为遵循 `.opencode/skills/git-workflow/SKILL.md`。
```

Then complete the required sections: `When to Use`, `Checklist`, `Quick Reference`, `Common Rationalizations`, `Red Flags`, and `Common Mistakes`.

Update `.opencode/skills/git-workflow/SKILL.md` to add a short cross-reference so both skills point to the same project policy.

**Step 4: Run test to verify it passes**

Re-read both skill files and confirm:
- no worktree creation steps remain in the new override skill
- the override skill explicitly forbids superpowers worktrees
- the override skill explicitly redirects to project `git-workflow`
- `git-workflow` now acknowledges the override entry

**Step 5: Commit**

```bash
git add .opencode/skills/using-git-worktrees/SKILL.md .opencode/skills/git-workflow/SKILL.md
git commit -m "docs(skills): override using-git-worktrees in project"
```

### Task 3: Refactor the skill against loopholes

**Files:**
- Modify: `.opencode/skills/using-git-worktrees/SKILL.md`
- Modify: `docs/plans/2026-03-11-using-git-worktrees-override-red-evidence.md`

**Step 1: Write the failing test**

List the likely loopholes that would weaken the override, such as:

```markdown
- "只是先建个 worktree，更安全"
- "上游 brainstorming / executing-plans 说要用 worktree"
- "用户没禁止，所以默认沿用 superpowers"
```

**Step 2: Run test to verify it fails**

Check whether the first draft of the override skill explicitly blocks each loophole.

Expected: at least one loophole is still phrased too loosely or only implied.

**Step 3: Write minimal implementation**

Tighten the override skill language so each loophole has an explicit counter in `Common Rationalizations` or `Red Flags`. Update the RED evidence note with the final blocked patterns.

**Step 4: Run test to verify it passes**

Re-read the override skill and verify every identified loophole is explicitly closed.

**Step 5: Commit**

```bash
git add .opencode/skills/using-git-worktrees/SKILL.md docs/plans/2026-03-11-using-git-worktrees-override-red-evidence.md
git commit -m "docs(skills): harden worktree override rules"
```

### Task 4: Final verification sweep

**Files:**
- No intended code changes.

**Step 1: Verify file set**

Run:

```bash
git diff -- .opencode/skills/using-git-worktrees/SKILL.md .opencode/skills/git-workflow/SKILL.md docs/plans/2026-03-11-using-git-worktrees-override-design.md docs/plans/2026-03-11-using-git-worktrees-override-implementation.md docs/plans/2026-03-11-using-git-worktrees-override-red-evidence.md
```

Expected: only the intended skill and planning documents appear.

**Step 2: Verify the override contract**

Re-read `.opencode/skills/using-git-worktrees/SKILL.md` and check for these exact outcomes:
- same skill name as superpowers: `using-git-worktrees`
- no instructions to create `.worktrees/`, `worktrees/`, or global worktree directories
- explicit prohibition on using the superpowers built-in worktree workflow
- explicit redirect to `.opencode/skills/git-workflow/SKILL.md`

**Step 3: Verify repository docs consistency**

Run:

```bash
git status
```

Expected: only the intended project-local skill and `docs/plans/` files are modified.

**Step 4: Optional progress entry**

If implementation work is completed in the same session, add a `.progress/` entry describing the override decision and link the final commit hash.
