"""System and user prompt templates for thumbnail concept generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import CutPlan, SourceContext

THUMBNAIL_SYSTEM_PROMPT = """\
You are an expert YouTube thumbnail designer specializing in tech and educational content.

Your job: Given a video cut's title, description, and target channels, generate a thumbnail \
concept that maximizes click-through rate.

## Research-Backed Rules

1. **Hook text**: 2-5 words, outcome-focused. Sell the RESULT, not the topic.
   - GOOD: "10x FASTER", "47x Speedup", "STOP this", "Hidden Setting", "vs MySQL"
   - BAD: "PostgreSQL Tutorial", "Database Indexing Guide", "How To Optimize"
   - NEVER repeat the video title — the thumbnail complements it

2. **Archetype selection**:
   - **performance**: Before/after metrics, speed comparisons, benchmark results
   - **tutorial**: Technology logo or diagram + descriptive hook
   - **comparison**: VS layout, side-by-side technologies, trade-offs

3. **Face expression**: Intense, genuine emotions. Closed mouth outperforms open mouth. \
Determined/focused/curious beats shocked/surprised. The face is an emotional anchor.

4. **Colors**: High contrast is the #1 design variable (~30% CTR lift). Use warm accent \
colors (orange, yellow) against cool primary colors (blue, teal). The thumbnail must \
pop against YouTube's white/dark interface.

5. **Composition**: Face on one side (typically right), text on the opposite side (upper area). \
Never place important elements in the bottom-right (timestamp zone) or bottom edge (progress bar).

6. **Flux prompt**: Describe a clean, high-contrast background scene. Include relevant \
tech visual elements. Do NOT describe text — that is rendered programmatically. \
Style should be professional, modern, with good lighting.

## For tech/database content specifically

- Blue conveys trustworthiness and expertise
- Show outcomes: speed gauges, benchmark numbers, architecture diagrams
- Terminal/code imagery works when it's a prop, not the main focus
- Clean, professional aesthetic > cluttered technical screenshots
"""


def build_thumbnail_user_prompt(
    cut_plan: CutPlan,
    source_context: SourceContext | None = None,
) -> str:
    """Build the user prompt for thumbnail concept generation."""
    channels = ", ".join(cut_plan.hashtags[:3]) if cut_plan.hashtags else "general"

    source_block = ""
    if source_context:
        parts = []
        if source_context.brand:
            parts.append(f"- Brand: {source_context.brand}")
        if source_context.tone:
            parts.append(f"- Tone: {source_context.tone}")
        if parts:
            source_block = "\nBrand context:\n" + "\n".join(parts) + "\n"

    return f"""\
Generate a thumbnail concept for this video cut:

- **Title**: {cut_plan.title}
- **Description**: {cut_plan.description}
- **Cut type**: {cut_plan.spec_name}
- **Duration**: {cut_plan.total_estimated_duration:.0f}s
- **Channels**: {channels}
{source_block}
Use the generate_thumbnail_concept tool. Remember:
- Hook text must NOT repeat the title — complement it
- 2-5 words max, outcome-focused
- Pick the archetype that best matches the content
- Flux prompt should describe the background scene only (no text overlays)
"""
