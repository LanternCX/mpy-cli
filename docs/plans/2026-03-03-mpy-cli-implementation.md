# mpy-cli MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-ready MVP of `mpy-cli` that supports interactive deployment to MicroPython devices with `.mpyignore`, `full`/`incremental` sync modes, runtime-local persistence, and CI release automation.

**Architecture:** Implement modular layers (`config`, `ignore`, `gitdiff`, `planner`, `backend`, `executor`, `cli`) with strict TDD. Keep device I/O isolated in an `mpremote` adapter and keep planning logic pure/testable. Persist all runtime state under project-local `.mpy-cli/` and use dual-channel logging (`rich` console + rotating file).

**Tech Stack:** Python 3.11+, pytest, questionary, rich, GitHub Actions.

---

### Task 1: Bootstrap Python Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `mpy_cli/__init__.py`
- Create: `mpy_cli/__main__.py`
- Create: `tests/test_bootstrap.py`
- Test: `tests/test_bootstrap.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_package_has_version() -> None:
    from mpy_cli import __version__
    assert isinstance(__version__, str)
    assert __version__


def test_module_entrypoint_exists() -> None:
    assert Path("mpy_cli/__main__.py").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bootstrap.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing files.

**Step 3: Write minimal implementation**

```python
# mpy_cli/__init__.py
"""mpy-cli package."""

__version__ = "0.1.0"

# mpy_cli/__main__.py
from mpy_cli.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bootstrap.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add pyproject.toml README.md mpy_cli/__init__.py mpy_cli/__main__.py tests/test_bootstrap.py
git commit -m "feat(core): bootstrap python package and test harness" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 2: Implement Configuration and Runtime Layout

**Files:**
- Create: `mpy_cli/config.py`
- Create: `mpy_cli/runtime.py`
- Create: `tests/test_config.py`
- Create: `tests/test_runtime.py`
- Modify: `mpy_cli/__init__.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from mpy_cli.config import SyncConfig, load_config, init_config
from mpy_cli.runtime import ensure_runtime_layout


def test_init_config_creates_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / ".mpy-cli.toml"
    init_config(config_path)
    cfg = load_config(config_path)
    assert cfg.sync.mode == "incremental"
    assert cfg.ignore_file == ".mpyignore"


def test_runtime_layout_uses_project_dir(tmp_path: Path) -> None:
    runtime_dir = tmp_path / ".mpy-cli"
    ensure_runtime_layout(runtime_dir)
    assert (runtime_dir / "logs").exists()
    assert (runtime_dir / "data" / "runtime.db").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py tests/test_runtime.py -v`
Expected: FAIL with missing module/functions.

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class SyncConfig:
    mode: Literal["full", "incremental"] = "incremental"


@dataclass(frozen=True)
class AppConfig:
    serial_port: str | None
    ignore_file: str
    runtime_dir: str
    sync: SyncConfig
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py tests/test_runtime.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add mpy_cli/config.py mpy_cli/runtime.py tests/test_config.py tests/test_runtime.py mpy_cli/__init__.py
git commit -m "feat(config): add project-local runtime and config loader" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 3: Implement .mpyignore Matching

**Files:**
- Create: `mpy_cli/ignore.py`
- Create: `tests/test_ignore.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from mpy_cli.ignore import IgnoreMatcher


def test_ignore_and_unignore_rules(tmp_path: Path) -> None:
    ignore_file = tmp_path / ".mpyignore"
    ignore_file.write_text("*.pyc\n!important.pyc\n", encoding="utf-8")
    matcher = IgnoreMatcher.from_file(ignore_file)
    assert matcher.is_ignored("foo.pyc")
    assert not matcher.is_ignored("important.pyc")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ignore.py -v`
Expected: FAIL with missing `IgnoreMatcher`.

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class Rule:
    pattern: str
    negated: bool


class IgnoreMatcher:
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ignore.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add mpy_cli/ignore.py tests/test_ignore.py
git commit -m "feat(sync): support mpyignore include and exclude rules" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 4: Implement Git Diff Parser

**Files:**
- Create: `mpy_cli/gitdiff.py`
- Create: `tests/test_gitdiff.py`

**Step 1: Write the failing test**

```python
from mpy_cli.gitdiff import parse_name_status_line


def test_parse_rename_line() -> None:
    entry = parse_name_status_line("R100\told.py\tnew.py")
    assert entry.status == "R"
    assert entry.src_path == "old.py"
    assert entry.dst_path == "new.py"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_gitdiff.py -v`
