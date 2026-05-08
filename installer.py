from __future__ import annotations

import platform
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from manifest import compute_checksum, read_manifest, write_manifest
from models import ManifestData, ManifestFileEntry, generate_timestamp
from targets.base import MigrationTarget

SKILLS_SUBDIR = "skills"
COMMANDS_SUBDIR = "commands"
AGENTS_SUBDIR = "agents"


def _copy_and_checksum(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return compute_checksum(dst)


def _read_agent_model(agent_path: Path) -> str | None:
    try:
        text = agent_path.read_text()
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            front = yaml.safe_load(m.group(1)) or {}
            return front.get("model")
    except Exception:
        pass
    return None


def _swap_agent_model(agent_path: Path, to_model: str) -> None:
    text = agent_path.read_text()
    fm = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
    m = fm.match(text)
    if not m:
        return
    front = yaml.safe_load(m.group(1)) or {}
    body = text[m.end() :]

    if to_model:
        front["model"] = to_model
    elif "model" in front:
        del front["model"]

    yaml_str = yaml.dump(
        front,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    ).strip()
    agent_path.write_text(f"---\n{yaml_str}\n---\n{body}")


def install(
    target: MigrationTarget,
    source: Path,
    dest: Path,
) -> ManifestData:
    manifest_path = target.default_manifest_path(dest)
    existing_manifest = read_manifest(manifest_path)
    is_first_install = existing_manifest is None

    manifest = ManifestData(
        version=1,
        installed_at=generate_timestamp(),
        source=str(source),
        target=str(dest),
    )

    files: dict[str, ManifestFileEntry] = {}
    agent_models: dict[str, dict[str, str]] = {}

    agents_src = source / AGENTS_SUBDIR
    if agents_src.exists():
        agents_dst = dest / AGENTS_SUBDIR
        for agent_file in sorted(agents_src.glob("**/*.md")):
            rel_path = agent_file.relative_to(agents_src)
            rel = f"agents/{rel_path.as_posix()}"
            dst_path = agents_dst / rel_path
            checksum = _copy_and_checksum(agent_file, dst_path)
            files[rel] = ManifestFileEntry(source=str(agent_file), checksum=checksum)

            if is_first_install:
                model = _read_agent_model(dst_path)
                if model:
                    agent_models[rel] = {"original": model}

    commands_src = source / COMMANDS_SUBDIR
    if commands_src.exists():
        commands_dst = dest / COMMANDS_SUBDIR
        commands_dst.mkdir(parents=True, exist_ok=True)
        for cmd_file in sorted(commands_src.glob("*.md")):
            rel = f"commands/{cmd_file.name}"
            dst_path = commands_dst / cmd_file.name
            checksum = _copy_and_checksum(cmd_file, dst_path)
            files[rel] = ManifestFileEntry(source=str(cmd_file), checksum=checksum)

    skills_src = source / SKILLS_SUBDIR
    if skills_src.exists():
        skills_dst = dest / SKILLS_SUBDIR
        for skill_dir in sorted(skills_src.glob("*")):
            if not skill_dir.is_dir():
                continue
            skill_md_src = skill_dir / "SKILL.md"
            if not skill_md_src.exists():
                continue
            rel = f"skills/{skill_dir.name}/SKILL.md"
            dst_skill_dir = skills_dst / skill_dir.name
            dst_skill_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_skill_dir / "SKILL.md"
            checksum = _copy_and_checksum(skill_md_src, dst_path)
            files[rel] = ManifestFileEntry(source=str(skill_md_src), checksum=checksum)

    manifest.files = files
    manifest.agent_models = agent_models

    if is_first_install:
        model_map = target.model_mapping()
        for rel_model, models in agent_models.items():
            original = models.get("original", "")
            if original in model_map:
                mapped = model_map[original]
                if mapped is not None:
                    agent_path = dest / rel_model
                    _swap_agent_model(agent_path, mapped)

    write_manifest(manifest_path, manifest)
    return manifest


def _is_opencode_running() -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq opencode.exe", "/NH"],
                capture_output=True, text=True, check=False,
            )
            return "opencode.exe" in result.stdout
        else:
            result = subprocess.run(
                ["pgrep", "-x", "opencode"],
                capture_output=True, text=True, check=False,
            )
            return result.returncode == 0
    except Exception:
        return False


def remove(target: MigrationTarget, dest: Path, force: bool = False) -> bool:
    if _is_opencode_running():
        print(
            "Error: OpenCode process is running — file locks may prevent deletion.\n"
            "Close OpenCode first, then retry.",
            file=__import__("sys").stderr,
        )
        return False

    manifest_path = target.default_manifest_path(dest)
    manifest = read_manifest(manifest_path)

    if manifest is None:
        return False

    if not force:
        file_count = len(manifest.files)
        response = input(f"Remove {file_count} deployed files and undo config changes? [y/N] ")
        if response.lower() != "y":
            return False

    for rel in manifest.files:
        file_path = dest / rel
        if file_path.exists():
            file_path.unlink()

    for rel in manifest.files:
        parent = (dest / rel).parent
        while parent != dest:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
            parent = parent.parent

    if manifest_path.exists():
        manifest_path.unlink()

    return True


def swap_models(
    target: MigrationTarget,
    dest: Path,
    from_model: str,
    to_model: str,
) -> int:
    manifest_path = target.default_manifest_path(dest)
    manifest = read_manifest(manifest_path)
    if manifest is None:
        return 0

    swapped = 0
    for rel, models in manifest.agent_models.items():
        original = models.get("original", "")
        if original != from_model:
            continue
        agent_path = dest / rel
        if agent_path.exists():
            _swap_agent_model(agent_path, to_model)
            swapped += 1

    return swapped
