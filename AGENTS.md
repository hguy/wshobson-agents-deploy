# WsHobson Agents Anywhere — Repo Rules

## Project

Python 3.12+ migration tool converting [wshobson/agents](https://github.com/wshobson/agents) (Claude Code) to OpenCode and other agent platforms.

The product is **the migration code itself**, not the resulting artifacts. Rerunnable every time the wshobson/agents plugin marketplace changes. Accuracy of conversion (field mapping, file placement, naming conventions) is the primary quality metric. Architecture is **target-pluggable**: source is always CC, output is OpenCode (default), Pi, Hermes, etc. Adding a target means writing a target module, not forking the tool.

## Build & Run

```powershell
# Install dependencies
uv sync --group dev

# Run (launcher scripts auto-check Python 3.12+, git, add -y for silent setup)
./agents.sh convert --target opencode
./agents.sh install --target opencode
./agents.sh swap --target opencode opus gpt-4o
./agents.sh remove --target opencode

# Skip prompts for missing prerequisites
./agents.sh -y convert

# Or call Python directly (deps must be installed)
uv run python convert.py --target opencode
```

### Launcher Scripts

`agents.sh` (macOS/Linux) and `agents.ps1` (Windows) handle:

| Flag | Purpose |
|------|---------|
| `-y` / `--yes` | Auto-confirm all prerequisite installations (no prompts) |

Checks performed:
1. **Python 3.12+** — auto-installs via uv/brew/apt/dnf/yum/apk/winget/choco
2. **git** — auto-installs via brew/apt/dnf/yum/apk/winget/choco (required for `convert`)
3. **uv** — recommended for faster dep management, falls back to system Python

## Lint & Type Check

```powershell
# Install dev dependencies
uv sync --group dev

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy convert.py install.py remove.py swap.py converter.py installer.py manifest.py targets/ models.py
```

## Implementation Order

1. `models.py` + `manifest.py` — data structures first
2. `targets/base.py` + `targets/opencode/` — target interface + OpenCode module
3. `converter.py` — core conversion (reads CC source, delegates to target)
4. `installer.py` — install/remove logic
5. `convert.py` + `install.py` + `remove.py` + `swap.py` — CLI entry points importing the shared modules above

## Test Protocol

Test the launcher scripts in a **clean Docker container** to verify prerequisite auto-install and full pipeline.

### 1. Fresh-Start Test (`-y` auto-install)

```bash
docker run -d --name test-agent -w /test \
  -v "$PWD":/test ubuntu:24.04 sleep 3600

docker exec test-agent bash -c "
  DEBIAN_FRONTEND=noninteractive bash /test/agents.sh -y convert --help 2>&1
"

docker kill test-agent; docker rm test-agent
```

**Expected**: Python 3.12+ auto-installed via apt, git auto-installed via apt, script proceeds to Python (import error for project deps is OK — `uv sync` not yet run).

### 2. Prompt-Abort Test (user declines)

```bash
docker run -d --name test-agent -w /test \
  -v "$PWD":/test ubuntu:24.04 sleep 3600

echo "n" | docker exec -i test-agent bash /test/agents.sh convert 2>&1
# → "Aborted. Python 3.12+ is required."  exit 1

docker kill test-agent; docker rm test-agent
```

### 3. Full Pipeline Test (with deps)

```bash
docker run -d --name test-agent -w /test \
  -v "$PWD":/test ubuntu:24.04 sleep 3600

docker exec test-agent bash -c '
  export PATH="$HOME/.local/bin:$PATH"

  # Create test fixture
  mkdir -p /tmp/src/.claude-plugin
  mkdir -p /tmp/src/plugins/test-plugin/{.claude-plugin,agents,commands,skills/test-skill}
  cat > /tmp/src/.claude-plugin/marketplace.json <<<"EOF"
  {"plugins": [{"name": "test-plugin", "source": "plugins/test-plugin", "version": "1.0.0", "description": "Test"}]}
EOF
  cat > /tmp/src/plugins/test-plugin/.claude-plugin/plugin.json <<<"EOF"
  {"name": "test-plugin", "version": "1.0.0", "description": "Test plugin"}
EOF
  cat > /tmp/src/plugins/test-plugin/agents/test-agent.md <<<"EOF"
---
name: test-agent
description: "A test agent"
model: opus
color: blue
tools: Read, Grep, Bash
---
body
EOF
  cat > /tmp/src/plugins/test-plugin/commands/test-cmd.md <<<"EOF"
---
description: A test command
---
echo hi
EOF
  mkdir -p /tmp/src/plugins/test-plugin/skills/test-skill
  cat > /tmp/src/plugins/test-plugin/skills/test-skill/SKILL.md <<<"EOF"
---
name: test-skill
description: "A test skill"
---
skill body
EOF

  # Install deps & run full pipeline
  cd /test
  DEBIAN_FRONTEND=noninteractive bash agents.sh -y convert --source /tmp/src --output /tmp/out
  bash agents.sh install --target opencode --source /tmp/out --dest /tmp/dest
  echo "Model after install: $(grep "model:" /tmp/dest/agents/test-agent.md)"
  bash agents.sh swap --target opencode --dest /tmp/dest opus gpt-4o
  echo "Model after swap: $(grep "model:" /tmp/dest/agents/test-agent.md)"
  bash agents.sh remove --target opencode --dest /tmp/dest --force
'

docker kill test-agent; docker rm test-agent
```

**Expected**: Convert → Install (model auto-mapped `opus→anthropic/claude-opus-4-20250514`) → Swap (→ `gpt-4o`) → Remove (files cleaned up).

### 4. Python Direct (no launcher scripts)

```bash
uv run python convert.py --source /tmp/src --output /tmp/out
uv run python install.py --target opencode --source /tmp/out --dest /tmp/dest
uv run python swap.py --target opencode --dest /tmp/dest opus gpt-4o
uv run python remove.py --target opencode --dest /tmp/dest --force
```

---

## Windows Test Protocol

Test `agents.ps1` in a **Windows Docker container** (requires Docker Desktop in Windows container mode). Use `mcr.microsoft.com/windows/servercore:ltsc2022` as the base image.

> **Note**: Windows server containers do not include winget or choco, so `agents.ps1`'s auto-install will always hit the error path in this environment. The full auto-install success path (winget) can only be tested on a real Windows desktop or VM. These tests validate the error handling and the core pipeline respectively.

### W1. Fresh-Start Test (`-y` auto-install)

```powershell
docker run -d --name test-win -v "$PWD:C:\test" `
  -w C:\test mcr.microsoft.com/windows/servercore:ltsc2022 `
  powershell -Command "Start-Sleep 3600"

docker exec test-win powershell -Command "C:\test\agents.ps1 -y convert --help 2>&1"
```

**Expected**: Python 3.12+ not found → `agents.ps1` tries uv/winget/choco → none available → "No supported package manager found" → exit 1. Validates the fallback error path is correct.

### W2. Prompt-Abort Test (user declines)

```powershell
echo "n" | docker exec -i test-win powershell -Command "C:\test\agents.ps1 convert --help 2>&1"
# → "Aborted. Python 3.12+ is required."  exit 1
```

### W3. Full Pipeline Test

Since `agents.ps1` cannot auto-install prerequisites in a server container, Python 3.12 and git are installed manually first. This tests the core pipeline (convert → install → swap → remove) on Windows, **not** the launcher's prerequisite feature.

```powershell
# Install Python + git (agents.ps1 can't do this in server containers — no winget)
docker exec test-win powershell -Command @"
  Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile C:\python-installer.exe -UseBasicParsing
  Start-Process C:\python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait; Remove-Item C:\python-installer.exe
  Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe' -OutFile C:\git-installer.exe -UseBasicParsing
  Start-Process C:\git-installer.exe -ArgumentList '/VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES' -Wait; Remove-Item C:\git-installer.exe
  powershell -ExecutionPolicy ByPass -c "Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -OutFile C:\uv-install.ps1 -UseBasicParsing"
  powershell -ExecutionPolicy ByPass C:\uv-install.ps1; Remove-Item C:\uv-install.ps1
"@

# Create fixtures and run pipeline (container-local venv to avoid mount permission issues)
docker exec test-win powershell -Command @"
  `$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  `$userBin = "`$env:USERPROFILE\.local\bin"
  if (Test-Path `$userBin) { `$env:Path = "`$userBin;`$env:Path" }
  `$env:UV_PROJECT_ENVIRONMENT = "C:\work\.venv"
  `$src = "C:\tmp\src"

  New-Item -ItemType Directory -Path "`$src\.claude-plugin" -Force | Out-Null
  New-Item -ItemType Directory -Path "`$src\plugins\test-plugin\.claude-plugin" -Force | Out-Null
  New-Item -ItemType Directory -Path "`$src\plugins\test-plugin\agents" -Force | Out-Null
  New-Item -ItemType Directory -Path "`$src\plugins\test-plugin\commands" -Force | Out-Null
  New-Item -ItemType Directory -Path "`$src\plugins\test-plugin\skills\test-skill" -Force | Out-Null

  '{"plugins": [{"name": "test-plugin", "source": "plugins/test-plugin", "version": "1.0.0", "description": "Test"}]}' | Set-Content "`$src\.claude-plugin\marketplace.json" -Encoding Ascii
  '{"name": "test-plugin", "version": "1.0.0", "description": "Test plugin"}' | Set-Content "`$src\plugins\test-plugin\.claude-plugin\plugin.json" -Encoding Ascii
  @'---`nname: test-agent`ndescription: "A test agent"`nmodel: opus`ncolor: blue`ntools: Read, Grep, Bash`n---`nbody'@ | Set-Content "`$src\plugins\test-plugin\agents\test-agent.md" -Encoding Ascii
  @'---`ndescription: A test command`n---`necho hi'@ | Set-Content "`$src\plugins\test-plugin\commands\test-cmd.md" -Encoding Ascii
  @'---`nname: test-skill`ndescription: "A test skill"`n---`nskill body'@ | Set-Content "`$src\plugins\test-plugin\skills\test-skill\SKILL.md" -Encoding Ascii

  cd C:\test
  uv sync --group dev 2>&1 | Select-Object -Last 3
  uv run python convert.py --source C:\tmp\src --output C:\tmp\out
  uv run python install.py --target opencode --source C:\tmp\out --dest C:\tmp\dest
  Select-String "model:" C:\tmp\dest\agents\test-agent.md
  uv run python swap.py --target opencode --dest C:\tmp\dest opus gpt-4o
  Select-String "model:" C:\tmp\dest\agents\test-agent.md
  uv run python remove.py --target opencode --dest C:\tmp\dest --force
"@
```

**Expected**: Convert → Install (model auto-mapped `opus→anthropic/claude-opus-4-20250514`) → Swap (→ `gpt-4o`) → Remove (files cleaned up).

### W4. Python Direct (no launcher scripts)

```powershell
uv run python convert.py --source C:\tmp\src --output C:\tmp\out
uv run python install.py --target opencode --source C:\tmp\out --dest C:\tmp\dest
uv run python swap.py --target opencode --dest C:\tmp\dest opus gpt-4o
uv run python remove.py --target opencode --dest C:\tmp\dest --force
```

## Conventions

- All functions **must** have full type annotations
- Prefer `pathlib.Path` over `os.path`
- Use Pydantic models for all data structures
- Each command (`convert`, `install`, `remove`, `swap`) is a standalone `.py` file that imports the appropriate shared module
- The manifest is always the source of truth for deployment state
