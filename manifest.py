from __future__ import annotations

import hashlib
import json
from pathlib import Path

from models import ManifestData


def compute_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(path: Path) -> ManifestData | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return ManifestData(**data)


def write_manifest(path: Path, manifest: ManifestData) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.model_dump(), indent=2, default=str))


def delete_manifest(path: Path) -> None:
    if path.exists():
        path.unlink()
