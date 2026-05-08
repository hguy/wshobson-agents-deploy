from __future__ import annotations

from pathlib import Path

import typer

from installer import swap_models
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
    from_model: str = typer.Argument(
        ...,
        help="Original model tier (opus, sonnet, haiku, inherit)",
    ),
    to_model: str = typer.Argument(..., help="Target model ID to swap to"),
    dest: Path | None = typer.Option(
        None,
        "--dest",
        help="Install destination (default: target-global or project-local)",
    ),
) -> None:
    target_impl = _load_target(target)
    resolved_dest = target_impl.resolve_dest(dest)

    count = swap_models(target_impl, resolved_dest, from_model, to_model)
    if count > 0:
        print(f"Swapped {count} agent(s) from '{from_model}' to '{to_model}'")
    else:
        print(f"No agents found with original model '{from_model}'")


if __name__ == "__main__":
    app()
