# Tree Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `mpy-cli tree` to print a remote directory tree on the MicroPython device, scoped by `device_upload_dir` and optional `--path`.

**Architecture:** Extend CLI command routing with a new read-only `tree` subcommand. Add a backend API that reads exactly one remote directory level and returns typed entries, then build tree output recursively in CLI for deterministic sorting and formatting. Keep existing port/config/error flow unchanged to minimize behavioral risk.

**Tech Stack:** Python 3.10+, argparse, mpremote backend adapter, pytest.

---

### Task 1: Backend typed directory listing API

**Files:**
- Modify: `mpy_cli/backend/mpremote.py`
- Test: `tests/test_mpremote_backend.py`

**Step 1: Write the failing test**

```python
def test_list_dir_parses_typed_entries() -> None:
    called: list[list[str]] = []

    def fake_runner(command, capture_output, text, check):  # noqa: ANN001
        called.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="D\tapps\nF\tmain.py\n",
            stderr="",
        )

    backend = MpremoteBackend(binary="mpremote", runner=fake_runner, resolver=lambda _: "/usr/bin/mpremote")
    entries = backend.list_dir(port="/dev/ttyACM0", remote_path="apps/demo")

    assert called[0][0:5] == ["mpremote", "connect", "/dev/ttyACM0", "resume", "exec"]
    assert [entry.name for entry in entries] == ["apps", "main.py"]
    assert [entry.is_dir for entry in entries] == [True, False]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py::test_list_dir_parses_typed_entries`
Expected: FAIL with missing `list_dir` or related symbol.

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class RemoteDirEntry:
    name: str
    is_dir: bool

def list_dir(self, port: str, remote_path: str) -> list[RemoteDirEntry]:
    cmd = self.build_list_dir_command(port=port, remote=remote_path)
    result = self._run(cmd)
    return _parse_remote_dir_entries(result.stdout)
```

Also add `_build_remote_list_dir_script()` and parser for `D\tname` / `F\tname` lines.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py::test_list_dir_parses_typed_entries`
Expected: PASS.

**Step 5: Commit**

```bash
git add mpy_cli/backend/mpremote.py tests/test_mpremote_backend.py
git commit -m "feat: add typed remote directory listing API"
```

### Task 2: CLI `tree` command routing and execution

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_tree_executes_remote_list_with_device_upload_prefix(...):
    # setup config with device_upload_dir="apps/demo"
    # run main(["tree", "--no-interactive", "--port", "COM3", "--path", "services"])
    # assert backend.list_dir called with "apps/demo/services"
```

Add another test for backend failure returning `2`.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py::test_tree_executes_remote_list_with_device_upload_prefix`
Expected: FAIL because `tree` command does not exist yet.

**Step 3: Write minimal implementation**

```python
tree_parser = subparsers.add_parser("tree", help="读取设备端目录树")
tree_parser.add_argument("--path", help="设备目标目录路径")
tree_parser.add_argument("--port", help="设备串口")
tree_parser.add_argument("--no-interactive", action="store_true", help="禁用 questionary 交互")
```

Implement `_cmd_tree(args)`:
- load config and setup logging
- resolve port (reuse existing function)
- resolve target directory with `_join_upload_target`
- call backend recursively and print tree lines
- map failure to exit code `2`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py::test_tree_executes_remote_list_with_device_upload_prefix tests/test_cli.py::test_tree_returns_failure_code_when_backend_list_fails`
Expected: PASS.

**Step 5: Commit**

```bash
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat: add tree command for remote directory view"
```

### Task 3: Tree output formatting and deterministic order

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_tree_prints_nested_structure_in_tree_style(...):
    # fake backend returns nested entries
    # assert stdout contains ├── / └── / │ formatting and stable order
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py::test_tree_prints_nested_structure_in_tree_style`
Expected: FAIL because output is not formatted yet.

**Step 3: Write minimal implementation**

Implement helper recursion in `cli.py`:

```python
def _render_remote_tree(...):
    # sort: directories first, then by name
    # render with connectors
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py::test_tree_prints_nested_structure_in_tree_style`
Expected: PASS.

**Step 5: Commit**

```bash
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat: format tree command output as hierarchical view"
```

### Task 4: README and docs consistency

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_lists_tree_command_parameters() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli tree", "--path"]:
        assert token in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py::test_readme_lists_tree_command_parameters`
Expected: FAIL because README has no tree section.

**Step 3: Write minimal implementation**

Update README command list and CLI 参数总览 with:

```bash
mpy-cli tree [--path PATH] [--port PORT] [--no-interactive]
```

Include semantics: path is relative to `device_upload_dir`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py::test_readme_lists_tree_command_parameters`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests/test_docs_and_ci.py
git commit -m "docs: document tree command parameters"
```

### Task 5: Verification sweep

**Files:**
- No code changes required unless failures appear.

**Step 1: Run focused suites**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py tests/test_cli.py tests/test_docs_and_ci.py`
Expected: PASS.

**Step 2: Run full suite**

Run: `python3 -m pytest -q`
Expected: PASS.

**Step 3: Optional syntax check**

Run: `python3 -m compileall mpy_cli`
Expected: No syntax errors.

**Step 4: Final diff review**

Run:

```bash
git status
git diff -- mpy_cli/cli.py mpy_cli/backend/mpremote.py tests/test_cli.py tests/test_mpremote_backend.py tests/test_docs_and_ci.py README.md
```

Expected: Only intended files changed.
