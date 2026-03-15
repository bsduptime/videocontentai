"""Stage orchestrator with checkpointing."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from .config import Config
from .models import (
    EditDecision,
    JobState,
    StageResult,
    StageStatus,
    Transcript,
)

console = Console()


class Pipeline:
    def __init__(
        self,
        source_file: str,
        config: Config,
        project: str = "",
        target_duration: float | None = None,
        ratios: list[str] | None = None,
        no_voice: bool = False,
        review: bool = False,
        dry_run: bool = False,
        job_id: str | None = None,
    ) -> None:
        self.source_file = str(Path(source_file).resolve())
        self.config = config
        self.project = project
        self.target_duration = target_duration or config.ai.target_total_duration
        self.ratios = ratios or ["16x9"]
        self.no_voice = no_voice
        self.review = review
        self.dry_run = dry_run

        # Create or load job
        if job_id:
            self.job = JobState.load(
                str(Path(config.paths.working_dir) / job_id)
            )
        else:
            self.job = self._create_job()

    def _create_job(self) -> JobState:
        job_id = f"{self.project or 'job'}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        working_dir = Path(self.config.paths.working_dir) / job_id
        working_dir.mkdir(parents=True, exist_ok=True)

        job = JobState(
            job_id=job_id,
            source_file=self.source_file,
            working_dir=str(working_dir),
            project=self.project,
            target_duration=self.target_duration,
            ratios=self.ratios,
            no_voice=self.no_voice,
        )
        job.save()
        return job

    def run(self) -> JobState:
        """Run all pipeline stages, skipping completed ones."""
        console.print(f"\n[bold]Job:[/bold] {self.job.job_id}")
        console.print(f"[bold]Source:[/bold] {self.job.source_file}")
        console.print(f"[bold]Working dir:[/bold] {self.job.working_dir}\n")

        try:
            self._run_stage("transcribe", self._stage_transcribe)
            self._run_stage("analyze", self._stage_analyze)

            if self.review:
                self._review_pause()

            if not self.no_voice:
                self._run_stage("voice", self._stage_voice)
            else:
                self._skip_stage("voice")

            self._run_stage("assemble", self._stage_assemble)
            self._run_stage("render", self._stage_render)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Resume with:[/yellow]")
            console.print(f"  videngine resume {self.job.job_id}")
            raise SystemExit(1)

        console.print("\n[bold green]Pipeline complete![/bold green]")
        outputs = self.job.stages.get("render", StageResult()).artifacts
        for ratio, path in outputs.items():
            console.print(f"  {ratio}: {path}")

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
        """Pause for user to review edit decision before proceeding."""
        decision_path = Path(self.job.working_dir) / "edit_decision.json"
        if decision_path.exists():
            console.print(f"\n[yellow]Review edit decision at:[/yellow]")
            console.print(f"  {decision_path}")
            console.print("[yellow]Press Enter to continue or Ctrl+C to abort...[/yellow]")
            input()

    # --- Stage implementations ---

    def _stage_transcribe(self) -> None:
        from .stages.transcribe import run_transcribe

        transcript = run_transcribe(
            self.job.source_file, self.job.working_dir, self.config
        )
        self.job.stages["transcribe"].artifacts = {
            "transcript": "transcript.json",
            "audio": "audio.wav",
        }

    def _stage_analyze(self) -> None:
        from .stages.analyze import run_analyze

        transcript = self._load_transcript()
        edit_decision = run_analyze(
            transcript, self.job.working_dir, self.config, self.target_duration
        )
        self.job.stages["analyze"].artifacts = {
            "edit_decision": "edit_decision.json",
        }

    def _stage_voice(self) -> None:
        from .stages.voice import run_voice

        edit_decision = self._load_edit_decision()
        intro_path, outro_path = run_voice(
            edit_decision, self.job.working_dir, self.config
        )
        self.job.stages["voice"].artifacts = {
            "narration_intro": "narration_intro.wav",
            "narration_outro": "narration_outro.wav",
        }

    def _stage_assemble(self) -> None:
        from .stages.assemble import run_assemble

        edit_decision = self._load_edit_decision()

        # Get voice artifacts if available
        voice_stage = self.job.stages.get("voice", StageResult())
        intro_wav = None
        outro_wav = None
        if voice_stage.status == StageStatus.COMPLETED:
            work = Path(self.job.working_dir)
            intro_wav = str(work / "narration_intro.wav")
            outro_wav = str(work / "narration_outro.wav")

        assembled = run_assemble(
            edit_decision,
            self.job.source_file,
            self.job.working_dir,
            self.config,
            intro_wav=intro_wav,
            outro_wav=outro_wav,
        )
        self.job.stages["assemble"].artifacts = {
            "assembled": "assembled_16x9.mp4",
        }

    def _stage_render(self) -> None:
        from .stages.render import run_render

        assembled_path = str(
            Path(self.job.working_dir) / "assembled_16x9.mp4"
        )
        outputs = run_render(
            assembled_path, self.job.working_dir, self.config, self.ratios
        )
        self.job.stages["render"].artifacts = {
            ratio: f"final_{ratio}.mp4" for ratio in outputs
        }

    # --- Helpers ---

    def _load_transcript(self) -> Transcript:
        path = Path(self.job.working_dir) / "transcript.json"
        return Transcript.model_validate_json(path.read_text())

    def _load_edit_decision(self) -> EditDecision:
        path = Path(self.job.working_dir) / "edit_decision.json"
        return EditDecision.model_validate_json(path.read_text())
