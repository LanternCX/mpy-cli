# Port Scan Selection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add interactive port auto-scan and selection for `plan/deploy` when `--port` is not provided.

**Architecture:** Keep scanning logic in `mpremote` backend and reuse CLI interaction helpers for selection. Port resolution priority remains CLI arg > config > interactive scan > manual input. Non-interactive mode remains strict and never auto-selects a port.

**Tech Stack:** Python, questionary, pytest, mpremote.

---

### Task 1: Add mpremote port listing and parser

**Files:**
- Modify: `mpy_cli/backend/mpremote.py`
- Test: `tests/test_mpremote_backend.py`

**Step 1: Write the failing test**

```python
def test_parse_port_list_output() -> None:
    output = """/dev/ttyACM0 1234\n/dev/ttyUSB0 5678\n"""
    ports = parse_port_list_output(output)
    assert ports == ["/dev/ttyACM0", "/dev/ttyUSB0"]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k port`
Expected: FAIL with missing parser/list method.

**Step 3: Write minimal implementation**

```python
def parse_port_list_output(output: str) -> list[str]:
    ...

class MpremoteBackend:
    def list_ports(self) -> list[str]:
        ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k port`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add mpy_cli/backend/mpremote.py tests/test_mpremote_backend.py
git commit -m "feat(cli): add mpremote port scan support" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 2: Wire interactive port resolution in CLI

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_resolve_port_scans_in_interactive(monkeypatch):
    ...

def test_resolve_port_keeps_non_interactive_strict(monkeypatch):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k port`
Expected: FAIL with missing resolution function/behavior.

**Step 3: Write minimal implementation**

```python
def _resolve_port(...):
    ...

def _scan_and_select_port(...):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k port`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat(cli): auto-scan and select device port in interactive mode" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 3: Update README and run regression tests

**Files:**
- Modify: `README.md`
- Test: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_auto_port_scan() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k port`
Expected: FAIL until README includes behavior.

**Step 3: Write minimal implementation**

```markdown
未提供 --port 且为交互模式时，工具会先自动扫描设备端口并让你选择。
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: PASS.

**Step 5: Commit**

```bash
# 先向用户确认后再 commit
git add README.md tests/test_docs_and_ci.py docs/plans/2026-03-03-port-scan-design.md docs/plans/2026-03-03-port-scan-implementation.md
git commit -m "docs: describe interactive port auto-scan behavior" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```
