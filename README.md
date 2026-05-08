# Wshobson Agents Anywhere

Deploys [wshobson/agents](https://github.com/wshobson/agents) — intelligent automation and multi-agent orchestration for Claude Code — to your agent platform of choice.

The [wshobson/agents](https://github.com/wshobson/agents) repository provides 80+ plugins with 185 specialized agents and 150+ skills covering development, DevOps, security, data engineering, UI design, and more. This tool converts those Claude Code agents to [OpenCode](https://opencode.ai) (default), Pi, Hermes, or other targets so you're not locked into a single client.

## Quick Start

```bash
# Convert + deploy in one step
./agents.ps1 install              # Windows
./agents.sh install               # macOS/Linux

# Or do it step by step:
./agents.sh convert              # convert only
./agents.sh deploy               # deploy only (uses converted output)

# Swap models for all opus agents to gpt-4o
./agents.sh swap opus openai/gpt-4o     

# Remove deployed agents
./agents.sh remove
```

## Documentation

| File | Contents |
|------|----------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Target interface, tech stack, implementation files, source repo management |
| [FORMATS.md](./FORMATS.md) | CC source format, target format references |
 | [COMMANDS.md](./COMMANDS.md) | CLI commands (`convert`, `deploy`, `install`, `remove`, `swap`), manifest format, validation |
| [AGENTS.md](./AGENTS.md) | Repo rules for the implementation agent (build/lint/typecheck commands) |

## Portability Notice

The wshobson/agents marketplace was designed for Claude Code. While conversion makes agents, commands, and skills available in other clients, some content is inherently CC-specific:

- **~22 files** reference CC-only features like `.claude/` config paths, `PreToolUse`/`PostToolUse` hooks, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, and `claude plugin install` CLI commands
- These files are still converted and deployed — they just may not function as intended on other platforms
- A `[NOTE]` line is printed during conversion listing the common CC-specific patterns to watch for

This is expected behavior: the conversion is a best-effort migration, not a rewrite of agent logic.


