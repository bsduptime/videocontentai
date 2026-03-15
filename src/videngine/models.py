"""Pydantic data models for the video production pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# --- Transcript (Stage 1 → Stage 2) ---


class Word(BaseModel):
    text: str
    start: float  # seconds
    end: float
    confidence: float = 1.0


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[Word]


class Transcript(BaseModel):
    source_file: str
    duration_seconds: float
    language: str
    segments: list[TranscriptSegment]


# --- EditDecision (Stage 2 → Stages 3+4) ---


class FocusHint(str, Enum):
    CENTER = "center"
    LEFT_THIRD = "left_third"
    RIGHT_THIRD = "right_third"


class SelectedSegment(BaseModel):
    segment_ids: list[int]
    start: float
    end: float
    text: str
    rationale: str
    topic: str
    focus_hint: FocusHint = FocusHint.CENTER


class EditDecision(BaseModel):
    title: str
    description: str
    segments: list[SelectedSegment]
    intro_narration: str
    outro_narration: str
    total_estimated_duration: float
    edit_rationale: str
    hashtags: list[str]


# --- JobState (Resumability) ---


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageResult(BaseModel):
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)  # name → relative path


STAGE_NAMES = ["transcribe", "analyze", "voice", "assemble", "render"]


class JobState(BaseModel):
    job_id: str
    source_file: str
    working_dir: str
    project: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_duration: float = 300.0
    ratios: list[str] = Field(default_factory=lambda: ["16x9"])
    no_voice: bool = False
    stages: dict[str, StageResult] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        for name in STAGE_NAMES:
            if name not in self.stages:
                self.stages[name] = StageResult()

    def save(self) -> None:
        path = Path(self.working_dir) / "job_state.json"
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, working_dir: str | Path) -> JobState:
        path = Path(working_dir) / "job_state.json"
        return cls.model_validate_json(path.read_text())
