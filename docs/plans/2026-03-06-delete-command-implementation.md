# Delete Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `mpy-cli delete` so users can delete a single file or recursively delete a directory on the MicroPython device with a path relative to `device_upload_dir`.

**Architecture:** Extend CLI routing with a dedicated `delete` subcommand that mirrors `run` command UX (`--path`, preview, confirmation, `--no-interactive`, `--yes`). In backend, add a new `mpremote ... resume exec` delete script path to handle both file and directory deletion in one flow, while keeping existing `delete_file()` behavior unchanged for deploy incremental operations.

**Tech Stack:** Python, argparse, pathlib, mpremote, pytest.

---

### Task 1: Add backend recursive delete command support

**Files:**
- Modify: `mpy_cli/backend/mpremote.py`
- Test: `tests/test_mpremote_backend.py`

**Step 1: Write the failing tests**

```python
def test_delete_tree_builds_expected_command() -> None:
    """@brief delete tree 命令应构建为 mpremote resume exec 调用。"""

    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_delete_tree_command(
        port="/dev/ttyACM0",
        remote="apps/demo",
    )

    assert cmd[0:4] == ["mpremote", "connect", "/dev/ttyACM0", "resume"]
    assert cmd[4] == "exec"
    assert "apps/demo" in cmd[5]


def test_delete_path_invokes_exec_command() -> None:
    """@brief delete_path 应调用 exec 命令执行删除。"""

    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    backend.delete_path(port="/dev/ttyACM0", remote_path="apps/demo")

    assert called
    assert called[0][0:5] == ["mpremote", "connect", "/dev/ttyACM0", "resume", "exec"]
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k "delete_tree or delete_path_invokes_exec"`
Expected: FAIL because `build_delete_tree_command()` and `delete_path()` do not exist.

**Step 3: Write minimal implementation**

- In `mpy_cli/backend/mpremote.py`, add:
  - `build_delete_tree_command(port: str, remote: str) -> list[str]`
  - `delete_path(port: str, remote_path: str) -> CommandResult`
  - internal helper script builder (for example `_build_remote_delete_script`) that:
    - normalizes target path,
    - resolves candidate absolute paths (`/<path>`, `/flash/<path>` when applicable),
    - deletes file directly or recursively deletes directory contents then directory itself,
    - raises clear `OSError` when path not found.
- Keep existing `build_delete_command()` / `delete_file()` unchanged for deploy flow.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k "delete_tree or delete_path_invokes_exec"`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_mpremote_backend.py mpy_cli/backend/mpremote.py
git commit -m "feat(delete): add backend recursive delete path support"
```

### Task 2: Add CLI delete command parsing and command routing

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_delete_non_interactive_requires_path(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    """@brief delete 非交互模式缺少 path 参数时应报错。"""

    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    code = main(["delete", "--no-interactive", "--port", "COM3", "--yes"])

    assert code == 1
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k delete_non_interactive_requires_path`
Expected: FAIL because parser does not include `delete`.

**Step 3: Write minimal implementation**

- In `build_parser()`, add `delete` parser with flags: `--path`, `--port`, `--yes`, `--no-interactive`.
- In `main()`, add dispatch branch for `args.command == "delete"`.
- Add `_cmd_delete(args: argparse.Namespace) -> int` skeleton using same config + port resolution flow as `run`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k delete_non_interactive_requires_path`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_cli.py mpy_cli/cli.py
git commit -m "feat(delete): add CLI delete command parsing"
```

### Task 3: Implement delete execution flow in CLI

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing tests**

```python
def test_delete_executes_remote_path_with_device_upload_prefix(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief delete 应按 device_upload_dir 拼接设备目标路径。"""
    ...


def test_delete_returns_failure_code_when_backend_delete_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:  # noqa: ANN001
    """@brief delete 执行失败时应返回失败退出码。"""
    ...
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_cli.py -k "delete_executes_remote_path or delete_returns_failure_code"`
Expected: FAIL because `_cmd_delete` has no full behavior.

**Step 3: Write minimal implementation**

In `_cmd_delete()` implement:
- load config and runtime logger,
- resolve port via `_resolve_port()`,
- resolve `--path` (prompt in interactive mode),
- compute final remote path via `_join_upload_target(cfg.device_upload_dir, target_path)`,
- print delete preview and confirm (skip with `--yes`),
- call `backend.ensure_available()` then `backend.delete_path(port=port, remote_path=final_remote_path)`,
- return `0/1/2` based on success, user cancellation, or backend failure.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_cli.py -k "delete_non_interactive_requires_path or delete_executes_remote_path or delete_returns_failure_code"`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_cli.py mpy_cli/cli.py
git commit -m "feat(delete): implement delete command execution flow"
```

### Task 4: Update README and docs consistency tests

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_lists_delete_command_parameters() -> None:
    """@brief README 应包含 delete 命令及参数说明。"""

    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli delete", "--path"]:
        assert token in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k delete`
Expected: FAIL because README does not include delete section.

**Step 3: Write minimal implementation**

- Add `mpy-cli delete` to README command list and CLI parameter overview.
- Document that `--path` is relative to `device_upload_dir` and directory targets are recursively deleted.
- Ensure `tests/test_docs_and_ci.py::test_readme_lists_all_cli_parameters` token list includes `mpy-cli delete`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k delete`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests/test_docs_and_ci.py
git commit -m "docs(delete): document delete command and parameters"
```

### Task 5: Regression verification

**Files:**
- Test: `tests/test_cli.py`
- Test: `tests/test_mpremote_backend.py`
- Test: `tests/test_docs_and_ci.py`

**Step 1: Run focused suites**

Run: `python3 -m pytest -q tests/test_cli.py tests/test_mpremote_backend.py tests/test_docs_and_ci.py`
Expected: PASS.

**Step 2: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS with no new failures.

**Step 3: Commit final integration checkpoint**

```bash
git add mpy_cli/cli.py mpy_cli/backend/mpremote.py tests/test_cli.py tests/test_mpremote_backend.py tests/test_docs_and_ci.py README.md
git commit -m "feat(delete): add manual remote delete command for file and directory"
```

### Task 6: Progress note and code review handoff

**Files:**
- Modify: `.progress` artifacts if enabled in current workspace.

**Step 1: Record progress note**

Run: follow `@progress-tracker` if the repository uses progress memory.
Expected: latest implementation summary is recorded.

**Step 2: Request review before merge**

Run: follow `@requesting-code-review` to validate behavior and docs consistency.
Expected: no unresolved high-severity review items.
