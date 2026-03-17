"""Typer CLI entry point."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config
from .models import JobState
from .pipeline import Pipeline, load_spec_file, detect_spec_file
from .storage import cleanup_jobs, get_latest_job, list_jobs

# Convention directories (relative to project root)
SOURCE_DIR = Path("source")
TO_CUT_DIR = SOURCE_DIR / "to_cut"
IN_PROGRESS_DIR = SOURCE_DIR / "in_progress"
DONE_DIR = SOURCE_DIR / "done"

# Brand → spec file mapping. Aspect ratio is auto-detected from the source.
BRAND_SPECS = {
    "dbexpertai": {
        "16:9": "config/cut_specs/landscape-dbexpertai.json",
        "9:16": "config/cut_specs/portrait-dbexpertai.json",
    },
    "founder": {
        "16:9": "config/cut_specs/landscape-founder.json",
        "9:16": "config/cut_specs/portrait-founder.json",
    },
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

app = typer.Typer(
    name="videngine",
    help="Automated video production pipeline with AI-driven editing.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def cut(
    brand: Annotated[
        Optional[str], typer.Option(help="Brand: dbexpertai or founder (overrides subdir detection)")
    ] = None,
    no_voice: Annotated[bool, typer.Option("--no-voice", help="Skip voice cloning")] = False,
    review: Annotated[bool, typer.Option(help="Pause after AI analysis for review")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would run without executing")] = False,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Process all videos in source/to_cut/.

    Drop video files into source/to_cut/dbexpertai/ or source/to_cut/founder/.
    The brand subdir determines which branding (intro/outro/watermark) to use.
    Aspect ratio is auto-detected from each file.

    Files move through: to_cut → in_progress → done.
    """
    config = load_config(config_file)

    # Ensure dirs exist
    for d in [TO_CUT_DIR, IN_PROGRESS_DIR, DONE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Find all video files in to_cut/ (including brand subdirs)
    files_to_process: list[tuple[Path, str]] = []  # (path, brand)
    for f in sorted(TO_CUT_DIR.rglob("*")):
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            # Detect brand from subdir
            detected_brand = brand
            if not detected_brand:
                rel = f.relative_to(TO_CUT_DIR)
                if rel.parts[0] in BRAND_SPECS:
                    detected_brand = rel.parts[0]
                else:
                    detected_brand = "dbexpertai"  # default
            files_to_process.append((f, detected_brand))

    if not files_to_process:
        console.print("[dim]No video files in source/to_cut/[/dim]")
        return

    console.print(f"\n[bold]Found {len(files_to_process)} video(s) to process[/bold]\n")

    for video_path, video_brand in files_to_process:
        console.print(f"[bold cyan]{'─' * 60}[/bold cyan]")
        console.print(f"[bold]File:[/bold] {video_path.name}")
        console.print(f"[bold]Brand:[/bold] {video_brand}")

        # Move to in_progress
        in_progress_path = IN_PROGRESS_DIR / video_path.name
        shutil.move(str(video_path), str(in_progress_path))

        try:
            # Detect aspect ratio → pick spec file
            from .ffmpeg.probe import probe
            info = probe(str(in_progress_path))
            aspect = "16:9" if info.width >= info.height else "9:16"

            specs_path = BRAND_SPECS.get(video_brand, {}).get(aspect)
            if not specs_path or not Path(specs_path).exists():
                console.print(f"[red]No spec file for brand={video_brand} aspect={aspect}[/red]")
                shutil.move(str(in_progress_path), str(TO_CUT_DIR / video_path.name))
                continue

            console.print(f"[bold]Specs:[/bold] {specs_path} ({aspect})")

            pipeline = Pipeline(
                source_file=str(in_progress_path),
                config=config,
                project=video_path.stem,
                specs_file=specs_path,
                no_voice=no_voice,
                review=review,
                dry_run=dry_run,
            )
            pipeline.run()

            # Move to done
            done_path = DONE_DIR / video_path.name
            shutil.move(str(in_progress_path), str(done_path))
            console.print(f"[green]Moved to {done_path}[/green]\n")

        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            # Move back to to_cut so it can be retried
            fallback = TO_CUT_DIR / video_path.name
            if in_progress_path.exists():
                shutil.move(str(in_progress_path), str(fallback))
            console.print(f"[yellow]Moved back to {fallback}[/yellow]\n")


@app.command()
def process(
    video: Annotated[Path, typer.Argument(help="Path to source video file")],
    project: Annotated[str, typer.Option(help="Project name for organization")] = "",
    specs: Annotated[
        Optional[Path], typer.Option("--specs", help="Path to JSON file with cut specs (auto-detects from source aspect ratio if omitted)")
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
    """Process a video through the AI-driven multi-cut pipeline.

    Aspect ratio is auto-detected from the source video. Landscape (16:9) and
    portrait (9:16) sources each have their own default cut specs under
    config/cut_specs/. Override with --specs to provide a custom spec file.
    """
    if not video.exists():
        console.print(f"[red]Video file not found: {video}[/red]")
        raise typer.Exit(1)

    config = load_config(config_file)

    if model:
        config.ai.model = model

    pipeline = Pipeline(
        source_file=str(video),
        config=config,
        project=project,
        specs_file=str(specs) if specs else None,
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
