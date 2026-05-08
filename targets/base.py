from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class MigrationTarget(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def convert_agent(self, frontmatter: dict[str, Any], body: str) -> str: ...

    @abstractmethod
    def convert_command(self, frontmatter: dict[str, Any], body: str) -> str: ...

    @abstractmethod
    def convert_skill(self, frontmatter: dict[str, Any], body: str) -> str: ...

    @abstractmethod
    def output_dir(self) -> str: ...

    @abstractmethod
    def project_config_dir(self) -> str: ...

    @abstractmethod
    def global_config_dir(self) -> Path: ...

    @abstractmethod
    def manifest_filename(self) -> str: ...

    @abstractmethod
    def model_mapping(self) -> dict[str, str | None]: ...

    @abstractmethod
    def validate_install(self, dest: Path) -> list[str]: ...

    @abstractmethod
    def resolve_dest(self, dest: Path | None) -> Path: ...

    @abstractmethod
    def default_source_dir(self) -> str: ...

    @abstractmethod
    def default_manifest_path(self, dest: Path) -> Path: ...
