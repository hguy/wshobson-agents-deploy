# WsHobson Agents Anywhere — Repo Rules

## Project

Python 3.12+ migration tool converting [wshobson/agents](https://github.com/wshobson/agents) (Claude Code) to OpenCode and other agent platforms.

The product is **the migration code itself**, not the resulting artifacts. Rerunnable every time the wshobson/agents plugin marketplace changes. Accuracy of conversion (field mapping, file placement, naming conventions) is the primary quality metric. Architecture is **target-pluggable**: source is always CC, output is OpenCode (default), Pi, Hermes, etc. Adding a target means writing a target module, not forking the tool.

## Build & Run

```powershell
# Install dependencies
uv sync --group dev

# Run (launcher scripts check prerequisites first)
./agents.sh convert --target opencode
./agents.sh deploy --target opencode
./agents.sh install                   # chains convert + deploy
./agents.sh swap --target opencode opus gpt-4o
./agents.sh remove --target opencode

# Or call Python directly (deps must be installed)
uv run python convert.py --target opencode
```

### Launcher Scripts

`agents.sh` (macOS/Linux) and `agents.ps1` (Windows) check prerequisites and print install commands for missing tools, then exit. They do **not** auto-install anything — you install the missing tools yourself and retry.

| Prerequisite | Required for | Install command |
|---|---|---|
| **Python 3.12+** | All commands | `apt install python3.12` / `brew install python@3.12` / [python.org](https://www.python.org/downloads/) |
| **git** | `convert` | `apt install git` / `brew install git` / [git-scm.com](https://git-scm.com/downloads) |
| **uv** | Recommended (faster dep mgmt) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` / [astral.sh](https://docs.astral.sh/uv/) |

## Lint & Type Check

```powershell
# Install dev dependencies
uv sync --group dev

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy .
```

## Implementation Order

1. `models.py` + `manifest.py` — data structures first
2. `targets/base.py` + `targets/opencode/` — target interface + OpenCode module
3. `converter.py` — core conversion (reads CC source, delegates to target)
4. `installer.py` — install/remove logic
5. `convert.py` + `deploy.py` + `install.py` + `remove.py` + `swap.py` — CLI entry points importing the shared modules above

## Test Protocol

Test the launcher scripts in a **clean Docker container** to verify prerequisite detection and full pipeline.

### 1. Missing-Prereq Test (no Python)

```bash
docker run -d --name test-agent -w /test \
  -v "$PWD":/test ubuntu:24.04 sleep 3600

docker exec test-agent bash /test/agents.sh convert --help 2>&1
# → "Missing: Python 3.12+" then "Install the missing tools above..."  exit 1

docker kill test-agent; docker rm test-agent
```

### 2. Full Pipeline Test (with deps)

```bash
docker run -d --name test-agent -w /test \
  -v "$PWD":/test ubuntu:24.04 sleep 3600

docker exec test-agent bash -c '
  export PATH="$HOME/.local/bin:$PATH"

  # Install deps & run full pipeline (convert clones wshobson/agents from GitHub)
  cd /test
  DEBIAN_FRONTEND=noninteractive apt update -qq
  DEBIAN_FRONTEND=noninteractive apt install -y python3.12 python3.12-venv git
  uv sync --group dev
  bash agents.sh convert --output /tmp/out
  bash agents.sh deploy --target opencode --source /tmp/out --dest /tmp/dest
  echo "Model after install: $(grep "model:" /tmp/dest/agents/python-development/python-pro.md)"
  bash agents.sh swap --target opencode --dest /tmp/dest opus gpt-4o
  echo "Model after swap: $(grep "model:" /tmp/dest/agents/python-development/python-pro.md)"
  bash agents.sh remove --target opencode --dest /tmp/dest --force
'

docker kill test-agent; docker rm test-agent
```

**Expected**: Convert clones wshobson/agents → converts 80+ plugins (185 agents, 100 commands, 153 skills) → Deploy (427 files, model auto-mapped `opus→anthropic/claude-opus-4-20250514`) → Swap (54 agents `opus→gpt-4o`) → Remove (files cleaned up).

### 3. Python Direct (no launcher scripts)

```bash
uv run python convert.py --source /tmp/src --output /tmp/out
uv run python deploy.py --target opencode --source /tmp/out --dest /tmp/dest
uv run python swap.py --target opencode --dest /tmp/dest opus gpt-4o
uv run python remove.py --target opencode --dest /tmp/dest --force
```

For the Python direct path, `--source` is still needed because the Python CLIs don't have the auto-clone logic (that's in the launcher scripts). Use a local clone or the fixture approach.

---

## Windows Test Protocol

Test `agents.ps1` in a **Windows Docker container** (requires Docker Desktop in Windows container mode). Use `mcr.microsoft.com/windows/servercore:ltsc2022` as the base image.

### W1. Missing-Prereq Test

```powershell
docker run -d --name test-win -v "$PWD:C:\test" `
  -w C:\test mcr.microsoft.com/windows/servercore:ltsc2022 `
  powershell -Command "Start-Sleep 3600"

docker exec test-win powershell -Command "C:\test\agents.ps1 convert --help 2>&1"
```

**Expected**: Python 3.12+ not found → "Missing prerequisites" → "Install the missing tools above, open a new terminal, and retry." → exit 1.

### W2. Full Pipeline Test

Install prerequisites manually, then run the full pipeline:

```powershell
docker exec test-win powershell -Command @"
  Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile C:\python-installer.exe -UseBasicParsing
  Start-Process C:\python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait; Remove-Item C:\python-installer.exe
  Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe' -OutFile C:\git-installer.exe -UseBasicParsing
  Start-Process C:\git-installer.exe -ArgumentList '/VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES' -Wait; Remove-Item C:\git-installer.exe
  powershell -ExecutionPolicy ByPass -c "Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -OutFile C:\uv-install.ps1 -UseBasicParsing"
  powershell -ExecutionPolicy ByPass C:\uv-install.ps1; Remove-Item C:\uv-install.ps1
"@

# Run pipeline via launcher (container-local venv to avoid mount permission issues)
docker exec test-win powershell -Command @"
  `$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  `$userBin = "`$env:USERPROFILE\.local\bin"
  if (Test-Path `$userBin) { `$env:Path = "`$userBin;`$env:Path" }
  `$env:UV_PROJECT_ENVIRONMENT = "C:\work\.venv"

  cd C:\test
  uv sync --group dev 2>&1 | Select-Object -Last 3
  C:\test\agents.ps1 convert --output C:\tmp\out
  C:\test\agents.ps1 deploy --target opencode --source C:\tmp\out --dest C:\tmp\dest
  Select-String "model:" C:\tmp\dest\agents\python-development\python-pro.md
  C:\test\agents.ps1 swap --target opencode --dest C:\tmp\dest opus gpt-4o
  Select-String "model:" C:\tmp\dest\agents\python-development\python-pro.md
  C:\test\agents.ps1 remove --target opencode --dest C:\tmp\dest --force
"@
```

**Expected**: Convert clones wshobson/agents → converts 80+ plugins → Deploy (model auto-mapped) → Swap (→ `gpt-4o`) → Remove (files cleaned up).

### W3. Python Direct (no launcher scripts)

```powershell
uv run python convert.py --source C:\tmp\src --output C:\tmp\out
uv run python deploy.py --target opencode --source C:\tmp\out --dest C:\tmp\dest
uv run python swap.py --target opencode --dest C:\tmp\dest opus gpt-4o
uv run python remove.py --target opencode --dest C:\tmp\dest --force
```

## Conventions

- All functions **must** have full type annotations
- Prefer `pathlib.Path` over `os.path`
- Use Pydantic models for all data structures
- Each command (`convert`, `deploy`, `install`, `remove`, `swap`) is a standalone `.py` file that imports the appropriate shared module
- The manifest is always the source of truth for deployment state
- All manifest paths use POSIX-style `/` separators (use `Path.as_posix()` when constructing rel keys)
