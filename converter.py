from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from re import Match
from typing import Any

import yaml

from models import (
    CCAgent,
    CCCommand,
    CCSkill,
    ConversionResult,
    ConvertedAgent,
    ConvertedCommand,
    ConvertedSkill,
    SourceCheckWarning,
)
from targets.base import MigrationTarget

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
AGENT_REF_RE = re.compile(r"(?<!\w)@([a-z0-9]+(-[a-z0-9]+)*)")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    front = yaml.safe_load(match.group(1)) or {}
    body = text[match.end() :]
    return front, body


def clone_or_fetch_source(
    repo_url: str,
    branch: str,
    cache_dir: Path,
) -> Path:
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(cache_dir)],
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "fetch", "origin"],
            check=True,
            capture_output=True,
            cwd=str(cache_dir),
        )
        subprocess.run(
            ["git", "reset", "--hard", f"origin/{branch}"],
            check=True,
            capture_output=True,
            cwd=str(cache_dir),
        )
    return cache_dir


def _warn_long(warnings: list[SourceCheckWarning], msg: str, plugin: str | None = None) -> None:
    warnings.append(SourceCheckWarning(message=msg, plugin=plugin))


def _resolve_plugin_dir(source_root: Path, entry: dict[str, Any]) -> Path | None:
    """Resolve plugin directory from a marketplace plugin entry.

    Returns None for external plugins (source is a dict) or if the path is invalid.
    """
    src = entry.get("source", "")
    if isinstance(src, dict):
        return None
    plugin_dir = source_root / str(src)
    return plugin_dir.resolve() if plugin_dir.exists() else None


def sanity_check(source_root: Path) -> list[SourceCheckWarning]:
    warnings: list[SourceCheckWarning] = []

    marketplace_path = source_root / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        _warn_long(
            warnings,
            "marketplace.json not found at .claude-plugin/marketplace.json",
        )
        return warnings

    try:
        marketplace_data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as e:
        _warn_long(warnings, f"marketplace.json is not valid JSON: {e}")
        return warnings

    if "plugins" not in marketplace_data or not isinstance(marketplace_data["plugins"], list):
        _warn_long(warnings, "marketplace.json missing 'plugins' array")
        return warnings

    plugins = marketplace_data["plugins"]

    seen_agent_names: dict[str, str] = {}
    seen_command_names: dict[str, str] = {}
    seen_skill_names: dict[str, str] = {}

    for entry in plugins:
        plugin_name: str = entry.get("name", "unknown")
        plugin_dir = _resolve_plugin_dir(source_root, entry)
        if plugin_dir is None:
            src = entry.get("source", "")
            src_desc = str(src) if isinstance(src, dict) else src
            _warn_long(warnings, f"Skipping external plugin: {src_desc}", plugin_name)
            continue

        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not plugin_json_path.exists():
            _warn_long(warnings, "plugin.json not found", plugin_name)
        else:
            try:
                pj = json.loads(plugin_json_path.read_text(encoding="utf-8"))
                if pj.get("name") != plugin_name:
                    msg = (
                        f"plugin.json name '{pj.get('name')}' doesn't match "
                        f"marketplace entry '{plugin_name}'"
                    )
                    _warn_long(warnings, msg, plugin_name)
            except (json.JSONDecodeError, ValueError):
                _warn_long(warnings, "plugin.json is not valid JSON", plugin_name)

        agents_dir = plugin_dir / "agents"
        if agents_dir.exists():
            for agent_file in sorted(agents_dir.glob("*.md")):
                front, _ = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
                name = front.get("name", "")
                if not name:
                    _warn_long(
                        warnings,
                        f"Agent file {agent_file.name} missing 'name' in frontmatter",
                        plugin_name,
                    )
                elif not NAME_RE.match(name):
                    _warn_long(
                        warnings,
                        f"Agent name '{name}' doesn't match naming convention",
                        plugin_name,
                    )
                if not front.get("description"):
                    _warn_long(
                        warnings,
                        f"Agent '{name}' missing 'description' in frontmatter",
                        plugin_name,
                    )
                if name:
                    key = f"agents/{name}"
                    if key in seen_agent_names:
                        msg = (
                            f"Duplicate agent name '{name}' "
                            f"(plugins: {seen_agent_names[key]}, {plugin_name})"
                        )
                        _warn_long(warnings, msg, plugin_name)
                    else:
                        seen_agent_names[key] = plugin_name

        commands_dir = plugin_dir / "commands"
        if commands_dir.exists():
            for cmd_file in sorted(commands_dir.glob("*.md")):
                front, _ = parse_frontmatter(cmd_file.read_text(encoding="utf-8"))
                cmd_name = cmd_file.stem
                if not cmd_name:
                    _warn_long(
                        warnings,
                        f"Command file {cmd_file.name} has no name",
                        plugin_name,
                    )
                elif not NAME_RE.match(cmd_name):
                    _warn_long(
                        warnings,
                        f"Command name '{cmd_name}' doesn't match naming convention",
                        plugin_name,
                    )
                if not front.get("description"):
                    _warn_long(
                        warnings,
                        f"Command '{cmd_name}' missing 'description' in frontmatter",
                        plugin_name,
                    )
                key = f"commands/{cmd_name}"
                if key in seen_command_names:
                    msg = (
                        f"Duplicate command name '{cmd_name}' "
                        f"(plugins: {seen_command_names[key]}, {plugin_name})"
                    )
                    _warn_long(warnings, msg, plugin_name)
                else:
                    seen_command_names[key] = plugin_name

        skills_dir = plugin_dir / "skills"
        if skills_dir.exists():
            for skill_dir_entry in sorted(skills_dir.glob("*")):
                if not skill_dir_entry.is_dir():
                    continue
                skill_md = skill_dir_entry / "SKILL.md"
                if not skill_md.exists():
                    continue
                front, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
                skill_name = front.get("name", "")
                if not skill_name:
                    _warn_long(
                        warnings,
                        f"Skill in {skill_dir_entry.name} missing 'name' in frontmatter",
                        plugin_name,
                    )
                elif not NAME_RE.match(skill_name):
                    _warn_long(
                        warnings,
                        f"Skill name '{skill_name}' doesn't match naming convention",
                        plugin_name,
                    )
                if not front.get("description"):
                    _warn_long(
                        warnings,
                        f"Skill '{skill_name}' missing 'description' in frontmatter",
                        plugin_name,
                    )
                if skill_dir_entry.name != skill_name:
                    msg = (
                        f"Skill directory '{skill_dir_entry.name}' doesn't match "
                        f"frontmatter name '{skill_name}'"
                    )
                    _warn_long(warnings, msg, plugin_name)
                if skill_name:
                    key = f"skills/{skill_name}"
                    if key in seen_skill_names:
                        msg = (
                            f"Duplicate skill name '{skill_name}' "
                            f"(plugins: {seen_skill_names[key]}, {plugin_name})"
                        )
                        _warn_long(warnings, msg, plugin_name)
                    else:
                        seen_skill_names[key] = plugin_name

        known_dirs = {"agents", "commands", "skills", ".claude-plugin"}
        for item in plugin_dir.iterdir():
            if item.is_dir() and item.name not in known_dirs:
                _warn_long(warnings, f"Orphan directory '{item.name}' in plugin", plugin_name)

    return warnings


