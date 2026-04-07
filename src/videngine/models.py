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


# --- Loudness Measurement (Stage 3 — cut) ---


class LoudnessMeasurement(BaseModel):
    input_i: float  # measured integrated loudness (LUFS)
    input_tp: float  # measured true peak (dBTP)
    input_lra: float  # measured loudness range (LU)
    input_thresh: float
    target_offset: float


# --- Visual Context (Stage 1 — transcribe) ---


class SceneChange(BaseModel):
    timestamp: float  # seconds
    score: float  # 0.0-1.0 magnitude


class VisualSegment(BaseModel):
    start: float
    end: float
    duration: float
    motion_level: str = ""  # "low", "medium", "high"


class FrameDescription(BaseModel):
    timestamp: float  # seconds into the video
    screen: str = ""  # what page/view is shown
    visible_elements: str = ""  # UI elements, text, data visible
    region_of_interest: str = ""  # where the action/focus is
    visual_density: str = ""  # "low", "medium", "high", "very high"
    overlay_opportunity: bool = False  # enough empty space for text overlay?
    zoom_candidate: str | None = None  # description of element to zoom, or null


class VisualContext(BaseModel):
    source_file: str
    duration_seconds: float
    frame_interval: float = 30.0  # seconds between sampled frames
    scene_changes: list[SceneChange]
    visual_segments: list[VisualSegment]
    frame_descriptions: list[FrameDescription] = Field(default_factory=list)
    total_scene_changes: int
    avg_scene_duration: float


# --- Cut Spec File (pipeline input) ---


class SourceContext(BaseModel):
    """Describes the source video format and tone — passed to the AI for context."""

    brand: str = ""  # "dbexpertai", "founder" — drives voice and terminology
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
    mood_options: list[str] = Field(
        default_factory=list
    )  # mood names from moods.json — agent picks one
    audio_profile: str = "macbook"  # audio preprocessing profile ("macbook", "iphone")


class Mood(BaseModel):
    """A music mood from moods.json — maps to audio files at assets/music/{file}."""

    name: str
    valence: str = ""  # "positive" or "negative"
    arousal: str = ""  # "high" or "low"
    bpm: int = 120
    files: list[str] = Field(
        default_factory=list
    )  # e.g. ["drive-1.wav", "drive-2.wav", "drive-3.wav"]
    used_by: list[str] = Field(default_factory=list)
    description: str = ""
    generation_prompt: str = ""


class MoodsConfig(BaseModel):
    """Top-level structure of moods.json."""

    moods: list[Mood] = Field(default_factory=list)


class WatermarkPosition(BaseModel):
    """Watermark overlay position and appearance for a specific aspect ratio."""

    scale: float = 0.40
    opacity: float = 0.9
    x: str = "W-w-65"  # ffmpeg overlay x expression
    y: str = "H-h-40"  # ffmpeg overlay y expression


class ThumbnailTemplate(BaseModel):
    """Per-brand thumbnail rendering config — colors, fonts, layout."""

    primary_color: str = "#336791"  # PostgreSQL blue
    accent_color: str = "#F5A623"  # warm orange
    font_impact: str = "assets/fonts/Montserrat-Bold.ttf"
    font_readable: str = "assets/fonts/BebasNeue-Regular.ttf"
    logo_scale: float = 0.08


class Branding(BaseModel):
    """Per-pipeline branding assets — intro/outro templates and watermark."""

    intro_16x9: str = ""
    intro_9x16: str = ""
    outro_16x9: str = ""
    outro_9x16: str = ""
    watermark: str = ""
    watermark_16x9: WatermarkPosition = Field(default_factory=WatermarkPosition)
    watermark_9x16: WatermarkPosition = Field(default_factory=WatermarkPosition)
    thumbnail: ThumbnailTemplate = Field(default_factory=ThumbnailTemplate)


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


class VisualEffect(BaseModel):
    """A zoom or text overlay effect to apply during the watermark re-encode pass."""

    effect_type: str  # "zoom" or "text_overlay"
    start: float  # seconds — effect start time (relative to the cut clip)
    end: float  # seconds — effect end time
    zoom_target_x: str = "iw/2"  # ffmpeg expression for zoom center x
    zoom_target_y: str = "ih/2"  # ffmpeg expression for zoom center y
    zoom_factor: float = 1.3  # crop zoom factor (1.3 = gentle)
    overlay_text: str = ""  # text to display (for text_overlay type)


class CutPlan(BaseModel):
    spec_name: str
    mood: str = ""  # mood chosen by the agent from the spec's mood_options
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
    visual_effects: list[VisualEffect] = Field(default_factory=list)


# --- Thumbnails (Stage 7) ---


class ThumbnailConcept(BaseModel):
    """AI-generated thumbnail concept — what to render."""

    hook_text: str  # 2-5 word outcome text (NOT the video title)
    archetype: str = "tutorial"  # "performance", "tutorial", "comparison"
    face_expression: str = "determined"  # expression guidance
    accent_color: str = "#F5A623"  # hex accent color
    visual_elements: list[str] = Field(default_factory=list)  # scene elements
    flux_prompt: str = ""  # image generation prompt for Flux Kontext
    text_position: str = "upper_left"  # face right, looking left toward text


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


STAGE_NAMES = [
    "transcribe",
    "analyze",
    "cut",
    "watermark",
    "intro_outro",
    "hook_prepend",
    "thumbnail",
]


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
