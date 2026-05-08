from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ModelTier(str, Enum):
    opus = "opus"
    sonnet = "sonnet"
    haiku = "haiku"
    inherit = "inherit"


class PluginInfo(BaseModel):
    name: str
    version: str
    description: str
    author: dict[str, str] | None = None
    license: str | None = None
    category: str | None = None
    homepage: str | None = None


class MarketplaceEntry(BaseModel):
    name: str
    source: str
    version: str
    description: str
    author: dict[str, str] | None = None
    category: str | None = None
    homepage: str | None = None
    license: str | None = None


class MarketplaceData(BaseModel):
    plugins: list[MarketplaceEntry]


class CCAgent(BaseModel):
    name: str
    description: str
    model: str | None = None
    color: str | None = None
    tools: list[str] | None = None
    body: str = ""
    source_plugin: str = ""


class CCCommand(BaseModel):
    name: str
    description: str
    argument_hint: str | None = None
    body: str = ""
    source_plugin: str = ""


class CCSkill(BaseModel):
    name: str
    description: str
    body: str = ""
    source_plugin: str = ""


class ConvertedAgent(BaseModel):
    name: str
    content: str
    original_model: str | None = None


class ConvertedCommand(BaseModel):
    name: str
    content: str


class ConvertedSkill(BaseModel):
    name: str
    content: str


class ConversionResult(BaseModel):
    agents: list[ConvertedAgent]
    commands: list[ConvertedCommand]
    skills: list[ConvertedSkill]


class SourceCheckWarning(BaseModel):
    message: str
    plugin: str | None = None


class ManifestFileEntry(BaseModel):
    source: str
    checksum: str


class ManifestData(BaseModel):
    version: int = 1
    installed_at: str = ""
    source: str = ""
    target: str = ""
    files: dict[str, ManifestFileEntry] = Field(default_factory=dict)
    agent_models: dict[str, dict[str, str]] = Field(default_factory=dict)


def generate_timestamp() -> str:
    return datetime.now().isoformat()