def _load_raw_cc_source(
    source_root: Path,
) -> tuple[list[CCAgent], list[CCCommand], list[CCSkill]]:
    raw_agents: list[CCAgent] = []
    raw_commands: list[CCCommand] = []
    raw_skills: list[CCSkill] = []

    marketplace_path = source_root / ".claude-plugin" / "marketplace.json"
    marketplace_data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugins = marketplace_data.get("plugins", [])

    for entry in plugins:
        plugin_name: str = entry.get("name", "unknown")
        plugin_dir = _resolve_plugin_dir(source_root, entry)
        if plugin_dir is None:
            continue

        agents_dir = plugin_dir / "agents"
        if agents_dir.exists():
            for agent_file in sorted(agents_dir.glob("*.md")):
                front, body = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
                tools_raw = front.get("tools")
                tools: list[str] | None = None
                if tools_raw:
                    if isinstance(tools_raw, str):
                        tools = [t.strip() for t in tools_raw.split(",")]
                    elif isinstance(tools_raw, list):
                        tools = [str(t) for t in tools_raw]

                raw_agents.append(
                    CCAgent(
                        name=front.get("name", agent_file.stem),
                        description=front.get("description", ""),
                        model=front.get("model"),
                        color=front.get("color"),
                        tools=tools,
                        body=body,
                        source_plugin=plugin_name,
                    )
                )

        commands_dir = plugin_dir / "commands"
        if commands_dir.exists():
            for cmd_file in sorted(commands_dir.glob("*.md")):
                front, body = parse_frontmatter(cmd_file.read_text(encoding="utf-8"))
                raw_commands.append(
                    CCCommand(
                        name=cmd_file.stem,
                        description=front.get("description", ""),
                        argument_hint=front.get("argument-hint"),
                        body=body,
                        source_plugin=plugin_name,
                    )
                )

        skills_dir = plugin_dir / "skills"
        if skills_dir.exists():
            for skill_dir_entry in sorted(skills_dir.glob("*")):
                if not skill_dir_entry.is_dir():
                    continue
                skill_md = skill_dir_entry / "SKILL.md"
                if not skill_md.exists():
                    continue
                front, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
                raw_skills.append(
                    CCSkill(
                        name=front.get("name", skill_dir_entry.name),
                        description=front.get("description", ""),
                        body=body,
                        source_plugin=plugin_name,
                    )
                )

    return raw_agents, raw_commands, raw_skills


def _build_agent_ref_map(
    raw_agents: list[CCAgent],
) -> dict[str, list[tuple[str, str]]]:
    """Build map from base agent name -> [(plugin, prefixed_name), ...]."""
    ref_map: dict[str, list[tuple[str, str]]] = {}
    for agent in raw_agents:
        plugin = agent.source_plugin or "unknown"
        prefixed = f"{plugin}-{agent.name}"
        ref_map.setdefault(agent.name, []).append((plugin, prefixed))
    return ref_map


