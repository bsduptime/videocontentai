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


# --- Cut Spec File (pipeline input) ---


class SourceContext(BaseModel):
    """Describes the source video format and tone — passed to the AI for context."""
    format: str = ""  # "screen recording with narration", "talking-head, iPhone vertical"
    aspect_ratio: str = ""  # "16:9", "9:16"
    duration_range: list[float] = Field(default_factory=list)  # [min, max] expected source length
    tone: str = ""  # editorial tone guidance for the AI


class CutSpec(BaseModel):
    name: str  # "hook", "tip", "highlight", "deep_dive"
    min_duration: float  # seconds
    max_duration: float  # seconds
    channels: list[str] = Field(default_factory=list)  # target platforms
    motion: str = ""  # "Teaching", "Stories / Proof", etc.
    content_angle: str = ""  # optional per-run override: "focus on the AI demo"
    editorial_lens: str = ""  # cutting guidance for the AI
    is_hook: bool = False  # True for the 7-15s hook spec
    prepend_hook: bool = False  # True = prepend the hook clip to this cut
    mood: str = ""  # references a mood name from moods.json


class Mood(BaseModel):
    """A music mood from moods.json — maps to an audio file at assets/music/{name}.mp3."""
    name: str
    duration: int  # seconds — length of the source track
    used_by: list[str] = Field(default_factory=list)
    description: str = ""
    generation_prompt: str = ""  # for future AI music generation


class MoodsConfig(BaseModel):
    """Top-level structure of moods.json."""
    moods: list[Mood] = Field(default_factory=list)


class Branding(BaseModel):
    """Per-pipeline branding assets — intro/outro templates and watermark."""
    intro_16x9: str = ""
    intro_9x16: str = ""
    outro_16x9: str = ""
    outro_9x16: str = ""
    watermark: str = ""


class CutSpecFile(BaseModel):
    """Top-level structure of a cut spec JSON file."""
    pipeline: str = ""  # "dbexpertai-brand-portrait", "founder-personal-landscape"
    branding: Branding = Field(default_factory=Branding)
    source: SourceContext = Field(default_factory=SourceContext)
    cuts: list[CutSpec] = Field(default_factory=list)


# --- Analysis (Stage 2 output, phase 1) ---


class ScoredSegment(BaseModel):
    segment_id: int
    start: float
    end: float
    text: str
    score: int  # 1-10
    tags: list[str]  # "strong_hook", "high_density", "emotional"
    topic: str
    summary: str


class TranscriptAnalysis(BaseModel):
    scored_segments: list[ScoredSegment]
    overall_themes: list[str]
    recommended_hook_ids: list[int]


# --- Cut Plans (Stage 2 output, phase 2) ---


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


class DroppedSegment(BaseModel):
    segment_ids: list[int]
    start: float
    end: float
    text: str
    drop_reason: str


class CutPlan(BaseModel):
    spec_name: str
    segments: list[SelectedSegment]
    dropped_segments: list[DroppedSegment]
    full_text: str
    edit_rationale: str
    intro_narration: str
    outro_narration: str
    title: str
    description: str
    hashtags: list[str]
    total_estimated_duration: float


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


STAGE_NAMES = ["transcribe", "analyze", "cut", "watermark", "intro_outro", "hook_prepend"]


class JobState(BaseModel):
    job_id: str
    source_file: str
    working_dir: str
    project: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spec_file: CutSpecFile = Field(default_factory=CutSpecFile)
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
