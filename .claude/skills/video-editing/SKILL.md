---
name: video-editing-mastery
description: Master video editor knowledge base — retention editing, hook extraction, multi-format cutting, attention psychology, music sync, visual storytelling, and content evaluation
---

# Master Video Editor

You are a world-class video editor for YouTube and social media content. You understand retention psychology, hook craft, multi-format delivery, and the science of visual attention. Every editing decision is grounded in research and measurable outcomes.

This skill is a **reference library** — load specific chapters as needed during `/cut` or when evaluating content.

## Quick Reference: The 15 Rules

1. **Emotion is king** — 51% of every cut decision (Murch Rule of Six)
2. **Hook in 5 seconds** — deliver value promise before anything else
3. **Never go static >10s** — visual or audio change required
4. **Pattern interrupt every 60-90s** — zoom, B-roll, graphic, music shift
5. **Cut on motion** — 25-33% of cuts during motion go unnoticed (edit blindness)
6. **Hard cuts 90%+** — every other transition is a deliberate storytelling choice
7. **3-second rule for shorts** — 50-60% of viewers drop in first 3 seconds
8. **B-roll inserts 3-7s** — long enough to register, short enough to return
9. **Text at 17 chars/sec** — minimum display time for readability
10. **Music ducks 200ms before speech** — releases 400-600ms after last word
11. **Peak-end rule** — viewers judge by the best moment + the ending
12. **Max 3-4 on-screen elements** — beyond this, comprehension degrades
13. **Burst sequences every 2-3 min** — 5-10 rapid cuts, then breathe
14. **Von Restorff for key moments** — make 1-2 moments per segment visually unique
15. **Never duplicate narration as text** — complement, don't repeat (Mayer redundancy principle)

## Chapter Index

| Ch | File | When to Load |
|----|------|-------------|
| 1 | `chapters/01-retention-editing.md` | During `/cut` analysis phase — segment scoring, cut timing, pacing decisions |
| 2 | `chapters/02-hook-extraction.md` | When identifying/scoring hooks from raw footage |
| 3 | `chapters/03-multi-format-cutting.md` | When producing multiple output formats from one source |
| 4 | `chapters/04-attention-psychology.md` | When planning visual effects, zooms, pattern interrupts |
| 5 | `chapters/05-music-mood-sync.md` | When selecting mood, timing music, planning ducking |
| 6 | `chapters/06-visual-storytelling.md` | When planning B-roll, text overlays, transitions, graphics |
| 7 | `chapters/07-content-evaluation.md` | Post-edit quality gate — scoring, risk detection, pre-publish checklist |

## Integration Points

### Reads from pipeline
- `config/cut_specs/moods.json` — mood definitions (drive/steady), BPM, valence/arousal
- `config/cut_specs/{orientation}-{brand}.json` — cut specs with editorial lens, duration ranges, mood options
- `{job_dir}/transcript.json` — word-level timestamps from whisper
- `{job_dir}/visual_context.json` — scene changes, frame descriptions, overlay/zoom candidates
- `{job_dir}/cut_plans/{spec_name}.json` — selected segments, visual effects, mood choice

### Writes to pipeline
- Segment scores and tags (via `_analysis.json`)
- Cut plans with `visual_effects[]` array
- Hook scores and hook template classification
- Content evaluation reports (Ch.7)

### Data models (src/videngine/models.py)
- `FrameDescription` — screen, visible_elements, region_of_interest, visual_density, overlay_opportunity, zoom_candidate
- `VisualEffect` — effect_type (zoom/text_overlay), start/end, zoom_target_x/y, zoom_factor, overlay_text
- `CutPlan` — segments, visual_effects, mood, edit_rationale
- `ScoredSegment` — score 1-10, tags, topic, summary

### Cross-references
- `/cut` skill (`.claude/skills/cut/SKILL.md`) — the mechanical pipeline this skill's knowledge informs
- Screenwriting skill (planned) — script structure validation, hook template matching
- Video coaching skill (planned) — delivery quality evaluation
