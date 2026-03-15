"""Structured output JSON schemas for Claude tool use."""

from __future__ import annotations

EDIT_DECISION_TOOL = {
    "name": "create_edit_decision",
    "description": (
        "Create an edit decision for the video. Select the best segments, "
        "order them for a compelling narrative, and write intro/outro narration scripts."
    ),
    "input_schema": {
        "type": "object",
        "required": [
            "title",
            "description",
            "segments",
            "intro_narration",
            "outro_narration",
            "total_estimated_duration",
            "edit_rationale",
            "hashtags",
        ],
        "properties": {
            "title": {
                "type": "string",
                "description": "Compelling title for the final video",
            },
            "description": {
                "type": "string",
                "description": "Short description for social media (1-2 sentences)",
            },
            "segments": {
                "type": "array",
                "description": "Selected segments in playback order",
                "items": {
                    "type": "object",
                    "required": [
                        "segment_ids",
                        "start",
                        "end",
                        "text",
                        "rationale",
                        "topic",
                    ],
                    "properties": {
                        "segment_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "IDs of transcript segments covered",
                        },
                        "start": {
                            "type": "number",
                            "description": "Cut start time in seconds (with 0.1s pre-padding)",
                        },
                        "end": {
                            "type": "number",
                            "description": "Cut end time in seconds (with 0.3s post-padding)",
                        },
                        "text": {
                            "type": "string",
                            "description": "The spoken text in this segment",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Why this segment was selected",
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topic label for this segment",
                        },
                        "focus_hint": {
                            "type": "string",
                            "enum": ["center", "left_third", "right_third"],
                            "description": "Where the speaker/subject is positioned for portrait cropping",
                        },
                    },
                },
            },
            "intro_narration": {
                "type": "string",
                "description": "Script for the voice-cloned intro narration (1-2 sentences, hook the viewer)",
            },
            "outro_narration": {
                "type": "string",
                "description": "Script for the voice-cloned outro narration (1-2 sentences, CTA)",
            },
            "total_estimated_duration": {
                "type": "number",
                "description": "Estimated total duration of selected segments in seconds",
            },
            "edit_rationale": {
                "type": "string",
                "description": "Overall editorial reasoning for the selections and ordering",
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant hashtags for social media",
            },
        },
    },
}
