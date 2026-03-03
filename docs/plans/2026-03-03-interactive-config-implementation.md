# Interactive Config Wizard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide fully interactive configuration via `mpy-cli init` and `mpy-cli config` so users do not need to manually edit `.mpy-cli.toml`.

**Architecture:** Add a dedicated config wizard module for prompts and defaults, add config persistence functions in `config.py`, and wire CLI commands (`init` and new `config`) to use the wizard. Keep command-line overrides unchanged.

**Tech Stack:** Python, questionary, pytest.

---

### Task 1: Add config persistence API

**Files:**
- Modify: `mpy_cli/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

```python
def test_save_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / ".mpy-cli.toml"
    cfg = AppConfig(...)
    save_config(config_path, cfg)
    loaded = load_config(config_path)
    assert loaded == cfg
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_config.py -k save`
Expected: FAIL with missing save API.

**Step 3: Write minimal implementation**

```python
def default_config() -> AppConfig:
    ...

def save_config(config_path: Path, cfg: AppConfig) -> None:
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_config.py -k save`
Expected: PASS.

**Step 5: Commit**

```bash
# commit 前需先向用户确认
git add mpy_cli/config.py tests/test_config.py
git commit -m "feat(config): add config save and defaults api" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 2: Add interactive wizard module

**Files:**
- Create: `mpy_cli/config_wizard.py`
- Test: `tests/test_config_wizard.py`

**Step 1: Write the failing test**

```python
def test_wizard_selects_scanned_port(monkeypatch):
    ...

def test_wizard_falls_back_to_manual_port(monkeypatch):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_config_wizard.py`
Expected: FAIL with missing module.

**Step 3: Write minimal implementation**

```python
def run_config_wizard(current: AppConfig | None, scanner: object) -> AppConfig:
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_config_wizard.py`
Expected: PASS.

**Step 5: Commit**

```bash
# commit 前需先向用户确认
git add mpy_cli/config_wizard.py tests/test_config_wizard.py
git commit -m "feat(config): add interactive configuration wizard" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 3: Wire CLI `init` and `config` commands

**Files:**
- Modify: `mpy_cli/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
def test_config_command_updates_existing_config(tmp_path, monkeypatch):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_cli.py -k config`
Expected: FAIL with missing command behavior.

**Step 3: Write minimal implementation**

```python
if args.command == "config":
    return _cmd_config()
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_cli.py -k config`
Expected: PASS.

**Step 5: Commit**

```bash
# commit 前需先向用户确认
git add mpy_cli/cli.py tests/test_cli.py
git commit -m "feat(cli): add init/config interactive setup flow" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```

### Task 4: Update README and regression tests

**Files:**
- Modify: `README.md`
- Modify: `tests/test_docs_and_ci.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_config_command() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py -k config`
Expected: FAIL until README updated.

**Step 3: Write minimal implementation**

```markdown
通过 `mpy-cli config` 进入交互式配置向导，无需手动编辑 TOML。
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_docs_and_ci.py`
Expected: PASS.

**Step 5: Commit**

```bash
# commit 前需先向用户确认
git add README.md tests/test_docs_and_ci.py docs/plans/2026-03-03-interactive-config-design.md docs/plans/2026-03-03-interactive-config-implementation.md
git commit -m "docs: describe interactive config wizard workflow" -m "Co-authored-by: opencode-agent[bot] <opencode-agent[bot]@users.noreply.github.com>"
```
