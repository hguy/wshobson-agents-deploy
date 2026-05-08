# Formats

## Claude Code Source Format

Source: [wshobson/agents](https://github.com/wshobson/agents). Cloned automatically by `convert`.

```
agents/
├── .claude-plugin/marketplace.json   # Registry: plugin name, source path, metadata
├── plugins/
│   ├── <plugin-name>/
│   │   ├── .claude-plugin/plugin.json  # {name, version, description, author, license}
│   │   ├── agents/*.md                 # Agent definition files
│   │   ├── commands/*.md               # Command definition files
│   │   └── skills/<skill-name>/SKILL.md # Skill definition files
│   └── ...
├── docs/                              # Documentation (not migrated)
└── tools/                             # Dev utilities (not migrated)
```

### CC Agent Frontmatter

```yaml
---
name: agent-name
description: "What this agent does. Use PROACTIVELY when [trigger conditions]."
model: opus|sonnet|haiku|inherit
color: blue|green|red|yellow|cyan|magenta  # optional
tools: Read, Grep, Glob  # optional — restricts available tools
---
```

### CC Skill Frontmatter

```yaml
---
name: skill-name
description: "Use this skill when [specific trigger conditions]."
---
```

### CC Command Frontmatter

```yaml
---
description: What this command does
argument-hint: <path> [--flag]
---
```

### plugin.json

```json
{ "name": "plugin-name", "version": "1.0.0", "description": "...", "author": {...}, "license": "MIT" }
```

### marketplace.json

Lists all plugins with name, source path, version, description, author, category, homepage, license.

---

## Target Formats

Each target defines its own output format. See the target's `SPEC.md` for details:

| Target | Location | Format |
|--------|----------|--------|
| OpenCode | `targets/opencode/SPEC.md` | agents/commands/skills in `.opencode/` |
| Pi | `targets/pi/SPEC.md` | (TBD) |
| Hermes | `targets/hermes/SPEC.md` | (TBD) |

## Agent Naming & Plugin Context

CC agents live in plugin-scoped directories (`plugins/<plugin>/agents/<agent>.md`) — names only need uniqueness within a plugin. Target platforms vary in how they handle this:

| Platform | Subdir discovery | Agent reference | Naming rule |
|----------|-----------------|-----------------|-------------|
| OpenCode | ✅ Recursive `**/*.md` | Flat `@name` from frontmatter | `{plugin}-{agent}` — unique global refs |
| Pi (TBD) | ? | ? | Verify before implementing |
| Hermes (TBD) | ? | ? | Verify before implementing |

**Key principle for any target integration**: Determine two things before deciding how to name agents:

1. **File placement** — Does the target discover agents from subdirectories, or only from a flat directory? Nested dirs preserve plugin grouping and avoid file collisions; flat dirs require prefixing the filename itself.
2. **Reference namespace** — Does the target use `@name` references that are globally unique, or are they scoped (e.g., `@plugin/agent`)? If flat/global, the `name` field must be prefixed. If namespaced, short names work.

The same applies to commands and skills. If any share a global namespace, prefix to avoid collisions.

## Adding a New Target

Create `targets/<name>/` with:
- `__init__.py`
- `target.py` implementing `MigrationTarget`

The target defines its own format mappings, output directory, model IDs, and tool naming via the target interface (see [ARCHITECTURE.md](./ARCHITECTURE.md)).
