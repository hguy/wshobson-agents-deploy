from __future__ import annotations

from pydantic import BaseModel


class OpenCodePermissions(BaseModel):
    read: str | None = None
    edit: str | None = None
    write: str | None = None
    grep: str | None = None
    glob: str | None = None
    bash: str | None = None
    task: str | None = None
    webfetch: str | None = None
    websearch: str | None = None
    lsp: str | None = None
    skill: str | None = None
    todowrite: str | None = None
    question: str | None = None


class OpenCodeConfig(BaseModel):
    agents: list[dict[str, str]] = []
    commands: list[dict[str, str]] = []
    permissions: OpenCodePermissions | None = None
