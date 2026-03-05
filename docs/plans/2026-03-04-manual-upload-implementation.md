# Manual Upload Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `mpy-cli upload` for interactive single-file upload with editable remote path and pre-execution confirmation.

**Architecture:** Extend CLI command routing with a dedicated `upload` subcommand and reuse existing port resolution, backend availability checks, and `DeployExecutor` execution path. Build a one-operation `DeployPlan` (`upload`) so logging and failure reporting stay consistent with existing deploy flow.

**Tech Stack:** Python, argparse, questionary, pathlib, pytest, mpremote.

---

### Task 1: Add CLI command shape for `upload`

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_upload_command_is_parsed_by_main(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    main(["init", "--no-interactive"])
    code = main(["upload", "--no-interactive"])
    assert code == 1
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k upload_command_is_parsed_by_main`
Expected: FAIL because parser does not know `upload`.

**Step 3: Write minimal implementation**

```python
if args.command == "upload":
    return _cmd_upload(args)

upload_parser = subparsers.add_parser("upload", help="单文件上传")
upload_parser.add_argument("--local", help="本地文件路径")
upload_parser.add_argument("--remote", help="设备目标路径")
upload_parser.add_argument("--port", help="设备串口")
upload_parser.add_argument("--yes", action="store_true", help="跳过执行前确认")
upload_parser.add_argument("--no-interactive", action="store_true", help="禁用交互")
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k upload_command_is_parsed_by_main`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat(cli): add upload command entrypoint" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 2: Implement input resolution and validation for single-file upload

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_upload_interactive_remote_defaults_to_local(monkeypatch, tmp_path):
    ...

def test_upload_rejects_missing_local_file(monkeypatch, tmp_path):
    ...

def test_upload_non_interactive_requires_arguments(monkeypatch, tmp_path):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k "upload_interactive or upload_rejects or upload_non_interactive"`
Expected: FAIL because `_cmd_upload` validation/interaction is missing.

**Step 3: Write minimal implementation**

```python
local = args.local or _ask_text("请输入本地文件路径")
default_remote = args.remote or local
remote = args.remote or _ask_text("请输入设备目标路径", default=default_remote)

if not Path(local).is_file():
    print("本地文件不存在或不是文件")
    return 1
if not remote.strip():
    print("目标路径不能为空")
    return 1
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k "upload_interactive or upload_rejects or upload_non_interactive"`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat(cli): validate upload local and remote paths" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 3: Reuse deploy executor for upload execution and confirmation

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_upload_executes_single_upload_operation(monkeypatch, tmp_path):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k upload_executes_single_upload_operation`
Expected: FAIL because upload execution path is incomplete.

**Step 3: Write minimal implementation**

```python
plan = DeployPlan(
    mode="incremental",
    operations=[
        PlanOperation(
            op_type="upload",
            local_path=local_path,
            remote_path=_join_remote_path(cfg.device_upload_dir, remote_path),
            reason="manual-upload",
        )
    ],
)
report = DeployExecutor(backend=backend, logger=logger).execute(plan=plan, port=port)
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k upload_executes_single_upload_operation`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat(cli): execute manual single-file upload via deploy executor" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 4: Update docs and coverage checks

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_lists_upload_command_parameters() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["mpy-cli upload", "--local", "--remote"]:
        assert token in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k upload`
Expected: FAIL until README and checklist tokens are updated.

**Step 3: Write minimal implementation**

```markdown
### `mpy-cli upload`

mpy-cli upload [--local LOCAL] [--remote REMOTE] [--port PORT] [--no-interactive] [--yes]
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add README.md tests/test_docs_and_ci.py docs/plans/2026-03-04-manual-upload-design.md docs/plans/2026-03-04-manual-upload-implementation.md
git commit -m "docs(cli): document manual single-file upload command" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 5: Regression verification

**Files:**
- Test: `tests/test_cli.py`
- Test: `tests/test_docs_and_ci.py`
- Test: `tests/test_executor.py`
- Test: `tests/test_mpremote_backend.py`

**Step 1: Run focused suites first**

Run: `python3 -m pytest -q tests/test_cli.py tests/test_docs_and_ci.py`
Expected: PASS.

**Step 2: Run deployment-adjacent suites**

Run: `python3 -m pytest -q tests/test_executor.py tests/test_mpremote_backend.py`
Expected: PASS.

**Step 3: Run full regression**

Run: `python3 -m pytest -q`
Expected: PASS with no new failures.

**Step 4: Commit (if pending files exist)**

```bash
# 先向用户确认后再 commit
git add README.md mpy_cli/cli.py tests/test_cli.py tests/test_docs_and_ci.py
git commit -m "test(cli): cover manual upload command flow"
```
