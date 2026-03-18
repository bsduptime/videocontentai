# Chapter 7: Feedback Format

How the reviewer communicates findings. Structured, timecoded, actionable — following the
SBI model and Pixar Braintrust principles.

---

## 7.1 The SBI Framework for Video Notes

Every feedback item follows **Situation-Behavior-Impact**:

| Component | What It Contains | Example |
|-----------|-----------------|---------|
| **Situation** | Timecode or time range | "At 0:23-0:35" |
| **Behavior** | Observable fact about the clip (not interpretation) | "The visual stays on the same talking-head framing with no cuts, overlays, or camera changes for 12 seconds" |
| **Impact** | Effect on the viewer or publishing outcome | "Viewers will experience attention drift here — this is the longest static segment in the clip and falls during an explanation that needs visual support" |

### What SBI is NOT

- NOT prescriptive: "Add B-roll at 0:25" ← this is a fix, not a diagnosis
- NOT vague: "The middle section is boring" ← no timecode, no observable behavior
- NOT subjective preference: "I don't like the music" ← not viewer-impact focused

---

## 7.2 Feedback Categories

Organize all notes into three tracks (adapted from Filestage):

| Track | What It Covers | Who Cares |
|-------|---------------|-----------|
| **Technical** | Audio levels, encoding, resolution, artifacts, sync | Always checked |
| **Editorial** | Hook, pacing, emotional arc, retention risks | Core of the review |
| **Platform** | Safe zones, duration, format, algorithm compliance | Checked per target platform |

---

## 7.3 Review Report Format

The reviewer outputs a structured JSON report per clip:

```json
{
  "clip": "highlight",
  "spec_name": "highlight",
  "duration_actual": 47.3,
  "duration_spec": [30, 60],
  "verdict": "PUBLISH WITH NOTES",
  "composite_score": 72,
  "dimension_scores": {
    "hook": 78,
    "pacing": 65,
    "audio": 88,
    "emotion": 70,
    "visual": 85,
    "platform": 80,
    "structure": 75,
    "accessibility": 60
  },
  "arc_shape": "man_in_a_hole",
  "hook_template": "stat",
  "hook_score": 78,
  "blockers": [],
  "issues": [
    {
      "severity": "ISSUE",
      "category": "editorial",
      "timestamp": "0:23-0:35",
      "situation": "At 0:23-0:35",
      "behavior": "12-second static talking-head segment with no visual changes",
      "impact": "Likely retention dip — longest static segment in clip, falls during technical explanation",
      "dimension_affected": "pacing"
    },
    {
      "severity": "ISSUE",
      "category": "editorial",
      "timestamp": "0:42-0:47",
      "situation": "Final 5 seconds",
      "behavior": "Energy drops as speaker says 'anyway, that's basically it'",
      "impact": "Weak ending violates peak-end rule — viewer's last impression will be deflated",
      "dimension_affected": "emotion"
    }
  ],
  "notes": [
    {
      "severity": "NOTE",
      "category": "platform",
      "timestamp": "0:00",
      "situation": "First frame",
      "behavior": "No text overlay on opening frame",
      "impact": "60%+ of short-form viewers watch muted — hook relies entirely on audio",
      "dimension_affected": "accessibility"
    }
  ],
  "strengths": [
    "Strong stat-based hook (78/100) — opens with specific number that creates curiosity",
    "Audio levels well-balanced throughout — music ducks cleanly during speech",
    "Clean emotional arc (man-in-a-hole) with identifiable peak at 0:18"
  ],
  "plan_alignment": {
    "duration_match": true,
    "segments_match": true,
    "mood_match": true,
    "effects_applied": false,
    "narration_match": true
  }
}
```

---

## 7.4 Summary Report

When reviewing multiple clips from the same job, output a summary:

```json
{
  "job_id": "dbexpertai-20260319-abc123",
  "total_clips": 4,
  "verdicts": {
    "hook": {"verdict": "PUBLISH", "score": 82},
    "highlight": {"verdict": "PUBLISH WITH NOTES", "score": 72},
    "focused_tutorial": {"verdict": "HOLD", "score": 58},
    "deep_dive": {"verdict": "HOLD", "score": 51}
  },
  "publish_ready": ["hook", "highlight"],
  "needs_work": ["focused_tutorial", "deep_dive"],
  "top_issues": [
    "focused_tutorial: 3 static segments >15s (pacing)",
    "deep_dive: no pattern interrupts in minutes 4-8 (pacing)",
    "deep_dive: emotional flatline minutes 6-9 (arc)"
  ]
}
```

---

## 7.5 Stop-Start-Continue Format

For human-readable feedback (not JSON), use three buckets:

**STOP** — Things hurting the video that should be eliminated:
- "Stop: 12-second static segment at 0:23 with no visual variety"
- "Stop: 'anyway, that's basically it' ending — energy drops"

**START** — Things not present that should be added:
- "Start: text overlay on opening frame for muted viewers"
- "Start: pattern interrupt in the 0:23-0:35 segment"

**CONTINUE** — Things working well that should be kept:
- "Continue: strong stat-based hook — specific number creates immediate curiosity"
- "Continue: clean audio ducking — music drops smoothly under speech"

---

## 7.6 Review Cycle Rules

Based on research: 2-3 review rounds is optimal. More than 5 is a process failure.

| Round | Focus | What Changes |
|-------|-------|-------------|
| **Round 1** | Structure + blockers | Major issues. Can the clip be published at all? |
| **Round 2** | Issues + editorial polish | Addressed blockers. Now refine pacing, arc, platform fit. |
| **Round 3** | Final pass | Verify fixes. Notes only. Should not introduce new issues. |

### Diminishing Returns Signal

If round 3 introduces new issues not present in round 2, the review process has a problem —
either the reviewer is being inconsistent or the fixes created new issues. Escalate rather
than adding round 4.

### The Fresh Eyes Principle

The reviewer must NOT be the same person/agent that edited the video. The editor has "tunnel
vision" — they see what they intended, not what actually plays. Fresh eyes catch:
- Assumptions baked into the edit that a new viewer doesn't share
- Logical gaps where the editor's knowledge fills in missing context
- Pacing issues the editor stopped noticing after repeated viewing
- Audio problems masked by familiarity

In our pipeline: the `/cut` skill edits, the content-reviewer skill reviews. They are
deliberately separate to enforce this principle.
