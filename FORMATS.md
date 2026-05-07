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

## Adding a New Target

Create `targets/<name>/` with:
- `__init__.py`
- `target.py` implementing `MigrationTarget`

The target defines its own format mappings, output directory, model IDs, and tool naming via the target interface (see [ARCHITECTURE.md](./ARCHITECTURE.md)).
