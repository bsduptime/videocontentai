"""Stage orchestrator with checkpointing."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .config import Config
from .ffmpeg.probe import probe
from .models import (
    Branding,
    CutPlan,
    CutSpec,
    CutSpecFile,
    JobState,
    SourceContext,
    StageResult,
    StageStatus,
    Transcript,
    VisualContext,
)

console = Console()

_BUNDLED_SPECS_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "cut_specs"


def load_spec_file(path: str | Path) -> CutSpecFile:
    """Load a cut spec file (pipeline + source + cuts)."""
    return CutSpecFile.model_validate_json(Path(path).read_text())


def detect_spec_file(source_file: str) -> CutSpecFile:
    """Auto-detect source aspect ratio, list matching spec files, pick the first.

    If multiple files match, prints them so the user knows to use --specs.
    """
    info = probe(source_file)
    is_landscape = info.width >= info.height
    aspect = "16:9" if is_landscape else "9:16"

    search_dirs = [Path("config/cut_specs"), _BUNDLED_SPECS_DIR]
    matches: list[tuple[Path, CutSpecFile]] = []

    for d in search_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                spec = load_spec_file(f)
                if spec.source.aspect_ratio == aspect:
                    matches.append((f, spec))
            except Exception:
                continue

    if not matches:
        raise FileNotFoundError(
            f"No spec files found for {aspect} source. "
            f"Provide --specs explicitly."
        )

    if len(matches) > 1:
        console.print(f"\n[yellow]Multiple spec files match {aspect} source:[/yellow]")
        for f, spec in matches:
            console.print(f"  {f}  ({spec.pipeline})")
        console.print(f"[yellow]Using first match. Override with --specs.[/yellow]\n")

    chosen_path, chosen_spec = matches[0]
    console.print(f"  [dim]Auto-detected {aspect} → {chosen_path} ({chosen_spec.pipeline})[/dim]")
    return chosen_spec


class Pipeline:
    def __init__(
        self,
        source_file: str,
        config: Config,
        project: str = "",
        specs_file: str | None = None,
        no_voice: bool = False,
        review: bool = False,
        dry_run: bool = False,
        job_id: str | None = None,
    ) -> None:
        self.source_file = str(Path(source_file).resolve()) if source_file else ""
        self.config = config
        self.project = project
        self.no_voice = no_voice
        self.review = review
        self.dry_run = dry_run

        # Create or load job
        if job_id:
            self.job = JobState.load(
                str(Path(config.paths.working_dir) / job_id)
            )
            self.spec_file = self.job.spec_file
            self.no_voice = self.job.no_voice
        else:
            if specs_file:
                self.spec_file = load_spec_file(specs_file)
            else:
                self.spec_file = detect_spec_file(self.source_file)
            self.job = self._create_job()

    @property
    def cut_specs(self) -> list[CutSpec]:
        return self.spec_file.cuts

    @property
    def source_context(self) -> SourceContext:
        return self.spec_file.source

    @property
    def branding(self) -> Branding:
        return self.spec_file.branding

    def _create_job(self) -> JobState:
        job_id = f"{self.project or 'job'}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        working_dir = Path(self.config.paths.working_dir) / job_id
        working_dir.mkdir(parents=True, exist_ok=True)

        job = JobState(
            job_id=job_id,
            source_file=self.source_file,
            working_dir=str(working_dir),
            project=self.project,
            spec_file=self.spec_file,
            no_voice=self.no_voice,
        )
        job.save()
        return job

    def run(self) -> JobState:
        """Run all pipeline stages, skipping completed ones."""
        console.print(f"\n[bold]Job:[/bold] {self.job.job_id}")
        console.print(f"[bold]Pipeline:[/bold] {self.spec_file.pipeline}")
        console.print(f"[bold]Source:[/bold] {self.job.source_file}")
        console.print(f"[bold]Working dir:[/bold] {self.job.working_dir}")
        console.print(f"[bold]Cuts:[/bold] {', '.join(f'{s.name} ({s.min_duration:.0f}-{s.max_duration:.0f}s)' for s in self.cut_specs)}\n")

        try:
            self._run_stage("transcribe", self._stage_transcribe)
            self._run_stage("analyze", self._stage_analyze)

            if self.review:
                self._review_pause()

            self._run_stage("cut", self._stage_cut)
            self._run_stage("watermark", self._stage_watermark)
            self._run_stage("intro_outro", self._stage_intro_outro)
            self._run_stage("hook_prepend", self._stage_hook_prepend)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Resume with:[/yellow]")
            console.print(f"  videngine resume {self.job.job_id}")
            raise SystemExit(1)

        console.print("\n[bold green]Pipeline complete![/bold green]")
        outputs = self.job.stages.get("hook_prepend", StageResult()).artifacts
        for spec_name, path in outputs.items():
            console.print(f"  {spec_name}: {path}")

        return self.job

    def _run_stage(self, name: str, func: callable) -> None:
        stage = self.job.stages[name]

        if stage.status == StageStatus.COMPLETED:
            console.print(f"  [dim]Stage {name}: already completed, skipping[/dim]")
            return

        console.print(f"  [bold cyan]Stage {name}:[/bold cyan] running...")
        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now(timezone.utc)
        self.job.save()

        try:
            if self.dry_run:
                console.print(f"    [dim](dry run — skipping execution)[/dim]")
            else:
                func()

            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now(timezone.utc)
            self.job.save()
            console.print(f"  [green]Stage {name}: done[/green]")

        except Exception as e:
            stage.status = StageStatus.FAILED
            stage.error = str(e)
            stage.completed_at = datetime.now(timezone.utc)
            self.job.save()
            console.print(f"  [red]Stage {name}: FAILED — {e}[/red]")
            raise

    def _skip_stage(self, name: str) -> None:
        stage = self.job.stages[name]
        stage.status = StageStatus.SKIPPED
        self.job.save()
        console.print(f"  [dim]Stage {name}: skipped[/dim]")

    def _review_pause(self) -> None:
        """Pause for user to review cut plans before proceeding."""
        plans_dir = Path(self.job.working_dir) / "cut_plans"
        if plans_dir.exists():
            console.print(f"\n[yellow]Review cut plans at:[/yellow]")
            console.print(f"  {plans_dir}")
            for f in sorted(plans_dir.glob("*.json")):
                console.print(f"    {f.name}")
            console.print("[yellow]Press Enter to continue or Ctrl+C to abort...[/yellow]")
            input()

    # --- Stage implementations ---

    def _stage_transcribe(self) -> None:
        from .stages.transcribe import run_transcribe, run_visual_analysis

        run_transcribe(
            self.job.source_file, self.job.working_dir, self.config
        )
        run_visual_analysis(
            self.job.source_file, self.job.working_dir,
        )
        self.job.stages["transcribe"].artifacts = {
            "transcript": "transcript.json",
            "audio": "audio.wav",
            "visual_context": "visual_context.json",
        }

    def _stage_analyze(self) -> None:
        from .stages.analyze import run_analyze

        transcript = self._load_transcript()
        visual_context = self._load_visual_context()
        cut_plans = run_analyze(
            transcript, self.job.working_dir, self.config,
            self.cut_specs, self.source_context,
            visual_context=visual_context,
        )
        artifacts = {"_analysis": "cut_plans/_analysis.json"}
        for plan in cut_plans:
            artifacts[plan.spec_name] = f"cut_plans/{plan.spec_name}.json"
        self.job.stages["analyze"].artifacts = artifacts

    def _stage_cut(self) -> None:
        from .stages.cut import run_cut

        cut_plans = self._load_cut_plans()
        clip_paths = run_cut(
            cut_plans, self.job.source_file, self.job.working_dir, self.config,
            cut_specs=self.cut_specs,
        )
        self.job.stages["cut"].artifacts = {
            name: f"clips/{name}/raw.mp4" for name in clip_paths
        }

    def _stage_watermark(self) -> None:
        from .stages.watermark import run_watermark

        clip_paths = self._get_clip_paths("cut", "raw.mp4")
        watermarked = run_watermark(
            clip_paths, self.job.working_dir, self.config, branding=self.branding,
        )
        self.job.stages["watermark"].artifacts = {
            name: f"clips/{name}/watermarked.mp4" for name in watermarked
        }

    def _stage_intro_outro(self) -> None:
        from .stages.intro_outro import run_intro_outro

        clip_paths = self._get_clip_paths("watermark", "watermarked.mp4")
        cut_plans = self._load_cut_plans()
        result = run_intro_outro(
            clip_paths, cut_plans, self.job.working_dir, self.config,
            self.no_voice, branding=self.branding,
        )
        self.job.stages["intro_outro"].artifacts = {
            name: f"clips/{name}/with_intro_outro.mp4" for name in result
        }

    def _stage_hook_prepend(self) -> None:
        from .stages.hook_prepend import run_hook_prepend

        clip_paths = self._get_clip_paths("intro_outro", "with_intro_outro.mp4")
        result = run_hook_prepend(
            clip_paths, self.job.working_dir, self.config,
            cut_specs=self.cut_specs,
        )
        self.job.stages["hook_prepend"].artifacts = {
            name: f"clips/{name}/final.mp4" for name in result
        }

    # --- Helpers ---

    def _load_transcript(self) -> Transcript:
        path = Path(self.job.working_dir) / "transcript.json"
        return Transcript.model_validate_json(path.read_text())

    def _load_visual_context(self) -> VisualContext | None:
        path = Path(self.job.working_dir) / "visual_context.json"
        if path.exists():
            return VisualContext.model_validate_json(path.read_text())
        return None

    def _load_cut_plans(self) -> list[CutPlan]:
        """Load all cut plans from the cut_plans/ directory."""
        plans_dir = Path(self.job.working_dir) / "cut_plans"
        plans = []
        for spec in self.cut_specs:
            plan_path = plans_dir / f"{spec.name}.json"
            if plan_path.exists():
                plans.append(CutPlan.model_validate_json(plan_path.read_text()))
        return plans

    def _get_clip_paths(self, stage_name: str, filename: str) -> dict[str, str]:
        """Build clip paths from a stage's artifacts."""
        work = Path(self.job.working_dir)
        artifacts = self.job.stages[stage_name].artifacts
        return {
            name: str(work / f"clips/{name}/{filename}")
            for name in artifacts
        }
