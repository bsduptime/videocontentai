"""Structured output JSON schemas for Claude tool use."""

from __future__ import annotations

ANALYZE_TRANSCRIPT_TOOL = {
    "name": "analyze_transcript",
    "description": (
        "Analyze and score every transcript segment on editorial criteria. "
        "Score each segment 1-10, tag it, identify themes, and recommend hook candidates."
    ),
    "input_schema": {
        "type": "object",
        "required": [
            "scored_segments",
            "overall_themes",
            "recommended_hook_ids",
        ],
        "properties": {
            "scored_segments": {
                "type": "array",
                "description": "Every transcript segment scored and tagged",
                "items": {
                    "type": "object",
                    "required": [
                        "segment_id",
                        "start",
                        "end",
                        "text",
                        "score",
                        "tags",
                        "topic",
                        "summary",
                    ],
                    "properties": {
                        "segment_id": {
                            "type": "integer",
                            "description": "ID of the transcript segment",
                        },
                        "start": {
                            "type": "number",
                            "description": "Start time in seconds",
                        },
                        "end": {
                            "type": "number",
                            "description": "End time in seconds",
                        },
                        "text": {
                            "type": "string",
                            "description": "The spoken text in this segment",
                        },
                        "score": {
                            "type": "integer",
                            "description": "Editorial quality score 1-10",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags: strong_hook, high_density, emotional, funny, contrarian, technical, story, filler, repetitive",
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topic label for this segment",
                        },
                        "summary": {
                            "type": "string",
                            "description": "One-line summary of the segment's content",
                        },
                    },
                },
            },
            "overall_themes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5 major themes across the full transcript",
            },
            "recommended_hook_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Segment IDs that would make strong hooks (attention-grabbing, surprising, contrarian)",
            },
        },
    },
}

CREATE_CUT_PLAN_TOOL = {
    "name": "create_cut_plan",
    "description": (
        "Create a cut plan for a specific content format. Select the best segments "
        "from the scored analysis, explain what was dropped and why, and write narration."
    ),
    "input_schema": {
        "type": "object",
        "required": [
            "spec_name",
            "segments",
            "dropped_segments",
            "full_text",
            "edit_rationale",
            "intro_narration",
            "outro_narration",
            "title",
            "description",
            "hashtags",
            "total_estimated_duration",
        ],
        "properties": {
            "spec_name": {
                "type": "string",
                "description": "Name of the cut spec this plan is for",
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
            "dropped_segments": {
                "type": "array",
                "description": "Segments that were considered but not included",
                "items": {
                    "type": "object",
                    "required": [
                        "segment_ids",
                        "start",
                        "end",
                        "text",
                        "drop_reason",
                    ],
                    "properties": {
                        "segment_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "IDs of dropped transcript segments",
                        },
                        "start": {
                            "type": "number",
                            "description": "Start time in seconds",
                        },
                        "end": {
                            "type": "number",
                            "description": "End time in seconds",
                        },
                        "text": {
                            "type": "string",
                            "description": "The spoken text",
                        },
                        "drop_reason": {
                            "type": "string",
                            "description": "Why this segment was dropped",
                        },
                    },
                },
            },
            "full_text": {
                "type": "string",
                "description": "The full concatenated text of all selected segments",
            },
            "edit_rationale": {
                "type": "string",
                "description": "Overall editorial reasoning for the selections and ordering",
            },
            "intro_narration": {
                "type": "string",
                "description": "Script for the voice-cloned intro narration (1-2 sentences, hook the viewer)",
            },
            "outro_narration": {
                "type": "string",
                "description": "Script for the voice-cloned outro narration (1-2 sentences, CTA)",
            },
            "title": {
                "type": "string",
                "description": "Compelling title for this cut",
            },
            "description": {
                "type": "string",
                "description": "Short description for social media (1-2 sentences)",
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant hashtags for social media",
            },
            "total_estimated_duration": {
                "type": "number",
                "description": "Estimated total duration of selected segments in seconds",
            },
        },
    },
}
