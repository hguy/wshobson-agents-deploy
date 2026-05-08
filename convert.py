from __future__ import annotations

import sys
from pathlib import Path

import typer

from converter import clone_or_fetch_source, convert, sanity_check, validate_conversion
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
    source_repo: str = typer.Option(
        "https://github.com/wshobson/agents",
        "--source-repo",
        help="GitHub URL of the CC agents repo",
    ),
    source_branch: str = typer.Option(
        "main",
        "--source-branch",
        help="Branch to check out",
    ),
    cache_dir: Path = typer.Option(
        Path.home() / ".cache" / "wshobson-agents",
        "--cache-dir",
        help="Where to clone the source repo",
    ),
    source: Path | None = typer.Option(
        None,
        "--source",
        help="Local path to CC source (skips clone)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Output directory for converted files",
    ),
) -> None:
    target_impl = _load_target(target)

    if source is not None:
        source_root = source.resolve()
    else:
        source_root = cache_dir.resolve()
        clone_or_fetch_source(source_repo, source_branch, source_root)

    if output is None:
        output = Path.cwd() / target_impl.output_dir()

    warnings = sanity_check(source_root)
    if warnings:
        for w in warnings:
            tag = f"[{w.plugin}]" if w.plugin else ""
            print(f"[WARN] {tag} {w.message}", file=sys.stderr)
        print(f"[WARN] {len(warnings)} warning(s), continuing...", file=sys.stderr)

    result = convert(target_impl, source_root, output)

    validation_errors = validate_conversion(output)
    if validation_errors:
        for e in validation_errors:
            print(f"[ERROR] {e}", file=sys.stderr)
        raise typer.Exit(1)

    agent_count = len(result.agents)
    command_count = len(result.commands)
    skill_count = len(result.skills)
    print(f"Converted {agent_count} agents, {command_count} commands, {skill_count} skills")
    print(
        "[NOTE] Not all content is fully portable — some commands, skills, and agents"
        " reference Claude Code-specific features (.claude/ paths, PreToolUse hooks,"
        " env vars) and may not function correctly in other clients.",
        file=sys.stderr,
    )
    print(f"Output: {output.resolve()}")


if __name__ == "__main__":
    app()
