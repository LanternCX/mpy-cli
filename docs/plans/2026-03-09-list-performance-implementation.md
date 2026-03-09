# List Command Performance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Speed up `mpy-cli list` on machines with many mixed serial ports by caching only the last scan's successful ports, probing those known-and-current ports first, and providing a reset option for prior scan records.

**Architecture:** Extend the runtime database with a `scanned_ports` table storing seen port names and a `last_success_at` marker used as the last-success snapshot. Keep current port discovery in `MpremoteBackend.list_ports()`, but let CLI orchestrate `known-first` / `known-only` / `full-only` behavior by intersecting last-success ports with the current `connect list` result. Add `--reset-scan-records` so users can clear scan history before re-running `list`.

**Tech Stack:** Python 3.10+, argparse, sqlite3, concurrent.futures, subprocess timeout support, logging, pytest.

---

### Task 1: Runtime DB support for cached scanned ports

**Files:**
- Modify: `mpy_cli/runtime.py`
- Test: `tests/test_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_layout_creates_scanned_ports_table(tmp_path: Path) -> None:
    paths = ensure_runtime_layout(tmp_path / ".mpy-cli")
    assert list_scanned_ports(paths.db_path) == []
```

Also add tests for `clear_scan_records()` and for replacing the previous success snapshot with the latest successful ports.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_runtime.py`
Expected: FAIL because `scanned_ports` table and helper functions do not exist yet.

**Step 3: Write minimal implementation**

Add the `scanned_ports` table in runtime initialization and implement `list_scanned_ports()` / `upsert_scanned_ports()` / `clear_scan_records()` / success-snapshot helpers.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_runtime.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add mpy_cli/runtime.py tests/test_runtime.py
git commit -m "feat: persist scanned ports in runtime db"
```

### Task 2: Backend probing for explicit port lists

**Files:**
- Modify: `mpy_cli/backend/mpremote.py`
- Test: `tests/test_mpremote_backend.py`

**Step 1: Write the failing test**

```python
def test_list_devices_returns_all_successfully_probed_devices() -> None:
    backend = MpremoteBackend(...)
    devices = backend.list_devices(ports=["/dev/ttyACM0", "COM3"], workers=4, probe_timeout=0.5)
    assert [device.port for device in devices] == ["/dev/ttyACM0", "COM3"]
```

Also keep tests for timeout/failure logging on explicit port lists.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k "list_devices"`
Expected: FAIL because `list_devices()` cannot yet probe a caller-provided port list.

**Step 3: Write minimal implementation**

Keep concurrent probing and timeout handling, but refactor `list_devices()` to accept optional `ports` so CLI can decide known-first vs full probe candidates.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_mpremote_backend.py -k "list_devices"`
Expected: PASS.

**Step 5: Commit**

```bash
git add mpy_cli/backend/mpremote.py tests/test_mpremote_backend.py
git commit -m "refactor: allow list backend to probe selected ports"
```

### Task 3: CLI cached-port scan modes

**Files:**
- Modify: `mpy_cli/cli.py`
- Modify: `mpy_cli/runtime.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_list_command_known_first_probes_known_available_ports_before_full_scan(...):
    # cached ports: ["COM3", "COM9"]
    # current ports: ["COM3", "COM7"]
    # first probe should use ["COM3"]
    # if no device found, second probe should use ["COM3", "COM7"]
```

Add parser/forwarding tests for `--scan-mode` and `--reset-scan-records`.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k "scan_mode or known_first"`
Expected: FAIL because CLI has no reset flag and does not yet use last-success-only cache semantics.

**Step 3: Write minimal implementation**

Add `--scan-mode` and `--reset-scan-records` to the parser. In `_cmd_list(args)`:
- optionally clear prior scan records
- read cached ports from runtime DB
- call `backend.list_ports()` once to get current available ports
- upsert current ports into DB
- compute last-success/current intersection
- orchestrate `known-first`, `known-only`, and `full-only`
- overwrite the success snapshot with this run's successful ports
- pass selected candidate ports into `backend.list_devices(...)`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k "scan_mode or known_first or workers or probe_timeout"`
Expected: PASS.

**Step 5: Commit**

```bash
git add mpy_cli/cli.py mpy_cli/runtime.py tests/test_cli.py
git commit -m "feat: add cached-port scan modes for list command"
```

### Task 4: README and docs consistency

**Files:**
- Modify: `README.md`
- Test: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_lists_list_command_performance_parameters() -> None:
    content = Path("README.md").read_text(encoding="utf-8")
    for token in ["--workers", "--probe-timeout", "--scan-mode", "known-first", "--reset-scan-records"]:
        assert token in content
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k "performance_parameters"`
Expected: FAIL because README lacks cached-port behavior and `--scan-mode`.

**Step 3: Write minimal implementation**

Document last-success-only cache behavior, reset semantics, fallback full scan, Windows compatibility through current-port intersection, and the new flags.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k "performance_parameters"`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests/test_docs_and_ci.py
git commit -m "docs: document cached-port list scanning behavior"
```

### Task 5: Verification sweep

**Files:**
- No code changes required unless failures appear.

**Step 1: Run focused suites**

Run: `python3 -m pytest -q tests/test_runtime.py tests/test_cli.py tests/test_mpremote_backend.py tests/test_docs_and_ci.py`
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
git diff -- mpy_cli/cli.py mpy_cli/backend/mpremote.py mpy_cli/runtime.py tests/test_runtime.py tests/test_cli.py tests/test_mpremote_backend.py tests/test_docs_and_ci.py README.md docs/plans/2026-03-09-list-performance-design.md docs/plans/2026-03-09-list-performance-implementation.md
```

Expected: Only intended files changed.
