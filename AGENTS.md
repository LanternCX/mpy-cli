# AGENTS Guide (`mpy-cli`)

This guide is for coding agents working in this repository.
Follow these commands and conventions unless the user explicitly asks otherwise.

## Scope
- Applies to the whole repo.
- Main language: Python.
- Main function: deploy local code to MicroPython devices via `mpremote`.

## External Agent Rules
- Cursor rules dir: `.cursor/rules/` -> not present.
- Cursor single file rules: `.cursorrules` -> not present.
- Copilot instructions: `.github/copilot-instructions.md` -> not present.
- If any of these files are added, treat them as higher-priority local instructions.

## Repository Facts
- Python: `>=3.10` (3.11 recommended).
- Packaging/config: `pyproject.toml`.
- CLI entrypoint: `mpy_cli.cli:main`.
- Console script: `mpy-cli`.
- Tests: `pytest`, under `tests/`.
- CI release workflow: `.github/workflows/release.yml`.

## Setup Commands
Run from repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

## Build / Lint / Test Commands
No dedicated formatter/linter is configured in `pyproject.toml`.
Testing is the primary quality gate.

### Install / package actions
```bash
# editable install for development
python3 -m pip install -e ".[dev]"

# non-editable install
python3 -m pip install .
```

### Run all tests
```bash
python3 -m pytest -q
```

### Run one test file
```bash
python3 -m pytest -q tests/test_cli.py
```

### Run one test case (important)
```bash
python3 -m pytest -q tests/test_cli.py::test_init_command_creates_config_and_ignore
```

### Run by keyword
```bash
python3 -m pytest -q -k config
```

### Useful targeted suites
```bash
python3 -m pytest -q tests/test_docs_and_ci.py
python3 -m pytest -q tests/test_mpremote_backend.py
python3 -m pytest -q tests/test_executor.py
```

### Optional syntax sanity check
```bash
python3 -m compileall mpy_cli
```

## CLI Smoke Commands
```bash
mpy-cli init
mpy-cli config
mpy-cli plan --mode incremental --port /dev/ttyACM0
mpy-cli deploy --mode incremental --port /dev/ttyACM0
```

Non-interactive examples:
```bash
mpy-cli plan --mode full --no-interactive --port /dev/ttyACM0
mpy-cli deploy --mode full --no-interactive --yes --port /dev/ttyACM0
```

## Code Style Guidelines

### Imports
- Order imports: stdlib -> third-party -> local.
- Prefer explicit imports; avoid wildcard imports.

### Formatting
- Use 4-space indentation.
- Keep long calls split across lines for readability.
- Keep diffs stable (use trailing commas in multiline literals/calls when helpful).

### Types
- Add type hints for public functions/methods.
- Type dataclass fields explicitly.
- Use `Literal` for constrained string values (`full`, `incremental`).
- Use `Protocol` for pluggable interfaces (e.g., logger/scanner contracts).

### Naming
- `snake_case`: functions, vars, modules.
- `PascalCase`: classes/dataclasses.
- `UPPER_CASE`: constants.
- Errors should end with `Error`.

### Docstrings and Comments
- Follow existing convention: Chinese Doxygen-style docstrings.
- Public APIs should include `@brief`; add `@param`/`@return` when useful.
- Add comments only for non-obvious logic.

### Error Handling
- Raise domain-specific exceptions in lower layers:
  - `ConfigError`
  - `GitDiffError`
  - `CommandExecutionError`
- At CLI boundaries, convert expected failures to readable messages + exit codes.
- Avoid exposing raw traceback to end users for expected errors.

### Logging
- Use `setup_logging()` from `mpy_cli/logging.py`.
- Keep dual output: console + rotating file logs.
- Preserve deploy progress logs (per operation / per file).

### Paths and Persistence
- Prefer `pathlib.Path`.
- Keep runtime artifacts under project runtime dir (default `.mpy-cli/`).
- Do not write runtime artifacts to system directories.

### CLI Behavior Rules
- Keep parser behavior, README examples, and tests synchronized.
- If CLI args change, update all three:
  1) `mpy_cli/cli.py`
  2) `README.md` parameter section
  3) `tests/test_docs_and_ci.py`

### Deployment Semantics
- `full`: wipe then upload all allowed files.
- `incremental`: compute operations from git changes.
- Nested uploads must ensure remote parent directories exist first.

## Test Writing Conventions
- Test files: `tests/test_*.py`.
- Test names: `test_<behavior>`.
- Keep tests behavior-focused and deterministic.
- Add regression tests for every bug fix.

## Documentation Conventions
- Keep command examples in `README.md` current.
- Keep parameter lists complete when CLI flags change.
- Keep `docs/developer-guide.md` aligned with architecture changes.

## Agent Completion Checklist
1. Run targeted tests for changed modules.
2. Run full suite: `python3 -m pytest -q`.
3. Verify README command examples still match real CLI behavior.
4. Ensure local artifacts are not accidentally staged.
