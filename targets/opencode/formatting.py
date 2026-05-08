from __future__ import annotations

from typing import Any

import yaml

TOOL_MAP: dict[str, str] = {
    "Read": "read",
    "Edit": "edit",
    "Write": "write",
    "Grep": "grep",
    "Glob": "glob",
    "Bash": "bash",
    "Task": "task",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
    "LSP": "lsp",
    "Skill": "skill",
    "TodoWrite": "todowrite",
    "Question": "question",
}

MODEL_MAP: dict[str, str | None] = {
    "opus": "anthropic/claude-opus-4-20250514",
    "sonnet": "anthropic/claude-sonnet-4-20250514",
    "haiku": "anthropic/claude-haiku-4-20250514",
    "inherit": None,
}

COLOR_MAP: dict[str, str] = {
    "cyan": "#00BCD4",
    "blue": "#2196F3",
    "green": "#4CAF50",
    "magenta": "#E91E63",
    "red": "#F44336",
    "yellow": "#FFC107",
}

ALL_KNOWN_TOOLS = sorted(TOOL_MAP.values())


def _parse_tools(tools_val: object) -> list[str] | None:
    if tools_val is None:
        return None
    if isinstance(tools_val, list):
        return [str(t).strip() for t in tools_val]
    if isinstance(tools_val, str):
        return [t.strip() for t in tools_val.split(",")]
    return None


def convert_agent_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}

    result["name"] = frontmatter["name"]
    result["description"] = frontmatter["description"]

    model = frontmatter.get("model")
    if model and model != "inherit":
        result["model"] = model
    color = frontmatter.get("color")
    if color:
        result["color"] = COLOR_MAP.get(color, color)

    result["mode"] = "subagent"

    tools = _parse_tools(frontmatter.get("tools"))
    if tools is not None:
        allowed: set[str] = set()
        for t in tools:
            mapped = TOOL_MAP.get(t)
            if mapped:
                allowed.add(mapped)
        if allowed:
            permission = {t: "allow" for t in sorted(allowed)}
            result["permission"] = permission

    return result


def convert_command_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    result["description"] = frontmatter.get("description", "")
    return result


def convert_skill_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    result["name"] = frontmatter["name"]
    result["description"] = frontmatter["description"]
    return result


def dump_yaml_frontmatter(data: dict[str, Any]) -> str:
    yaml_str = yaml.dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=1000000,
    ).strip()
    return f"---\n{yaml_str}\n---\n"


def format_agent_file(frontmatter: dict[str, Any], body: str) -> str:
    converted = convert_agent_frontmatter(frontmatter)
    header = dump_yaml_frontmatter(converted)
    return header + body


def format_command_file(frontmatter: dict[str, Any], body: str) -> str:
    converted = convert_command_frontmatter(frontmatter)
    header = dump_yaml_frontmatter(converted)
    return header + body


def format_skill_file(frontmatter: dict[str, Any], body: str) -> str:
    converted = convert_skill_frontmatter(frontmatter)
    header = dump_yaml_frontmatter(converted)
    return header + body
