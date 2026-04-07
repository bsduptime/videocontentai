"""Structured output JSON schema for thumbnail concept generation."""

from __future__ import annotations

GENERATE_THUMBNAIL_CONCEPT_TOOL = {
    "name": "generate_thumbnail_concept",
    "description": (
        "Generate a thumbnail concept for a video cut. Produce an outcome-focused "
        "hook text (2-5 words, NOT the video title), select an archetype, choose colors, "
        "and write an image generation prompt."
    ),
    "input_schema": {
        "type": "object",
        "required": [
            "hook_text",
            "archetype",
            "face_expression",
            "accent_color",
            "visual_elements",
            "flux_prompt",
            "text_position",
        ],
        "properties": {
            "hook_text": {
                "type": "string",
                "description": (
                    "2-5 word outcome-focused text for the thumbnail. "
                    "Sell the result, not the topic. Examples: '10x FASTER', "
                    "'STOP doing this', '47x Speedup', 'Hidden Setting'. "
                    "Must NOT repeat the video title."
                ),
            },
            "archetype": {
                "type": "string",
                "enum": ["performance", "tutorial", "comparison"],
                "description": (
                    "Thumbnail layout archetype. "
                    "performance: before/after metric + face + benchmark number. "
                    "tutorial: technology logo/diagram + face + descriptive hook. "
                    "comparison: VS split layout or tech logos side by side + face."
                ),
            },
            "face_expression": {
                "type": "string",
                "description": (
                    "Expression for the face in the thumbnail. "
                    "Use intense, genuine emotions: 'determined', 'curious', "
                    "'impressed', 'focused', 'surprised'. Avoid neutral or generic."
                ),
            },
            "accent_color": {
                "type": "string",
                "description": (
                    "Hex color for the accent/highlight elements. "
                    "Should contrast with the brand's primary color. "
                    "Warm colors (orange, yellow, red) create urgency and stand out."
                ),
            },
            "visual_elements": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "2-4 visual elements to include in the scene background. "
                    "Examples: 'PostgreSQL elephant logo', 'speed gauge', "
                    "'server rack', 'terminal with green text', 'rising graph'."
                ),
            },
            "flux_prompt": {
                "type": "string",
                "description": (
                    "Detailed image generation prompt for Flux Kontext. "
                    "Describe the scene, lighting, style, and composition. "
                    "Do NOT describe text overlays — those are added programmatically. "
                    "Focus on background scene, mood, and visual elements."
                ),
            },
            "text_position": {
                "type": "string",
                "enum": ["upper_left", "upper_right"],
                "description": (
                    "Where to place the hook text. Position text on the opposite "
                    "side from the face. If face is right, text goes upper_left."
                ),
            },
        },
    },
}
