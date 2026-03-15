"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config
from .models import JobState
from .pipeline import Pipeline
from .storage import cleanup_jobs, get_latest_job, list_jobs

app = typer.Typer(
    name="videngine",
    help="Automated video production pipeline with AI-driven editing.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def process(
    video: Annotated[Path, typer.Argument(help="Path to source video file")],
    project: Annotated[str, typer.Option(help="Project name for organization")] = "",
    target_duration: Annotated[
        Optional[float], typer.Option("--target-duration", help="Target output duration in seconds")
    ] = None,
    ratios: Annotated[
        Optional[str], typer.Option(help="Comma-separated output ratios: 16x9,9x16,4x5")
    ] = None,
    no_voice: Annotated[bool, typer.Option("--no-voice", help="Skip voice cloning")] = False,
    review: Annotated[bool, typer.Option(help="Pause after AI analysis for review")] = False,
    model: Annotated[
        Optional[str], typer.Option(help="Override AI model")
    ] = None,
    keep_intermediates: Annotated[
        bool, typer.Option("--keep-intermediates", help="Keep intermediate files")
    ] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would run without executing")] = False,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Process a video through the AI-driven editing pipeline."""
    if not video.exists():
        console.print(f"[red]Video file not found: {video}[/red]")
        raise typer.Exit(1)

    config = load_config(config_file)

    if model:
        config.ai.model = model

    ratio_list = ratios.split(",") if ratios else None

    pipeline = Pipeline(
        source_file=str(video),
        config=config,
        project=project,
        target_duration=target_duration,
        ratios=ratio_list,
        no_voice=no_voice,
        review=review,
        dry_run=dry_run,
    )
    pipeline.run()


@app.command()
def resume(
    job_id: Annotated[
        Optional[str], typer.Argument(help="Job ID to resume")
    ] = None,
    latest: Annotated[bool, typer.Option("--latest", help="Resume most recent job")] = False,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Resume a previously interrupted or failed job."""
    config = load_config(config_file)

    if latest:
        job = get_latest_job(config.paths.working_dir)
        if job is None:
            console.print("[red]No jobs found[/red]")
            raise typer.Exit(1)
        job_id = job.job_id
    elif job_id is None:
        console.print("[red]Provide a job ID or use --latest[/red]")
        raise typer.Exit(1)

    pipeline = Pipeline(
        source_file="",  # Will be loaded from job state
        config=config,
        job_id=job_id,
    )
    pipeline.run()


@app.command()
def jobs(
    status: Annotated[
        Optional[str], typer.Option(help="Filter by status: completed, failed, running")
    ] = None,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """List all jobs."""
    config = load_config(config_file)
    all_jobs = list_jobs(config.paths.working_dir, status=status)

    if not all_jobs:
        console.print("[dim]No jobs found[/dim]")
        return

    table = Table(title="Jobs")
    table.add_column("Job ID", style="cyan")
    table.add_column("Project")
    table.add_column("Created")
    table.add_column("Stages")

    for job in all_jobs:
        stages_summary = " ".join(
            f"[{'green' if s.status.value == 'completed' else 'red' if s.status.value == 'failed' else 'dim'}]{name[0].upper()}[/]"
            for name, s in job.stages.items()
        )
        table.add_row(
            job.job_id,
            job.project or "-",
            job.created_at.strftime("%Y-%m-%d %H:%M"),
            stages_summary,
        )

    console.print(table)


@app.command()
def cleanup(
    older_than: Annotated[str, typer.Option(help="Delete jobs older than (e.g. 7d)")] = "7d",
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Delete old completed jobs."""
    config = load_config(config_file)

    # Parse duration string
    days = int(older_than.rstrip("d"))
    deleted = cleanup_jobs(config.paths.working_dir, older_than_days=days)
    console.print(f"Deleted {deleted} job(s)")


if __name__ == "__main__":
    app()
