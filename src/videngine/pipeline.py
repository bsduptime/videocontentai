"""Stage orchestrator with checkpointing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .brand import apply_manifest_overrides, brand_to_branding, load_brand, load_manifest
from .config import Config
from .ffmpeg.probe import probe
from .models import (
    BrandConfig,
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
            f"No spec files found for {aspect} source. " f"Provide --specs explicitly."
        )

    if len(matches) > 1:
        console.print(f"\n[yellow]Multiple spec files match {aspect} source:[/yellow]")
        for f, spec in matches:
            console.print(f"  {f}  ({spec.pipeline})")
        console.print("[yellow]Using first match. Override with --specs.[/yellow]\n")

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
        manifest_dir: str | None = None,
        no_voice: bool = False,
        no_thumbnail: bool = False,
        review: bool = False,
        dry_run: bool = False,
        job_id: str | None = None,
    ) -> None:
        self.source_file = str(Path(source_file).resolve()) if source_file else ""
        self.config = config
        self.project = project
        self.no_voice = no_voice
        self.no_thumbnail = no_thumbnail
        self.review = review
        self.dry_run = dry_run

        # Create or load job
        if job_id:
            self.job = JobState.load(str(Path(config.paths.working_dir) / job_id))
            self.spec_file = self.job.spec_file
            self.no_voice = self.job.no_voice
        else:
            if specs_file:
                self.spec_file = load_spec_file(specs_file)
            else:
                self.spec_file = detect_spec_file(self.source_file)
            self.job = self._create_job()

        # Load brand: manifest → brand loader → legacy cut spec fallback
        self._manifest = load_manifest(manifest_dir) if manifest_dir else None
        self._brand_config = self._load_brand_config()

    @property
    def cut_specs(self) -> list[CutSpec]:
        return self.spec_file.cuts

    @property
    def source_context(self) -> SourceContext:
        ctx = self.spec_file.source
        # Apply audio profile from manifest if present
        if self._manifest and self._manifest.audio_profile:
            ctx = ctx.model_copy(update={"audio_profile": self._manifest.audio_profile})
        return ctx

    @property
    def branding(self) -> Branding:
        """Branding for stages — converted from BrandConfig."""
        return brand_to_branding(self._brand_config)

    @property
    def brand(self) -> BrandConfig:
        return self._brand_config

    def _load_brand_config(self) -> BrandConfig:
        """Load brand config from manifest or cut spec source.brand.

        Brand is required — pipeline fails if no brand can be loaded.
        """
        brand_name = ""
        source = ""

        # Manifest takes priority
        if self._manifest and self._manifest.brand:
            brand_name = self._manifest.brand
            source = "manifest"
        else:
            brand_name = self.spec_file.source.brand
            source = "cut spec"

        if not brand_name:
            raise ValueError(
                "No brand specified. Set 'brand' in manifest.json or source.brand in the cut spec."
            )

        brand = load_brand(brand_name)
        if not brand:
            raise FileNotFoundError(
                f"Brand '{brand_name}' not found. " f"Create assets/brands/{brand_name}/brand.json"
            )

        if self._manifest:
            brand = apply_manifest_overrides(brand, self._manifest)

        console.print(f"  [dim]Brand: {brand.display_name or brand.name} (from {source})[/dim]")
        return brand

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
        console.print(
            f"[bold]Cuts:[/bold] {', '.join(f'{s.name} ({s.min_duration:.0f}-{s.max_duration:.0f}s)' for s in self.cut_specs)}\n"
        )

        try:
            self._run_stage("transcribe", self._stage_transcribe)
            self._run_stage("analyze", self._stage_analyze)

            if self.review:
                self._review_pause()

            self._run_stage("cut", self._stage_cut)
            self._run_stage("watermark", self._stage_watermark)

            if self.config.background.enabled:
                self._run_stage("background", self._stage_background)
            else:
                self._skip_stage("background")

            self._run_stage("intro_outro", self._stage_intro_outro)
            self._run_stage("hook_prepend", self._stage_hook_prepend)

            if self.no_thumbnail or not self.config.thumbnail.enabled:
                self._skip_stage("thumbnail")
            else:
                self._run_stage("thumbnail", self._stage_thumbnail)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Resume with:[/yellow]")
            console.print(f"  videngine resume {self.job.job_id}")
            raise SystemExit(1)

        console.print("\n[bold green]Pipeline complete![/bold green]")
        outputs = self.job.stages.get("hook_prepend", StageResult()).artifacts
        for spec_name, path in outputs.items():
            console.print(f"  {spec_name}: {path}")

        thumb_outputs = self.job.stages.get("thumbnail", StageResult()).artifacts
        if thumb_outputs:
            console.print("\n  [bold]Thumbnails:[/bold]")
            for spec_name, path in thumb_outputs.items():
                console.print(f"    {spec_name}: {path}")

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
                console.print("    [dim](dry run — skipping execution)[/dim]")
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
            console.print("\n[yellow]Review cut plans at:[/yellow]")
            console.print(f"  {plans_dir}")
            for f in sorted(plans_dir.glob("*.json")):
                console.print(f"    {f.name}")
            console.print("[yellow]Press Enter to continue or Ctrl+C to abort...[/yellow]")
            input()

    # --- Stage implementations ---

    def _stage_transcribe(self) -> None:
        from .stages.transcribe import run_transcribe, run_visual_analysis

        run_transcribe(
            self.job.source_file,
            self.job.working_dir,
            self.config,
            audio_profile=self.source_context.audio_profile,
        )

        # Adaptive frame interval based on source format
        frame_interval, dedup_window = self._get_frame_sampling_params()

        run_visual_analysis(
            self.job.source_file,
            self.job.working_dir,
            dedup_window=dedup_window,
            frame_interval=frame_interval,
        )
        artifacts = {
            "transcript": "transcript.json",
            "audio": "audio.wav",
            "visual_context": "visual_context.json",
        }
        # Track clean source if denoise produced one
        clean_source = Path(self.job.working_dir) / "source_clean.mp4"
        if clean_source.exists():
            artifacts["source_clean"] = "source_clean.mp4"
        self.job.stages["transcribe"].artifacts = artifacts

    def _stage_analyze(self) -> None:
        from .stages.analyze import run_analyze

        transcript = self._load_transcript()
        visual_context = self._load_visual_context()
        cut_plans = run_analyze(
            transcript,
            self.job.working_dir,
            self.config,
            self.cut_specs,
            self.source_context,
            visual_context=visual_context,
        )
        artifacts = {"_analysis": "cut_plans/_analysis.json"}
        for plan in cut_plans:
            artifacts[plan.spec_name] = f"cut_plans/{plan.spec_name}.json"
        self.job.stages["analyze"].artifacts = artifacts

    def _stage_cut(self) -> None:
        from .stages.cut import run_cut

        cut_plans = self._load_cut_plans()
        # Use clean source (denoised audio) if stage 1 produced one
        source = self._get_clean_source()
        clip_paths = run_cut(
            cut_plans,
            source,
            self.job.working_dir,
            self.config,
            cut_specs=self.cut_specs,
        )
        self.job.stages["cut"].artifacts = {name: f"clips/{name}/raw.mp4" for name in clip_paths}

    def _stage_watermark(self) -> None:
        from .stages.watermark import run_watermark

        clip_paths = self._get_clip_paths("cut", "raw.mp4")
        cut_plans = self._load_cut_plans()
        watermarked = run_watermark(
            clip_paths,
            self.job.working_dir,
            self.config,
            branding=self.branding,
            cut_plans=cut_plans,
        )
        self.job.stages["watermark"].artifacts = {
            name: f"clips/{name}/watermarked.mp4" for name in watermarked
        }

    def _stage_background(self) -> None:
        from .stages.background import run_background

        clip_paths = self._get_clip_paths("watermark", "watermarked.mp4")
        result = run_background(
            clip_paths,
            self.job.working_dir,
            self.config,
        )
        self.job.stages["background"].artifacts = {
            name: f"clips/{name}/bg_replaced.mp4" for name in result
        }

    def _stage_intro_outro(self) -> None:
        from .stages.intro_outro import run_intro_outro

        # Read from background stage if it ran, otherwise from watermark
        bg_stage = self.job.stages.get("background", StageResult())
        if bg_stage.status == StageStatus.COMPLETED and bg_stage.artifacts:
            clip_paths = self._get_clip_paths("background", "bg_replaced.mp4")
        else:
            clip_paths = self._get_clip_paths("watermark", "watermarked.mp4")
        cut_plans = self._load_cut_plans()
        result = run_intro_outro(
            clip_paths,
            cut_plans,
            self.job.working_dir,
            self.config,
            self.no_voice,
            branding=self.branding,
        )
        self.job.stages["intro_outro"].artifacts = {
            name: f"clips/{name}/with_intro_outro.mp4" for name in result
        }

    def _stage_hook_prepend(self) -> None:
        from .stages.hook_prepend import run_hook_prepend

        clip_paths = self._get_clip_paths("intro_outro", "with_intro_outro.mp4")
        result = run_hook_prepend(
            clip_paths,
            self.job.working_dir,
            self.config,
            cut_specs=self.cut_specs,
        )
        self.job.stages["hook_prepend"].artifacts = {
            name: f"clips/{name}/final.mp4" for name in result
        }

    def _stage_thumbnail(self) -> None:
        from .stages.thumbnail import run_thumbnail

        cut_plans = self._load_cut_plans()
        result = run_thumbnail(
            cut_plans,
            self.job.source_file,
            self.job.working_dir,
            self.config,
            branding=self.branding,
            source_context=self.source_context,
        )
        self.job.stages["thumbnail"].artifacts = {
            name: f"clips/{name}/thumbnails/thumbnail_youtube.png" for name in result
        }

    # --- Helpers ---

    def _get_frame_sampling_params(self) -> tuple[float, float]:
        """Determine frame interval and dedup window from source.format.

        Returns (frame_interval, dedup_window) in seconds.
        """
        source_format = self.source_context.format.lower()
        if "screen" in source_format:
            return 10.0, 1.5
        elif "talking" in source_format:
            return 30.0, 2.0
        else:
            return 15.0, 2.0

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

    def _get_clean_source(self) -> str:
        """Return path to denoised source video, falling back to original."""
        clean = Path(self.job.working_dir) / "source_clean.mp4"
        if clean.exists():
            return str(clean)
        return self.job.source_file

    def _get_clip_paths(self, stage_name: str, filename: str) -> dict[str, str]:
        """Build clip paths from a stage's artifacts."""
        work = Path(self.job.working_dir)
        artifacts = self.job.stages[stage_name].artifacts
        return {name: str(work / f"clips/{name}/{filename}") for name in artifacts}
