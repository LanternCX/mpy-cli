# Incremental Base Reference Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `--base` to incremental `plan/deploy` so users can compute deployment deltas from a specified Git commit-ish to the current workspace while preserving current `HEAD`-based behavior when omitted.

**Architecture:** Keep planning and execution behavior unchanged outside the Git change collection boundary. Extend CLI parsing in `mpy_cli/cli.py`, pass a `base_ref` down into `mpy_cli/gitdiff.py`, and continue feeding the resulting `ChangeEntry` list into the existing planner. Reject `--base` in `full` mode to avoid silent no-op arguments.

**Tech Stack:** Python, argparse, pathlib, subprocess, pytest.

---

### Task 1: Add failing gitdiff regression test for custom base refs

**Files:**
- Modify: `tests/test_gitdiff.py`
- Test: `mpy_cli/gitdiff.py`

**Step 1: Write the failing test**

```python
def test_collect_git_changes_uses_custom_base_ref(monkeypatch) -> None:
    captured: list[list[str]] = []

    def fake_run_git(args: list[str], repo_path: Path) -> str:
        captured.append(args)
        return ""

    monkeypatch.setattr("mpy_cli.gitdiff._run_git", fake_run_git)

    collect_git_changes(Path("/tmp/repo"), base_ref="abc123")

    assert captured == [
        ["diff", "--name-status", "--relative", "abc123", "--", "."],
        ["ls-files", "--others", "--exclude-standard", "--", "."],
    ]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_gitdiff.py -k custom_base_ref`
Expected: FAIL because `collect_git_changes()` does not accept `base_ref` yet.

**Step 3: Write minimal implementation**

```python
def collect_git_changes(repo_path: Path, base_ref: str = "HEAD") -> list[ChangeEntry]:
    name_status_output = _run_git(
        ["diff", "--name-status", "--relative", base_ref, "--", "."],
        repo_path,
    )
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_gitdiff.py -k custom_base_ref`
Expected: PASS.

### Task 2: Add failing CLI tests for `--base`

**Files:**
- Modify: `tests/test_cli.py`
- Test: `mpy_cli/cli.py`

**Step 1: Write the failing tests**

```python
def test_plan_incremental_passes_base_ref_to_gitdiff(...):
    ...
    code = main(["plan", "--no-interactive", "--mode", "incremental", "--base", "abc123", "--port", "COM3"])
    assert captured_base_ref["value"] == "abc123"


def test_deploy_incremental_passes_base_ref_to_gitdiff(...):
    ...
    code = main(["deploy", "--no-interactive", "--yes", "--mode", "incremental", "--base", "abc123", "--port", "COM3"])
    assert captured_base_ref["value"] == "abc123"


def test_plan_full_rejects_base_ref(...):
    code = main(["plan", "--no-interactive", "--mode", "full", "--base", "abc123", "--port", "COM3"])
    assert code == 1
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k base_ref`
Expected: FAIL because parser and CLI flow do not support `--base` yet.

**Step 3: Write minimal implementation**

```python
cmd.add_argument("--base", help="增量模式的 Git 基准提交")

if mode == "full" and args.base:
    print("--base 仅支持 incremental 模式")
    return 1

changes = collect_git_changes(source_root, base_ref=args.base or "HEAD")
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k base_ref`
Expected: PASS.

### Task 3: Update gitdiff defaults and keep backward compatibility

**Files:**
- Modify: `mpy_cli/gitdiff.py`
- Test: `tests/test_gitdiff.py`

**Step 1: Add coverage for default behavior**

```python
def test_collect_git_changes_defaults_base_ref_to_head(monkeypatch) -> None:
    ...
    collect_git_changes(Path("/tmp/repo"))
    assert captured[0] == ["diff", "--name-status", "--relative", "HEAD", "--", "."]
```

**Step 2: Run targeted tests**

Run: `python3 -m pytest -q tests/test_gitdiff.py`
Expected: PASS.

### Task 4: Update README and doc assertions

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write failing docs test**

```python
def test_readme_documents_incremental_base_flag() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "--base" in content
    assert "Git 基准提交" in content
```
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k incremental_base_flag`
Expected: FAIL before README update.

**Step 3: Write minimal documentation update**

- Extend `plan` command synopsis with `--base BASE`.
- Extend `deploy` command synopsis with `--base BASE`.
- Add a short note: `--base` only applies to `incremental` mode and compares the specified base to the current workspace.

**Step 4: Run docs tests**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: PASS.

### Task 5: Run focused and full verification

**Files:**
- Test: `tests/test_gitdiff.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_docs_and_ci.py`

**Step 1: Run focused suite**

Run: `python3 -m pytest -q tests/test_gitdiff.py tests/test_cli.py tests/test_docs_and_ci.py`
Expected: PASS.

**Step 2: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS.

**Step 3: Progress update**

Run: follow `@progress-tracker` and record the feature outcome with related commit fields set to `TBD` if no commit is created in this session.