def _resolve_cross_refs(
    content: str,
    ref_map: dict[str, list[tuple[str, str]]],
    source_plugin: str | None = None,
) -> str:
    """Replace @agent-name references with @plugin-agent-name in body content."""

    def _replacer(m: Match[str]) -> str:
        base = m.group(1)
        candidates = ref_map.get(base)
        if not candidates:
            return m.group(0)
        if len(candidates) == 1:
            return f"@{candidates[0][1]}"
        if source_plugin:
            for plugin, prefixed in candidates:
                if plugin == source_plugin:
                    return f"@{prefixed}"
        return m.group(0)

    return AGENT_REF_RE.sub(_replacer, content)


def _find_name_collisions(
    items: Sequence[CCAgent | CCCommand | CCSkill],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item.name] = counts.get(item.name, 0) + 1
    return {name: cnt for name, cnt in counts.items() if cnt > 1}


def _print_collision_warn(
    label: str,
    collisions: dict[str, int],
) -> None:
    if not collisions:
        return
    sorted_c = sorted(collisions.items(), key=lambda x: -x[1])
    examples = ", ".join(f"{n} in {c} plugins" for n, c in sorted_c[:3])
    print(
        f"[WARN] {len(collisions)} {label} names collide across plugins "
        f"— prefixed with plugin name (e.g. {examples})",
        file=sys.stderr,
    )


def convert(
    target: MigrationTarget,
    source_root: Path,
    output_dir: Path,
) -> ConversionResult:
    raw_agents, raw_commands, raw_skills = _load_raw_cc_source(source_root)

    agent_collisions = _find_name_collisions(raw_agents)
    command_collisions = _find_name_collisions(raw_commands)
    skill_collisions = _find_name_collisions(raw_skills)

    _print_collision_warn("agent", agent_collisions)
    _print_collision_warn("command", command_collisions)
    _print_collision_warn("skill", skill_collisions)

    ref_map = _build_agent_ref_map(raw_agents)

    converted_agents: list[ConvertedAgent] = []
    converted_commands: list[ConvertedCommand] = []
    converted_skills: list[ConvertedSkill] = []

    agents_out = output_dir / "agents"
    agents_out.mkdir(parents=True, exist_ok=True)

    for agent in raw_agents:
        plugin = agent.source_plugin or "unknown"
        prefixed = f"{plugin}-{agent.name}"

        front: dict[str, Any] = {
            "name": prefixed,
            "description": agent.description,
        }
        if agent.model:
            front["model"] = agent.model
        if agent.color:
            front["color"] = agent.color
        if agent.tools:
            front["tools"] = ", ".join(agent.tools)

        content = target.convert_agent(front, agent.body)
        content = _resolve_cross_refs(content, ref_map, agent.source_plugin)
        agent_plugin_out = agents_out / plugin
        agent_plugin_out.mkdir(parents=True, exist_ok=True)
        (agent_plugin_out / f"{agent.name}.md").write_text(content, encoding="utf-8")

        converted_agents.append(
            ConvertedAgent(
                name=prefixed,
                content=content,
                original_model=agent.model,
            )
        )

    commands_out = output_dir / "commands"
    commands_out.mkdir(parents=True, exist_ok=True)

    for cmd in raw_commands:
        cmd_name = f"{cmd.source_plugin}-{cmd.name}" if cmd.name in command_collisions else cmd.name
        cmd_front: dict[str, Any] = {"description": cmd.description}
        if cmd.argument_hint:
            cmd_front["argument-hint"] = cmd.argument_hint
        content = target.convert_command(cmd_front, cmd.body)
        content = _resolve_cross_refs(content, ref_map, cmd.source_plugin)
        (commands_out / f"{cmd_name}.md").write_text(content, encoding="utf-8")
        converted_commands.append(ConvertedCommand(name=cmd_name, content=content))

    skills_out = output_dir / "skills"
    skills_out.mkdir(parents=True, exist_ok=True)

    for skill in raw_skills:
        skill_name = (
            f"{skill.source_plugin}-{skill.name}" if skill.name in skill_collisions else skill.name
        )
        front = {
            "name": skill_name,
            "description": skill.description,
        }
        content = target.convert_skill(front, skill.body)
        content = _resolve_cross_refs(content, ref_map, skill.source_plugin)
        skill_dir = skills_out / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        converted_skills.append(ConvertedSkill(name=skill.name, content=content))

    return ConversionResult(
        agents=converted_agents,
        commands=converted_commands,
        skills=converted_skills,
    )


def validate_conversion(output_dir: Path) -> list[str]:
    errors: list[str] = []
    for subdir in ["agents", "commands", "skills"]:
        d = output_dir / subdir
        if not d.exists():
            errors.append(f"Missing output directory: {d}")
            continue
        for f in sorted(d.glob("**/*.md")):
            front, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            if not front:
                errors.append(f"File {f} has no frontmatter")
                continue
            name = front.get("name", f.stem)
            if not NAME_RE.match(name):
                errors.append(f"Name '{name}' in {f} doesn't match convention")
    return errors
