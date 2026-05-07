# WSHOBSON Agents Deploy — Repo Rules

## Project

Python 3.12+ migration tool converting [wshobson/agents](https://github.com/wshobson/agents) (Claude Code format) to OpenCode (and other target platforms).

The product is **the migration code itself**, not the resulting artifacts. Rerunnable every time the upstream CC plugin marketplace changes. Accuracy of conversion (field mapping, file placement, naming conventions) is the primary quality metric. Architecture is **target-pluggable**: source is always CC, output is OpenCode (default), Pi, Hermes, etc. Adding a target means writing a target module, not forking the tool.

## Build & Run

```powershell
# Install dependencies
uv sync

# Run
python convert.py --target opencode
python install.py --target opencode
python swap.py opus gpt-4o
python remove.py

## Lint & Type Check

```powershell
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy convert.py install.py remove.py swap.py converter.py installer.py manifest.py targets/
```

## Implementation Order

1. `models.py` + `manifest.py` — data structures first
2. `targets/base.py` + `targets/opencode/` — target interface + OpenCode module
3. `converter.py` — core conversion (reads CC source, delegates to target)
4. `installer.py` — install/remove logic
5. `convert.py` + `install.py` + `remove.py` + `swap.py` — CLI entry points importing the shared modules above

## Conventions

- All functions **must** have full type annotations
- Prefer `pathlib.Path` over `os.path`
- Use Pydantic models for all data structures
- Each command (`convert`, `install`, `remove`, `swap`) is a function in `migrate.py` that delegates to the appropriate module
- The manifest is always the source of truth for deployment state
