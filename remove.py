from __future__ import annotations

from pathlib import Path

import typer

from installer import remove
from targets.base import MigrationTarget
from targets.opencode.target import OpenCodeMigrationTarget

app = typer.Typer()


def _load_target(name: str) -> MigrationTarget:
    if name == "opencode":
        return OpenCodeMigrationTarget()
    raise typer.BadParameter(f"Unknown target: {name}")


@app.command()
def main(
    target: str = typer.Option("opencode", "--target", help="Target platform name"),
    dest: Path | None = typer.Option(
        None,
        "--dest",
        help="Install destination (default: target-global or project-local)",
    ),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    target_impl = _load_target(target)
    resolved_dest = target_impl.resolve_dest(dest)

    removed = remove(target_impl, resolved_dest, force=force)
    if removed:
        print(f"Removed deployment from {resolved_dest}")
    else:
        print("Nothing to remove (no manifest found or cancelled)")


if __name__ == "__main__":
    app()
