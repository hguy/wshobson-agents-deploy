# CLI Commands

## `install`

```
# Launcher (recommended):
./agents.sh install [--target opencode] [--source-repo https://github.com/wshobson/agents]
                    [--source-branch main] [--cache-dir ~/.cache/wshobson-agents]
                    [--source <local-cc-path>] [--output ./<target>] [--dest <target-default>]
# Direct:
python install.py [<same-args>]
```

Runs `convert` then `deploy` in one step: clones the CC source repo (or uses `--source`), converts to target format, and deploys to the target config directory. Accepts all convert and deploy options.

**Options:**
- All options from `convert` (see above)
- `--dest` — deploy destination (default: target's global config dir)

---

## `convert`

```
# Launcher (recommended — checks prerequisites first):
./agents.sh convert [--target opencode] [--source-repo https://github.com/wshobson/agents]
                    [--source-branch main] [--cache-dir ~/.cache/wshobson-agents]
                    [--source <local-path>] [--output ./<target>]
# Direct:
python convert.py [<same-args>]
```

> Windows: `agents.ps1` instead of `./agents.sh`

Reads CC format from the source repo and writes target format. Defaults to OpenCode target.

**Options:**
- `--target` (default: `"opencode"`)
- `--source-repo` (default: `"https://github.com/wshobson/agents"`)
- `--source-branch` (default: `"main"`)
- `--cache-dir` (default: `~/.cache/wshobson-agents`)
- `--source` — local path (skips clone)
- `--output` — output directory (default: `./<target output dir>`)

**Operations:**
1. Clone/fetch source repo (unless `--source` given)
2. **Sanity check source structure**: Validate the CC repo has expected layout and warn on any deviation (see below)
3. Parse `marketplace.json` to discover all plugins
4. For each plugin, read `plugin.json` metadata
5. Convert each `agents/*.md` → `<output>/agents/<plugin>/<name>.md` (model enums preserved as-is)
6. Convert each `commands/*.md` → `<output>/commands/<name>.md`
7. Copy each `skills/<name>/SKILL.md` → `<output>/skills/<name>/SKILL.md`
8. Generate config file (delegated to target module)

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

## `deploy`

```
# Launcher (recommended):
./agents.sh deploy [--target opencode] [--source ./<target>] [--dest <target-default>]
# Direct:
python deploy.py [<same-args>]
```

Deploys previously converted files. Unlike `install`, this skips the clone+convert step — it reads already-converted files from `--source` and copies them to `--dest`. Defaults to OpenCode target.

**Options:**
- `--target` (default: `"opencode"`)
- `--source` — converted files directory (default: `./<target output dir>`)
- `--dest` — deploy destination (default: target's global config dir)

`--dest` resolution:
- **Not provided** → use the target's global config directory (e.g. `~/.config/opencode`)
- **Provided + is a git repo root** (has `.git`) → translate via `target.project_config_dir()`
- **Provided + any other path** → use as-is

**Operations:**
1. **Detect config format**: Target-specific (see target SPEC)
2. Copy all agents from source to target agents dir
3. Copy all commands from source to target commands dir
4. Copy all skills from source to target skills dir
5. Copy tools/plugins as needed
6. **Merge config**:
   - First deploy: back up original config
   - Subsequent: do NOT overwrite backup
7. **Record original model enums** (first deploy only): Read `model:` from each deployed agent file
8. **Swap model enums → target model IDs** (first deploy only): Apply default tier→ID mapping via internal `swap` call
9. **Generate manifest** with deployed files, config format, and pre-swap model enums
10. Run target validation (target-specific, see target SPEC)

---

## `remove`

```
# Launcher (recommended):
./agents.sh remove [--target opencode] [--dest <target-default>] [--force]
# Direct:
python remove.py [<same-args>]
```

Undoes `install` using the manifest. Defaults to OpenCode target. Safe to call multiple times (manifest deleted on first remove).

Prompts once for confirmation before removing any files. Use `--force` to skip the prompt.

**Options:**
- `--target` (default: `"opencode"`)
- `--dest` — install destination (default: target's global config dir)
- `--force` — skip confirmation prompt

**Operations:**
1. If manifest doesn't exist, exit (nothing to remove)
2. Prompt for confirmation (skip if `--force` set)
3. Read manifest → get deployed file list
4. Delete each deployed file
5. Clean up empty directories
6. Restore original config from pre-migration backup
7. Delete backup file
8. Delete manifest

---

## `swap`

```
# Launcher (recommended):
./agents.sh swap [--target opencode] [--dest <target-default>] <from> <to>
# Direct:
python swap.py [<same-args>]
```

Swaps `model:` frontmatter for deployed agents whose original CC model tier matches `<from>`. `install` invokes this internally on first deploy. Defaults to OpenCode target.

**Options:**
- `--target` (default: `"opencode"`)
- `--dest` — install destination (default: target's global config dir)

**Positional arguments:**
- `from` — `opus`, `sonnet`, `haiku`, or `inherit`
- `to` — target model ID

**Operations:**
1. Load manifest; read `agent_models` for each agent's original model enum
2. Filter to agents whose original model matches `<from>`
3. For each match: replace or inject `model:` frontmatter with `<to>`

**Idempotency:** Running when agents already have the target model is a no-op.

---

# Manifest

All paths in the manifest use POSIX-style `/` separators regardless of OS. This ensures portability across platforms — the manifest can be inspected, compared, or processed on any system without separator mismatches.

## Format

```json
{
  "version": 1,
  "installed_at": "2026-05-07T18:00:00Z",
  "source": "<target>",
  "target": "<install-path>",
  "files": {
    "agents/<plugin>/<name>.md": {
      "source": "<target>/agents/<plugin>/<name>.md",
      "checksum": "sha256-hash"
    },
    "skills/<name>/SKILL.md": {
      "source": "<target>/skills/<name>/SKILL.md",
      "checksum": "sha256-hash"
    }
  },
  "agent_models": {
    "agents/<plugin>/<name>.md": { "original": "sonnet" }
  }
}
```

---

# Validation Strategy

After each `convert`, `deploy`, and `install`:

1. **Structural**: Verify directory layout matches target expectations (see target SPEC)
2. **Content**: Frontmatter correctness
   - YAML parses without errors
   - Required fields present
   - `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$`
3. **Idempotency**:
   - `convert` ×2: byte-identical output
   - `deploy` ×2: same manifest, same checksums. Backup NOT overwritten.
   - `remove` after `deploy` ×2: restores true original config
   - `remove` ×2: second call is no-op
