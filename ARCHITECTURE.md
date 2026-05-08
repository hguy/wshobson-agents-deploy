# Architecture

## Overview

The migrator is a single-source, multi-target converter. The source is always Claude Code format ([wshobson/agents](https://github.com/wshobson/agents)). The target is pluggable — OpenCode (default), Pi, Hermes, KiloCode, etc.

```
CC Source ──→ converter.py ──→ targets/<name>/ ──→ install/remove/swap
                     ↑
              delegates per-item
              to active target module
```

## Target Interface

Every target lives in `targets/<name>/` and implements `MigrationTarget` from `targets/base.py`:

| Method | Purpose |
|--------|---------|
| `convert_agent(raw: dict, body: str) → str` | Transform a CC agent → target agent markdown |
| `convert_command(raw: dict, body: str) → str` | Transform a CC command → target command markdown |
| `convert_skill(source: Path, out: Path) → None` | Copy/adapt a CC skill → target skill directory |
| `generate_config(agents: list, ...) → dict` | Produce the target's config file |
| `generate_rules(agents: list, ...) → str` | Produce the target's rules/instructions file |
| `output_dir() → str` | Output subdirectory name |
| `project_config_dir() → str` | Project-local config dir name |
| `global_config_dir() → Path` | Default global install path |
| `model_mapping() → dict[str, str\|None]` | `{opus→id, sonnet→id, haiku→id, inherit→None}` |
| `tool_mapping() → dict[str, str]` | CC tool name → target tool name |

Each target also provides install/remove-specific behavior: config format detection, rules file integration, and validation commands. See `targets/<name>/SPEC.md` for per-target details.

## Commands Overview

| Command | Entry Point | Description |
|---------|-------------|-------------|
| `install` | `install.py --target X` | Chains `convert` + `deploy` (clone → convert → deploy) |
| `convert` | `convert.py --target X` | Reads CC source, writes target format |
| `deploy` | `deploy.py --target X` | Deploys converted files to config dir |
| `remove` | `remove.py` | Removes deployed files via manifest |
| `swap` | `swap.py <from> <to>` | Swaps model IDs in deployed agents |

## Source Repo Management

The `convert` command manages a local clone of `https://github.com/wshobson/agents`:

| Flag | Default | Description |
|------|---------|-------------|
| `--source-repo` | `https://github.com/wshobson/agents` | GitHub URL to clone |
| `--source-branch` | `main` | Branch to check out |
| `--cache-dir` | `~/.cache/wshobson-agents/` | Where to store the clone |
| `--source` | _(none)_ | Local path override (skips clone) |

Logic:
1. If `--source` is given → use as-is (no clone)
2. Else if `--cache-dir` does not exist → `git clone --depth 1 <repo> <cache-dir>`
3. Else → `git fetch origin && git reset --hard origin/<branch>`
4. `--source` defaults to `<cache-dir>/plugins`

## Tech Stack

- Python 3.12+ with `uv` as package manager
- `pyyaml` for YAML frontmatter parsing/emission
- `typer` for CLI interface
- `pydantic` for config/models
- `ruff` for linting (with type annotation enforcement)
- `mypy` for static type checking (strict mode)
- All function signatures **must** have full type annotations

## Implementation Files

```
.
├── GOAL.md                      # High-level overview
├── ARCHITECTURE.md              # This file
├── FORMATS.md                   # Source format (CC) + target format references
├── COMMANDS.md                  # Generic CLI command specs
├── AGENTS.md                    # Repo rules for implementation agent
├── README.md                    # User-facing project overview
├── pyproject.toml               # Python project config
├── convert.py                   # convert command
├── deploy.py                    # deploy command
├── install.py                   # install command (chains convert + deploy)
├── remove.py                    # remove command
├── swap.py                      # swap command
├── converter.py                 # Shared: target-agnostic conversion core
├── installer.py                 # Shared: install/remove logic
├── models.py                    # Shared: Pydantic models
├── manifest.py                  # Shared: manifest read/write
├── targets/                     # Pluggable target modules
│   ├── base.py                  # MigrationTarget ABC
│   ├── opencode/                # OpenCode target
│   │   ├── __init__.py
│   │   ├── SPEC.md              # OpenCode-specific format + install details
│   │   ├── target.py            # OpenCode migration logic
│   │   ├── config.py            # opencode.json generation
│   │   ├── formatting.py        # Agent/command frontmatter conversion
│   │   └── models.py            # OpenCode-specific models
│   ├── pi/                      # Pi target (placeholder)
│   │   ├── __init__.py
│   │   └── target.py
│   └── hermes/                  # Hermes target (placeholder)
│       ├── __init__.py
│       └── target.py
├── agents.ps1                   # PowerShell launcher (Windows)
├── agents.sh                    # Shell launcher (macOS/Linux)
└── <target>/                    # Converted output (generated, name varies by --target)
    ├── agents/
    ├── commands/
    ├── skills/
    ...
```
