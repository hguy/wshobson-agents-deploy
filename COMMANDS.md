# CLI Commands

## `convert`

```
python convert.py --target <name> [--source-repo https://github.com/wshobson/agents] [--output ./<target>]
```

Reads CC format from the source repo and writes target format.

**Operations:**
1. Clone/fetch source repo (unless `--source` given)
2. **Sanity check source structure**: Validate the CC repo has expected layout and warn on any deviation (see below)
3. Parse `marketplace.json` to discover all plugins
4. For each plugin, read `plugin.json` metadata
5. Convert each `agents/*.md` → `<output>/agents/<name>.md` (model enums preserved as-is)
6. Convert each `commands/*.md` → `<output>/commands/<name>.md`
7. Copy each `skills/<name>/SKILL.md` → `<output>/skills/<name>/SKILL.md`
8. Generate config file (delegated to target module)
9. Generate rules/instructions file (delegated to target module)

### Source Sanity Check

Before any conversion, validate the CC source repo's structural integrity. Warnings are non-fatal (conversion proceeds) but reported to the user:

| Check | What it validates |
|-------|-------------------|
| `marketplace.json` | Exists at repo root, valid JSON, has `plugins` array |
| Plugin dirs exist | Each `marketplace.plugins[i].source` path resolves to a real directory |
| `plugin.json` | Exists in each plugin dir, valid JSON, `name` matches marketplace entry |
| Agent frontmatter | Each `agents/*.md` has YAML frontmatter with `name` and `description` |
| Skill frontmatter | Each `skills/*/SKILL.md` has YAML frontmatter with `name` and `description` |
| Skill dir naming | Skill directory name matches frontmatter `name` field |
| Command frontmatter | Each `commands/*.md` has YAML frontmatter with `description` |
| Orphan files | Plugin subdirectories that are not `agents/`, `commands/`, `skills/`, or `.claude-plugin/` are flagged |
| `name` format | All `name` fields match `^[a-z0-9]+(-[a-z0-9]+)*$` |
| Duplicate names | Agents/commands/skills with the same name across plugins are flagged |

Warnings print to stderr with `[WARN]` prefix. A summary line shows `N warnings, M plugins OK`.

**Validation:**
- Verify file naming conventions match target requirements
- YAML frontmatter parses without errors
- Required fields present
- `name` fields match `^[a-z0-9]+(-[a-z0-9]+)*$`

---

## `install`

```
python install.py --target <name> [--source ./<target>] [--dest <target-default>]
```

Deploys converted files. `--target` selects which target module's install logic applies (required, no default). The target module defines default paths for `--source` and `--dest` (see `targets/<name>/SPEC.md`).

`--dest` resolution rules (implemented by the target module):
1. **Not provided** → use the target's global directory
2. **Git repo root** (has `.git` subdirectory) → translate via `target.project_config_dir()`
3. **Any other path** → use as-is

**Operations:**
1. **Detect config format**: Target-specific (see target SPEC)
2. Copy all agents from source to target agents dir
3. Copy all commands from source to target commands dir
4. Copy all skills from source to target skills dir
5. Copy tools/plugins as needed
6. **Merge config**:
   - First install: back up original config
   - Subsequent: do NOT overwrite backup
7. **Integrate with target's rules file** (target-specific, see target SPEC)
8. **Create compiled instruction file** with full migrated agent instructions
9. **Record original model enums** (first install only): Read `model:` from each deployed agent file
10. **Swap model enums → target model IDs** (first install only): Apply default tier→ID mapping via internal `swap` call
11. **Generate manifest** with deployed files, config format, and pre-swap model enums
12. Run target validation (target-specific, see target SPEC)

---

## `remove`

```
python remove.py [--manifest <path>] [--force]
```

Undoes `install` using the manifest. Safe to call multiple times (manifest deleted on first remove).

Prompts once for confirmation before removing any files. Use `--force` to skip the prompt.

**Operations:**
1. If manifest doesn't exist, exit (nothing to remove)
2. Prompt for confirmation (skip if `--force` set)
3. Read manifest → get deployed file list
4. Delete each deployed file
5. Clean up empty directories
5. **Restore target's rules file** (target-specific, see target SPEC — e.g. OC removes `@WSHOBSON_AGENTS.md` ref from AGENTS.md)
6. **Delete compiled instruction file** (target-specific — e.g. OC deletes `WSHOBSON_AGENTS.md`)
7. Restore original config from pre-migration backup
8. Delete backup file
9. Delete manifest

---

## `swap`

```
python swap.py --target <name> [--manifest <path>] <from> <to>
```

Swaps `model:` frontmatter for deployed agents whose original CC model tier matches `<from>`. `install` invokes this internally on first deploy.

`--target` selects which target's manifest to use (required). The manifest path defaults to the target's standard manifest location (see target SPEC); use `--manifest` to override.

**Parameters:**
- `--target`: target module name (required)
- `from`: `opus`, `sonnet`, `haiku`, or `inherit`
- `to`: target model ID
- `--manifest`: manifest path override (optional)

**Operations:**
1. Load manifest; read `agent_models` for each agent's original model enum
2. Filter to agents whose original model matches `<from>`
3. For each match: replace or inject `model:` frontmatter with `<to>`

**Idempotency:** Running when agents already have the target model is a no-op.

---

# Manifest

## Format

```json
{
  "version": 1,
  "installed_at": "2026-05-07T18:00:00Z",
  "source": "<target>",
  "target": "<install-path>",
  "files": {
    "agents/<name>.md": {
      "source": "<target>/agents/<name>.md",
      "checksum": "sha256-hash"
    },
    "skills/<name>/SKILL.md": {
      "source": "<target>/skills/<name>/SKILL.md",
      "checksum": "sha256-hash"
    }
  },
  "agents_modifications": {
    "AGENTS.md": {
      "added_lines": ["@<INSTRUCTIONS_FILE>.md"],
      "checksum": "sha256-hash"
    }
  },
  "agent_models": {
    "agents/<name>.md": { "original": "sonnet" }
  },
  "config_backups": {
    "<config-file>": "backups/<config-file>.timestamp"
  }
}
```

---

# Validation Strategy

After each `convert` and `install`:

1. **Structural**: Verify directory layout matches target expectations (see target SPEC)
2. **Content**: Frontmatter correctness
   - YAML parses without errors
   - Required fields present
   - `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$`
3. **Idempotency**:
   - `convert` ×2: byte-identical output
   - `install` ×2: same manifest, same checksums. Backup NOT overwritten.
   - `remove` after `install` ×2: restores true original config
   - `remove` ×2: second call is no-op
