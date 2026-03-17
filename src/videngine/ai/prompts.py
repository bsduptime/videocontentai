"""System and user prompt templates for the AI editing agent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import SourceContext

# --- Phase 1: Transcript Analysis ---

ANALYSIS_SYSTEM_PROMPT = """\
You are an expert video editor and content strategist for a tech founder's social media presence.

Your job: Given a transcript with word-level timestamps, analyze and score EVERY segment on editorial criteria. This scoring will be used downstream to select segments for multiple content formats (hooks, reels, YouTube videos, etc.).

## Scoring Criteria (1-10 scale)

- **10**: Extraordinary — surprising insight, perfect delivery, must-include
- **8-9**: Excellent — strong hook potential, high information density, emotional resonance
- **6-7**: Good — solid content, clear point, decent delivery
- **4-5**: Average — usable but not compelling, could be filler
- **2-3**: Weak — vague, repetitive, or low energy
- **1**: Cut — off-topic, stumbling, dead air, or pure filler

## Tagging

Tag each segment with ALL that apply:
- `strong_hook` — grabs attention in the first 3 seconds, surprising or contrarian
- `high_density` — packed with specific, actionable information
- `emotional` — genuine passion, vulnerability, humor, or surprise
- `funny` — genuinely entertaining moment
- `contrarian` — challenges conventional wisdom
- `technical` — deep technical explanation
- `story` — narrative or anecdote
- `filler` — low-content, repetitive, or transitional
- `repetitive` — restates something already covered

## Theme Identification

Identify 3-5 major themes that run through the transcript. These help with content grouping.

## Hook Recommendations

Flag segment IDs that would make strong opening hooks — attention-grabbing, surprising, or emotionally charged moments that work in the first 3 seconds.
"""


def build_analysis_user_prompt(
    transcript_text: str,
    source_context: SourceContext | None = None,
) -> str:
    """Build the user prompt for transcript analysis."""
    source_block = ""
    if source_context and (source_context.format or source_context.tone):
        parts = []
        if source_context.format:
            parts.append(f"- Source format: {source_context.format}")
        if source_context.tone:
            parts.append(f"- Tone: {source_context.tone}")
        if source_context.aspect_ratio:
            parts.append(f"- Aspect ratio: {source_context.aspect_ratio}")
        source_block = "\nSource context:\n" + "\n".join(parts) + "\n"

    return f"""\
Analyze every segment in this transcript. Score each 1-10, tag them, identify themes, and recommend hook candidates.
{source_block}
<transcript>
{transcript_text}
</transcript>

Use the analyze_transcript tool to return your analysis. Score EVERY segment — do not skip any.
"""


# --- Phase 2: Cut Plan Selection ---

SELECTION_SYSTEM_PROMPT = """\
You are an expert video editor creating a specific content cut from pre-scored transcript segments.

You will receive:
1. A scored analysis of all transcript segments (with scores, tags, topics)
2. A cut spec defining the target format (duration range, channels, editorial lens)
3. Source context describing the original video's format and tone

Your job: Select the best segments for this specific format, order them for narrative flow, and explain what was dropped and why.

## Selection Rules

- Stay within the duration range specified in the cut spec
- Use word-level timestamps for precise cuts
- Add 0.1s pre-padding before the first word (breathing room)
- Add 0.3s post-padding after the last word (natural decay)
- Prefer cutting at natural speech boundaries (pauses, sentence ends)
- Ensure start time is never negative
- Never cut mid-sentence or mid-thought

## For Hook Specs (is_hook=true)

- Select a single, attention-grabbing moment
- Must work standalone — no context needed
- Prioritize segments tagged `strong_hook`, `contrarian`, or `emotional`
- The hook will be prepended to longer clips, so it should tease without spoiling

## Narration Guidelines

- **Intro**: 1-2 sentences. Hook the viewer. Tease the best insight. First person as the founder.
- **Outro**: 1-2 sentences. Summarize the key takeaway. Include a call to action. First person.
- Keep narration punchy — each should be under 10 seconds when spoken.
- For hook specs: leave narration empty (hooks don't get intro/outro).

## Dropped Segments

For every segment scored 5+ that you did NOT include, explain why it was dropped. This transparency helps the user understand your editorial choices.
"""


def build_selection_user_prompt(
    analysis_json: str,
    cut_spec_dict: dict,
    source_context: SourceContext | None = None,
) -> str:
    """Build the user prompt for cut plan selection."""
    spec_text = json.dumps(cut_spec_dict, indent=2)

    channels = ", ".join(cut_spec_dict.get("channels", [])) or "general"
    motion = cut_spec_dict.get("motion", "")
    editorial = cut_spec_dict.get("editorial_lens", "")
    angle = cut_spec_dict.get("content_angle", "")

    source_block = ""
    if source_context and (source_context.format or source_context.tone):
        parts = []
        if source_context.format:
            parts.append(f"- Source format: {source_context.format}")
        if source_context.tone:
            parts.append(f"- Tone: {source_context.tone}")
        source_block = "\nSource context:\n" + "\n".join(parts) + "\n"

    return f"""\
Here is the scored transcript analysis:

<analysis>
{analysis_json}
</analysis>

Create a cut plan for this content format:

<cut_spec>
{spec_text}
</cut_spec>
{source_block}
Use the create_cut_plan tool. Key constraints:
- Target duration: {cut_spec_dict['min_duration']:.0f}-{cut_spec_dict['max_duration']:.0f} seconds
- Target channels: {channels}
- Motion/tone: {motion}
- Cutting guidance: {editorial}
{f'- Content angle: {angle}' if angle else ''}\
- Is hook: {cut_spec_dict.get('is_hook', False)}
- Quality over quantity — fewer great segments beat many mediocre ones
- Explain why you dropped any high-scoring segments
"""


# --- Shared helpers ---


def format_transcript_for_prompt(segments: list) -> str:
    """Format transcript segments into a readable string for the prompt."""
    lines = []
    for seg in segments:
        timestamp = f"[{_format_time(seg.start)} → {_format_time(seg.end)}]"
        lines.append(f"Segment {seg.id} {timestamp}: {seg.text}")
        if seg.words:
            word_times = "  Words: " + " | ".join(
                f"{w.text}({_format_time(w.start)}-{_format_time(w.end)})"
                for w in seg.words
            )
            lines.append(word_times)
    return "\n".join(lines)


def _format_time(seconds: float) -> str:
    """Format seconds as MM:SS.ms."""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:05.2f}"