Expected: FAIL with missing parser.

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class ChangeEntry:
    status: str
    src_path: str | None
    dst_path: str
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_gitdiff.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add mpy_cli/gitdiff.py tests/test_gitdiff.py
git commit -m "feat(sync): parse git diff changes for incremental deploy" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 5: Implement Deployment Planner

**Files:**
- Create: `mpy_cli/planner.py`
- Create: `tests/test_planner.py`

**Step 1: Write the failing test**

```python
from mpy_cli.planner import build_plan


def test_full_mode_includes_wipe_first() -> None:
    plan = build_plan(mode="full", files=["main.py"], changes=[])
    assert plan.operations[0].op_type == "wipe"
    assert plan.operations[1].op_type == "upload"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_planner.py -v`
Expected: FAIL with missing planner.

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class PlanOperation:
    op_type: Literal["wipe", "upload", "delete"]
    local_path: str | None
    remote_path: str | None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_planner.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add mpy_cli/planner.py tests/test_planner.py
git commit -m "feat(sync): add full and incremental deployment planner" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 6: Implement mpremote Backend and Executor

**Files:**
- Create: `mpy_cli/backend/__init__.py`
- Create: `mpy_cli/backend/mpremote.py`
- Create: `mpy_cli/executor.py`
- Create: `tests/test_mpremote_backend.py`
- Create: `tests/test_executor.py`

**Step 1: Write the failing test**

```python
from mpy_cli.backend.mpremote import MpremoteBackend


def test_upload_builds_expected_command() -> None:
    backend = MpremoteBackend(binary="mpremote")
    cmd = backend.build_upload_command(port="/dev/ttyACM0", local="main.py", remote="main.py")
    assert cmd == ["mpremote", "connect", "/dev/ttyACM0", "fs", "cp", "main.py", ":main.py"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mpremote_backend.py tests/test_executor.py -v`
Expected: FAIL with missing backend/executor.

**Step 3: Write minimal implementation**

```python
class MpremoteBackend:
    def build_upload_command(self, port: str, local: str, remote: str) -> list[str]:
        return [self.binary, "connect", port, "fs", "cp", local, f":{remote}"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_mpremote_backend.py tests/test_executor.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add mpy_cli/backend/__init__.py mpy_cli/backend/mpremote.py mpy_cli/executor.py tests/test_mpremote_backend.py tests/test_executor.py
git commit -m "feat(device): add mpremote backend and plan executor" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 7: Build Interactive CLI and Logging

**Files:**
- Create: `mpy_cli/logging.py`
- Create: `mpy_cli/cli.py`
- Create: `tests/test_cli.py`
- Modify: `mpy_cli/__main__.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from mpy_cli.cli import main


def test_init_command_creates_config_and_ignore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    code = main(["init"])
    assert code == 0
    assert (tmp_path / ".mpy-cli.toml").exists()
    assert (tmp_path / ".mpyignore").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with missing CLI implementation.

**Step 3: Write minimal implementation**

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add mpy_cli/logging.py mpy_cli/cli.py tests/test_cli.py mpy_cli/__main__.py
git commit -m "feat(cli): add interactive init plan deploy commands" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 8: Add Documentation, CI, and Cross-Platform Release Packaging

**Files:**
- Modify: `README.md`
- Create: `docs/user-guide.md`
- Create: `docs/developer-guide.md`
- Create: `docs/deployment.md`
- Create: `.github/workflows/release.yml`
- Create: `scripts/build_release.py`
- Create: `assets/default-config.toml`
- Create: `assets/runtime.db`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_release_workflow_exists() -> None:
    assert Path(".github/workflows/release.yml").exists()


def test_docs_are_split_user_and_developer() -> None:
    assert Path("docs/user-guide.md").exists()
    assert Path("docs/developer-guide.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs_and_ci.py -v`
Expected: FAIL with missing files.

**Step 3: Write minimal implementation**

```yaml
on:
  push:
    tags:
      - "v*"
```

**Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: PASS.

**Step 5: Commit**

```bash
# 必须先向用户出具提交确认单，再执行 commit
git add README.md docs/user-guide.md docs/developer-guide.md docs/deployment.md .github/workflows/release.yml scripts/build_release.py assets/default-config.toml assets/runtime.db tests/test_docs_and_ci.py
git commit -m "feat(release): add docs split and tag-based release workflow" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```
