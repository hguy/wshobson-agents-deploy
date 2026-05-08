from __future__ import annotations

from pathlib import Path
from typing import Any

from targets.base import MigrationTarget
from targets.opencode.formatting import (
    MODEL_MAP,
    format_agent_file,
    format_command_file,
    format_skill_file,
)


class OpenCodeMigrationTarget(MigrationTarget):
    def name(self) -> str:
        return "opencode"

    def convert_agent(self, frontmatter: dict[str, Any], body: str) -> str:
        return format_agent_file(frontmatter, body)

    def convert_command(self, frontmatter: dict[str, Any], body: str) -> str:
        return format_command_file(frontmatter, body)

    def convert_skill(self, frontmatter: dict[str, Any], body: str) -> str:
        return format_skill_file(frontmatter, body)

    def output_dir(self) -> str:
        return "opencode"

    def project_config_dir(self) -> str:
        return ".opencode"

    def global_config_dir(self) -> Path:
        return Path.home() / ".config" / "opencode"

    def manifest_filename(self) -> str:
        return "wshobson-agents-manifest.json"

    def model_mapping(self) -> dict[str, str | None]:
        return dict(MODEL_MAP)

    def validate_install(self, dest: Path) -> list[str]:
        errors: list[str] = []
        agents_dir = dest / "agents"
        if not agents_dir.exists():
            errors.append(f"agents directory not found at {agents_dir}")
        return errors

    def resolve_dest(self, dest: Path | None) -> Path:
        if dest is not None:
            if (dest / ".git").exists():
                return dest / self.project_config_dir()
            return dest
        return self.global_config_dir()

    def config_format(self, dest: Path) -> str:
        jsonc_path = dest / "opencode.jsonc"
        if jsonc_path.exists():
            return "jsonc"
        return "json"

    def default_source_dir(self) -> str:
        return self.output_dir()

    def default_manifest_path(self, dest: Path) -> Path:
        return dest / self.manifest_filename()
