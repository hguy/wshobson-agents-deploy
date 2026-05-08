# OpenCode Target Specification

## Output Format

```
opencode/
├── agents/              # agents/<plugin>/<agent>.md
│   └── <plugin>/
│       └── <agent>.md
├── commands/            # commands/<command-name>.md
│   └── <command-name>.md
├── skills/              # skills/<name>/SKILL.md
│   └── <skill-name>/
│       └── SKILL.md
└── AGENTS.md            # Rules file
```

### Agent Conversion

| CC Field | OC Field | Rule |
|----------|----------|------|
| `name` | (filename) | `<plugin>/<name>.md` inside `agents/` |
| `name` | `name` | `{plugin}-{name}` (prefixed for unique `@ref`) |
| `description` | `description` | Pass through |
| `model: opus` | `model: opus` | Kept as enum; `deploy` maps via `swap` |
| `model: sonnet` | `model: sonnet` | |
| `model: haiku` | `model: haiku` | |
| `model: inherit` | (omit) | Leave unset |
| `color` | `color` | Named colors mapped to hex: `cyan→#00BCD4`, `blue→#2196F3`, `green→#4CAF50`, `magenta→#E91E63`, `red→#F44336`, `yellow→#FFC107` |
| `tools: Read, Grep` | `permission: { read: allow, grep: allow }` | Listed = `allow`, others = `deny` |
| (none) | `mode: subagent` | All CC agents become subagents |
| Body | Body | Pass through |

### Model Tier Mapping

Used by `swap` and `deploy`:

| CC Enum | OC Model ID |
|---------|------------|
| `opus` | `anthropic/claude-opus-4-20250514` |
| `sonnet` | `anthropic/claude-sonnet-4-20250514` |
| `haiku` | `anthropic/claude-haiku-4-20250514` |
| `inherit` | (omit field) |

### Tool Name Mapping

| CC Tool | OC Tool |
|---------|---------|
| `Read` | `read` |
| `Edit` | `edit` |
| `Write` | `write` (gated by `edit`) |
| `Grep` | `grep` |
| `Glob` | `glob` |
| `Bash` | `bash` |
| `Task` | `task` |
| `WebFetch` | `webfetch` |
| `WebSearch` | `websearch` |
| `LSP` | `lsp` |
| `Skill` | `skill` |
| `TodoWrite` | `todowrite` |
| `Question` | `question` |

### Skill Conversion

Skills are already compatible — OpenCode natively discovers `.claude/skills/`. Two options:
1. Copy to `.opencode/skills/<name>/SKILL.md` (recommended)
2. Leave in place at `.claude/skills/<name>/SKILL.md` (auto-discovered)

### Command Conversion

| CC Field | OC Field | Rule |
|----------|----------|------|
| `description` | `description` | Pass through |
| `argument-hint` | (omit) | Implied by `$ARGUMENTS` |
| (none) | `agent` | Omit or set to `build` |
| Body | Body (template) | Pass through |

### Plugin Conversion

CC plugins are JSON metadata. OC plugins are executable JS/TS with hooks. For initial migration, create `.opencode/plugins/<name>.ts` as lightweight registration wrappers. `marketplace.json` becomes the `opencode.json` config and/or plugin references.

---

## Install Details

### Default Paths

| Setting | Value |
|---------|-------|
| `output_dir()` | `opencode` |
| `project_config_dir()` | `.opencode` |
| `global_config_dir()` | `~/.config/opencode` |

### Config Format Handling

OpenCode supports two config formats: `opencode.json` and `opencode.jsonc`. They are alternatives, not additive. The installer detects which is in use:
1. Check `~/.config/opencode/opencode.json` → use `.json`
2. Else check `~/.config/opencode/opencode.jsonc` → use `.jsonc`
3. If neither → default to `.json`

Same logic for per-project `opencode.json`/`opencode.jsonc` and `tui.json`/`tui.jsonc`. The manifest records the format used.

### AGENTS.md Integration

No integration — agents are self-discovered by OpenCode from `agents/` subdirectory.

### Manifest

Stored as `wshobson-agents-manifest.json` at the install target. See [COMMANDS.md](../../COMMANDS.md#manifest) for format.

### Validation

```
opencode agent list
```
