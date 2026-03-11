# CLI Short Options Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a single-character short-option synonym for every existing CLI argument while keeping all current long-option behavior unchanged.

**Architecture:** Update `argparse` definitions in `mpy_cli/cli.py` so each `add_argument()` accepts both short and long forms. Resolve collisions only within each subcommand, preserving intuitive shared aliases like `-p` for `--port` across different commands. Back the change with parser-focused regression tests plus README synchronization updates.

**Tech Stack:** Python 3.10+, argparse, pytest, Markdown docs.

---

### Task 1: Add a failing parser test for representative short options

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `mpy_cli/cli.py`

**Step 1: Write the failing test**

```python
def test_plan_command_accepts_short_options() -> None:
    parser = build_parser()

    args = parser.parse_args(["plan", "-m", "full", "-b", "HEAD~1", "-p", "COM3", "-n", "-y"])

    assert args.command == "plan"
    assert args.mode == "full"
    assert args.base == "HEAD~1"
    assert args.port == "COM3"
    assert args.no_interactive is True
    assert args.yes is True
```

Add similar focused tests for `list`, `upload`, and one collision case such as `tree -a`.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k short_options`
Expected: FAIL because the parser does not accept the new short flags yet.

**Step 3: Write minimal implementation**

```python
cmd.add_argument("-m", "--mode", choices=["full", "incremental"], help="同步模式")
cmd.add_argument("-b", "--base", help="增量模式的 Git 基准提交")
cmd.add_argument("-p", "--port", help="设备串口，例如 /dev/ttyACM0")
cmd.add_argument("-y", "--yes", action="store_true", help="跳过交互确认")
cmd.add_argument("-n", "--no-interactive", action="store_true", help="禁用 questionary 交互")
```

Repeat for every existing command argument, using the approved mapping.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k short_options`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_cli.py mpy_cli/cli.py
git commit -m "feat(cli): add short options for command arguments"
```

### Task 2: Cover all subcommand-specific mappings and collision choices

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `mpy_cli/cli.py`

**Step 1: Write the failing test**

```python
def test_tree_command_accepts_path_short_option_a() -> None:
    parser = build_parser()

    args = parser.parse_args(["tree", "-a", "lib", "-p", "COM3", "-n"])

    assert args.path == "lib"
    assert args.port == "COM3"
    assert args.no_interactive is True
```

Add complementary assertions for:
- `init -f -n`
- `list -w 4 -t 1.5 -s full-only -r`
- `upload -l main.py -r :main.py -p COM3 -n -y`
- `run -f boot.py -p COM3 -n -y`
- `delete -f old.py -p COM3 -n -y`

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k "short_options or tree_command_accepts_path_short_option_a"`
Expected: FAIL on unmapped or conflicting short options.

**Step 3: Write minimal implementation**

Apply the full approved mapping in `build_parser()`:

```python
init:   -f/--force, -n/--no-interactive
list:   -w/--workers, -t/--probe-timeout, -s/--scan-mode, -r/--reset
plan:   -m/--mode, -b/--base, -p/--port, -y/--yes, -n/--no-interactive
deploy: -m/--mode, -b/--base, -p/--port, -y/--yes, -n/--no-interactive
upload: -l/--local, -r/--remote, -p/--port, -y/--yes, -n/--no-interactive
run:    -f/--path, -p/--port, -y/--yes, -n/--no-interactive
delete: -f/--path, -p/--port, -y/--yes, -n/--no-interactive
tree:   -a/--path, -p/--port, -n/--no-interactive
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k short_options`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_cli.py mpy_cli/cli.py
git commit -m "test(cli): cover short option aliases across subcommands"
```

### Task 3: Update README parameter reference and examples

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_documents_cli_short_options() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    assert "mpy-cli plan [-m|--mode {incremental,full}]" in content
    assert "mpy-cli list [-w|--workers N]" in content
    assert "mpy-cli tree [-a|--path PATH] [-p|--port PORT] [-n|--no-interactive]" in content
```

If there is already a docs synchronization test, extend it rather than duplicating coverage.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: FAIL because README still shows only long options.

**Step 3: Write minimal implementation**

Update README command synopsis and representative examples so users can discover the new aliases without removing long-form examples.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests/test_docs_and_ci.py
git commit -m "docs(cli): document short option aliases"
```

### Task 4: Verification sweep

**Files:**
- No intended code changes.

**Step 1: Run focused suites**

Run: `python3 -m pytest -q tests/test_cli.py tests/test_docs_and_ci.py`
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
git diff -- mpy_cli/cli.py tests/test_cli.py tests/test_docs_and_ci.py README.md docs/plans/2026-03-11-cli-short-options-design.md docs/plans/2026-03-11-cli-short-options-implementation.md
```

Expected: Only intended CLI, tests, README, and plan/design files changed.
