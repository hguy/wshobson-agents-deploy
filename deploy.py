from __future__ import annotations

from pathlib import Path

import typer

from installer import install
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
    source: Path | None = typer.Option(
        None,
        "--source",
        help="Source directory with converted files (default: ./<target output dir>)",
    ),
    dest: Path | None = typer.Option(
        None,
        "--dest",
        help="Install destination (default: target-global or project-local)",
    ),
) -> None:
    target_impl = _load_target(target)

    if source is None:
        source = Path.cwd() / target_impl.default_source_dir()

    resolved_dest = target_impl.resolve_dest(dest)

    if not source.exists():
        print(f"Error: source directory not found: {source}")
        raise typer.Exit(1)

    manifest = install(target_impl, source, resolved_dest)

    validation_errors = target_impl.validate_install(resolved_dest)
    if validation_errors:
        for e in validation_errors:
            print(f"[ERROR] {e}")
        raise typer.Exit(1)

    print(f"Deployed {len(manifest.files)} files to {resolved_dest}")


if __name__ == "__main__":
    app()
