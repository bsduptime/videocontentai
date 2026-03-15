"""Stage 2: AI editing agent — segment selection via Claude."""

from __future__ import annotations

import json
from pathlib import Path

from ..ai.client import AIClient
from ..ai.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    format_transcript_for_prompt,
)
from ..config import Config
from ..models import EditDecision, Transcript


def run_analyze(
    transcript: Transcript,
    working_dir: str,
    config: Config,
    target_duration: float | None = None,
) -> EditDecision:
    """Run the AI editing agent to select segments and create edit decisions."""
    work = Path(working_dir)
    target = target_duration or config.ai.target_total_duration

    # Format transcript for the prompt
    transcript_text = format_transcript_for_prompt(transcript.segments)

    # Handle long transcripts by chunking
    # Rough token estimate: ~0.75 tokens per character
    estimated_tokens = len(transcript_text) * 0.75
    if estimated_tokens > 50_000:
        edit_decision = _analyze_chunked(
            transcript, transcript_text, target, config
        )
    else:
        edit_decision = _analyze_single(transcript_text, target, config)

    # Save edit decision
    decision_path = work / "edit_decision.json"
    decision_path.write_text(edit_decision.model_dump_json(indent=2))

    return edit_decision


def _analyze_single(
    transcript_text: str,
    target_duration: float,
    config: Config,
) -> EditDecision:
    """Single-pass analysis for normal-length transcripts."""
    client = AIClient(config.ai)
    user_prompt = build_user_prompt(transcript_text, target_duration)

    raw = client.create_edit_decision(SYSTEM_PROMPT, user_prompt)
    return EditDecision.model_validate(raw)


def _analyze_chunked(
    transcript: Transcript,
    transcript_text: str,
    target_duration: float,
    config: Config,
) -> EditDecision:
    """Chunked analysis for long transcripts (>50K estimated tokens).

    Strategy: Split into 15-min windows, select best per chunk,
    then do a curator pass to pick the final set.
    """
    client = AIClient(config.ai)

    # Split segments into ~15 minute chunks
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

    # Per-chunk duration budget (proportional)
    total_source_duration = transcript.duration_seconds
    chunk_budget = target_duration / len(chunks) * 1.5  # Over-select, curator trims

    # Analyze each chunk
    all_candidates = []
    for i, chunk_segments in enumerate(chunks):
        chunk_text = format_transcript_for_prompt(chunk_segments)
        user_prompt = build_user_prompt(chunk_text, chunk_budget)
        raw = client.create_edit_decision(SYSTEM_PROMPT, user_prompt)
        decision = EditDecision.model_validate(raw)
        all_candidates.extend(decision.segments)

    # Curator pass: select final set from all candidates
    candidates_text = "\n".join(
        f"- [{s.start:.1f}s-{s.end:.1f}s] Topic: {s.topic} | {s.text[:100]}... | Rationale: {s.rationale}"
        for s in all_candidates
    )

    curator_prompt = f"""\
You previously analyzed a long video in chunks and selected these candidate segments:

{candidates_text}

Now select the BEST segments to create a final video of ~{target_duration:.0f} seconds.
Reorder them for the best narrative flow. Write new intro/outro narration for the final selection.
Use the create_edit_decision tool.
"""
    raw = client.create_edit_decision(SYSTEM_PROMPT, curator_prompt)
    return EditDecision.model_validate(raw)
