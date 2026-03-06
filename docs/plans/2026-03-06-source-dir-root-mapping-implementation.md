# Source Dir Root Mapping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `source_dir` map directly to remote root across the repository so `source_dir="src"` uploads `src/main.py` as `main.py` (plus optional `device_upload_dir` prefix), and align `.mpyignore`/interactive defaults to the same path language.

**Architecture:** Keep collecting incremental changes from `source_root`, but treat returned paths as canonical `source-relative` paths without re-prefixing. In scanner, always map remote paths relative to `source_root`. In CLI upload interactive mode, derive default remote from local path relative to `source_root` when possible. Preserve explicit `--remote` and `device_upload_dir` behavior.

**Tech Stack:** Python, pathlib, argparse, pytest.

---

### Task 1: Add failing tests for unified source-relative semantics

**Files:**
- Modify: `tests/test_scanner.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing tests**

```python
def test_list_local_files_uses_source_relative_remote_path_for_relative_source_dir(
    tmp_path: Path,
) -> None:
    project_root = tmp_path
    source_root = project_root / "app_src"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "main.py").write_text("print('ok')\n", encoding="utf-8")

    entries = list_local_files(
        project_root=project_root,
        source_dir="app_src",
        runtime_dir=".mpy-cli",
    )

    assert entries[0].remote_path == "main.py"


def test_deploy_incremental_uses_source_relative_remote_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ...
    assert operation.remote_path == "main.py"


def test_upload_interactive_defaults_remote_to_source_relative_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ...
    assert asked_defaults == ["main.py"]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_scanner.py tests/test_cli.py -k "source_relative"`
Expected: FAIL because scanner/incremental/upload default still preserve `source_dir` prefix.

**Step 3: Commit**

```bash
git add tests/test_scanner.py tests/test_cli.py
git commit -m "test(path): add source-relative mapping regression tests"
```

### Task 2: Implement scanner source-relative mapping

**Files:**
- Modify: `mpy_cli/scanner.py`
- Test: `tests/test_scanner.py`

**Step 1: Write minimal implementation**

```python
def _to_remote_path(file_path: Path, source_root: Path) -> str:
    return file_path.relative_to(source_root).as_posix()
```

- Remove project-root-based remote mapping branch.
- Keep local path collection and ignore directory filtering unchanged.

**Step 2: Run targeted tests**

Run: `python3 -m pytest -q tests/test_scanner.py`
Expected: PASS.

**Step 3: Commit**

```bash
git add mpy_cli/scanner.py tests/test_scanner.py
git commit -m "fix(path): map scanner remote paths from source root"
```

### Task 3: Implement incremental source-relative path flow

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write minimal implementation**

- In `_cmd_plan_or_deploy`, use `collect_git_changes(source_root)` directly.
- Remove `_prefix_change_paths`, `_derive_source_path_prefix`, `_join_source_path_prefix`, `_strip_source_path_prefix` usage from incremental flow.
- Simplify `_resolve_incremental_upload_local_paths` / `_resolve_incremental_local_path` signatures to rely on `source_root` + `local_path` directly.

```python
changes = collect_git_changes(source_root)
resolved_path = (source_root / local_path).resolve()
```

**Step 2: Run targeted tests**

Run: `python3 -m pytest -q tests/test_cli.py -k "incremental or source_relative"`
Expected: PASS.

**Step 3: Commit**

```bash
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "fix(path): keep incremental paths source-relative"
```

### Task 4: Implement upload interactive default alignment

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write minimal implementation**

- Add helper to derive default remote path from `local_path` and `cfg.source_dir`:
  - if local file resolves under `source_root`, return source-relative path;
  - else return original input.
- Use this helper to set `default_remote_path` in `_cmd_upload`.

```python
default_remote_path = _derive_upload_default_remote_path(
    local_path=local_path,
    project_root=Path.cwd().resolve(),
    source_dir=cfg.source_dir,
)
```

**Step 2: Run targeted tests**

Run: `python3 -m pytest -q tests/test_cli.py -k "upload_interactive_defaults_remote_to_source_relative_path"`
Expected: PASS.

**Step 3: Commit**

```bash
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "fix(upload): default interactive remote to source-relative path"
```

### Task 5: Update README and docs assertions

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write failing docs test**

```python
def test_readme_mentions_source_dir_root_mapping() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "source_dir" in content
    assert "相对 source_dir" in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k source_dir_root_mapping`
Expected: FAIL before README update.

**Step 3: Write minimal documentation update**

- In README, add unified semantics for:
  - `source_dir` as local source root,
  - `.mpyignore` matching source-relative paths,
  - migration note when `source_dir != "."`.

**Step 4: Run docs tests**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests/test_docs_and_ci.py
git commit -m "docs(path): document source_dir root mapping semantics"
```

### Task 6: Full verification

**Files:**
- Test: `tests/test_scanner.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_docs_and_ci.py`

**Step 1: Run focused suite**

Run: `python3 -m pytest -q tests/test_scanner.py tests/test_cli.py tests/test_docs_and_ci.py`
Expected: PASS.

**Step 2: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS.

**Step 3: Progress update**

Run: follow `@progress-tracker` if progress memory is enabled.
