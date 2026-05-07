# wshobson-agents-deploy

Converts [wshobson/agents](https://github.com/wshobson/agents) (Claude Code format) to any supported agent platform. Architecture is **target-pluggable**: source is always CC, output is OpenCode (default), Pi, Hermes, etc.

## Quick Start

```bash
# Convert agents from the upstream repo
./agents.ps1 convert              # Windows
./agents.sh convert               # macOS/Linux

# Install into ~/.config/opencode/
./agents.ps1 install
./agents.sh install

# Swap models for all opus agents to gpt-4o
./agents.ps1 swap opus gpt-4o
./agents.sh swap opus gpt-4o

# Remove deployed agents
./agents.ps1 remove
./agents.sh remove
```

## Documentation

| File | Contents |
|------|----------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Target interface, tech stack, implementation files, source repo management |
| [FORMATS.md](./FORMATS.md) | CC source format, target format references |
| [COMMANDS.md](./COMMANDS.md) | CLI commands (`convert`, `install`, `remove`, `swap`), manifest format, validation |
| [AGENTS.md](./AGENTS.md) | Repo rules for the implementation agent (build/lint/typecheck commands) |
