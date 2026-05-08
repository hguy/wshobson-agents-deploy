# Wshobson Agents Anywhere

Deploys [wshobson/agents](https://github.com/wshobson/agents) — intelligent automation and multi-agent orchestration for Claude Code — to your agent platform of choice.

The [wshobson/agents](https://github.com/wshobson/agents) repository provides 80+ plugins with 185 specialized agents and 150+ skills covering development, DevOps, security, data engineering, UI design, and more. This tool converts those Claude Code agents to [OpenCode](https://opencode.ai) (default), Pi, Hermes, or other targets so you're not locked into a single client.

## Quick Start

```bash
# Convert agents from the source repo
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
