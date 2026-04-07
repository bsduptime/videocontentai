"""Stage 2: AI editing agent — two-phase analysis and cut plan creation."""

from __future__ import annotations

from pathlib import Path

from ..ai.client import AIClient
from ..ai.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    SELECTION_SYSTEM_PROMPT,
    build_analysis_user_prompt,
    build_selection_user_prompt,
    format_transcript_for_prompt,
    format_visual_context,
)
from ..config import Config
from ..models import (
    CutPlan,
    CutSpec,
    ScoredSegment,
    SourceContext,
    Transcript,
    TranscriptAnalysis,
    VisualContext,
)


def run_analyze(
    transcript: Transcript,
    working_dir: str,
    config: Config,
    cut_specs: list[CutSpec],
    source_context: SourceContext | None = None,
    visual_context: VisualContext | None = None,
) -> list[CutPlan]:
    """Run two-phase AI analysis: score all segments, then create per-spec cut plans."""
    work = Path(working_dir)
    plans_dir = work / "cut_plans"
    plans_dir.mkdir(exist_ok=True)

    client = AIClient(config.ai)
    visual_text = format_visual_context(visual_context) if visual_context else None

    # Phase 1: Analyze and score all segments
    transcript_text = format_transcript_for_prompt(transcript.segments)

    estimated_tokens = len(transcript_text) * 0.75
    if estimated_tokens > 50_000:
        analysis = _analyze_chunked(transcript, client, source_context, visual_text)
    else:
        analysis = _analyze_single(transcript_text, client, source_context, visual_text)

    # Save analysis
    analysis_path = plans_dir / "_analysis.json"
    analysis_path.write_text(analysis.model_dump_json(indent=2))

    # Phase 2: Create cut plan for each spec
    analysis_json = analysis.model_dump_json(indent=2)
    cut_plans = []
    for spec in cut_specs:
        plan = _create_cut_plan(analysis_json, spec, client, source_context, visual_text)
        plan_path = plans_dir / f"{spec.name}.json"
        plan_path.write_text(plan.model_dump_json(indent=2))
        cut_plans.append(plan)

    return cut_plans


def _analyze_single(
    transcript_text: str,
    client: AIClient,
    source_context: SourceContext | None = None,
    visual_text: str | None = None,
) -> TranscriptAnalysis:
    """Single-pass analysis for normal-length transcripts."""
    user_prompt = build_analysis_user_prompt(transcript_text, source_context, visual_text)
    raw = client.analyze_transcript(ANALYSIS_SYSTEM_PROMPT, user_prompt)
    return TranscriptAnalysis.model_validate(raw)


def _analyze_chunked(
    transcript: Transcript,
    client: AIClient,
    source_context: SourceContext | None = None,
    visual_text: str | None = None,
) -> TranscriptAnalysis:
    """Chunked analysis for long transcripts (>50K estimated tokens).

    Strategy: Split into 15-min windows, analyze each, merge scored segments.
    """
    chunk_duration = 900  # 15 minutes in seconds
    chunks: list[list] = []
    current_chunk: list = []
    chunk_start = 0.0

    for seg in transcript.segments:
        current_chunk.append(seg)
        if seg.end - chunk_start >= chunk_duration:
            chunks.append(current_chunk)
            current_chunk = []
            chunk_start = seg.end

    if current_chunk:
        chunks.append(current_chunk)

    # Analyze each chunk
    all_scored: list[ScoredSegment] = []
    all_themes: list[str] = []
    all_hook_ids: list[int] = []

    for chunk_segments in chunks:
        chunk_text = format_transcript_for_prompt(chunk_segments)
        user_prompt = build_analysis_user_prompt(chunk_text, source_context, visual_text)
        raw = client.analyze_transcript(ANALYSIS_SYSTEM_PROMPT, user_prompt)
        chunk_analysis = TranscriptAnalysis.model_validate(raw)
        all_scored.extend(chunk_analysis.scored_segments)
        all_themes.extend(chunk_analysis.overall_themes)
        all_hook_ids.extend(chunk_analysis.recommended_hook_ids)

    # Deduplicate themes
    unique_themes = list(dict.fromkeys(all_themes))[:5]

    return TranscriptAnalysis(
        scored_segments=all_scored,
        overall_themes=unique_themes,
        recommended_hook_ids=all_hook_ids,
    )


def _create_cut_plan(
    analysis_json: str,
    spec: CutSpec,
    client: AIClient,
    source_context: SourceContext | None = None,
    visual_text: str | None = None,
) -> CutPlan:
    """Create a cut plan for a specific content format."""
    user_prompt = build_selection_user_prompt(
        analysis_json, spec.model_dump(), source_context, visual_text
    )
    raw = client.create_cut_plan(SELECTION_SYSTEM_PROMPT, user_prompt)
    return CutPlan.model_validate(raw)
