# Run Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `mpy-cli run` to execute an existing file on the MicroPython device using a path relative to `device_upload_dir`.

**Architecture:** Extend CLI routing with a dedicated `run` subcommand that reuses existing config loading, port resolution, confirmation flow, and remote-path joining logic. Add backend support in `MpremoteBackend` to execute a remote file via `mpremote ... exec` with a robust path-resolution script on the device side.

**Tech Stack:** Python, argparse, pathlib, mpremote, pytest.

---

### Task 1: Add backend run command builder and executor

**Files:**
- Modify: `mpy_cli/backend/mpremote.py`
- Test: `tests/test_mpremote_backend.py`

**Step 1: Write the failing tests**

```python
def test_run_builds_expected_command() -> None:
    backend = MpremoteBackend(binary="mpremote")

    cmd = backend.build_run_command(port="/dev/ttyACM0", remote="apps/demo/main.py")

    assert cmd[0:4] == ["mpremote", "connect", "/dev/ttyACM0", "resume"]
    assert cmd[4] == "exec"
    assert "apps/demo/main.py" in cmd[5]


def test_run_file_invokes_exec_command() -> None:
    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok\n",
            stderr="",
        )

    backend = MpremoteBackend(
        binary="mpremote",
        runner=fake_runner,
        resolver=lambda _: "/usr/bin/mpremote",
    )

    backend.run_file(port="/dev/ttyACM0", remote_path="apps/demo/main.py")

    assert called
    assert called[0][0:5] == ["mpremote", "connect", "/dev/ttyACM0", "resume", "exec"]
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k run`
Expected: FAIL because `build_run_command/run_file` do not exist.

**Step 3: Write minimal implementation**

Implement `build_run_command()` and `run_file()` in `MpremoteBackend`.

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k run`
Expected: PASS.

### Task 2: Add CLI `run` subcommand routing and argument parsing

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_run_non_interactive_requires_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])

    code = main(["run", "--no-interactive", "--port", "COM3", "--yes"])

    assert code == 1
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k run_non_interactive_requires_path`
Expected: FAIL because parser does not include `run`.

**Step 3: Write minimal implementation**

Add parser entry and command dispatch for `run`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k run_non_interactive_requires_path`
Expected: PASS.

### Task 3: Implement `_cmd_run` flow with path join, confirmation, and execution

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing tests**

```python
def test_run_executes_remote_file_with_device_upload_prefix(tmp_path: Path, monkeypatch) -> None:
    ...


def test_run_returns_failure_code_when_backend_run_fails(tmp_path: Path, monkeypatch) -> None:
    ...
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_cli.py -k "run_executes_remote_file or run_returns_failure_code"`
Expected: FAIL because `_cmd_run` is not implemented.

**Step 3: Write minimal implementation**

Implement `_cmd_run()` in `cli.py`:
- load config
- resolve port
- resolve/validate path input
- compute final remote path via `_join_upload_target`
- preview + confirmation
- `backend.ensure_available()` and `backend.run_file(...)`
- return code `0/1/2` per design

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_cli.py -k "run_executes_remote_file or run_returns_failure_code or run_non_interactive_requires_path"`
Expected: PASS.

### Task 4: Update README and docs consistency tests

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_lists_run_command_parameters() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli run", "--path"]:
        assert token in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k run`
Expected: FAIL.

**Step 3: Write minimal implementation**

Add `run` command section to README and include `--path` semantics relative to `device_upload_dir`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k run`
Expected: PASS.

### Task 5: Regression verification

**Files:**
- Test: `tests/test_cli.py`
- Test: `tests/test_mpremote_backend.py`
- Test: `tests/test_docs_and_ci.py`
- Test: `tests/test_executor.py`

**Step 1: Run focused suites**

Run: `python3 -m pytest -q tests/test_cli.py tests/test_mpremote_backend.py tests/test_docs_and_ci.py`
Expected: PASS.

**Step 2: Run full regression**

Run: `python3 -m pytest -q`
Expected: PASS with no new failures.
