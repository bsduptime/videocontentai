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

5. **Composition**: Tech visual or diagram center-left (~60%), face on the RIGHT side \
looking LEFT toward the text and visuals (~30%), hook text upper-left. The face's gaze \
directs the viewer's eyes toward the key visual elements and text. \
Never place important elements in the bottom-right (timestamp zone) or bottom edge (progress bar).

6. **Flux prompt**: Describe the scene with a man on the RIGHT side of frame. Include \
the person's positioning (right side, looking slightly left toward visuals), expression \
(determined, focused, intense), and the tech visual elements on the left/center. \
Do NOT describe text overlays — those are rendered programmatically. \
Style should be professional, modern, cinematic lighting, high contrast, dark background.

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
