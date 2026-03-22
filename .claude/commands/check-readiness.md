---
description: Full readiness check for a video slug — pre-process, scene match, cut beats, score, report
allowed-tools: Bash, Read, Write, Glob, Grep
---

Run the complete pre-processing pipeline for `$ARGUMENTS` and produce a readiness report.

## Overview

This command orchestrates the full pipeline from raw input to readiness report. It wipes production clean and starts fresh every time — no stale state, always a full check.

**Slug**: `$ARGUMENTS` (e.g., `/check-readiness 2026-03-24-my-video`)

## Steps

### Step 1: Clean slate

Delete `video-content/production/{slug}/` if it exists. Start fresh.

```bash
rm -rf video-content/production/{slug}/
```

### Step 2: Run pre-processing (CLI — steps 1-3)

```bash
videngine pre-process {slug}
```

This handles: ingest → audio preprocessing → transcription. Wait for it to complete. If it fails, stop and report the error.

### Step 3: Scene matching (agent intelligence — step 4)

This is the step that requires judgment. You must:

1. **Read the coached script** from `video-content/production/{slug}/` (the `.md` file)
2. **Read all transcripts** from `video-content/production/{slug}/transcripts/*/transcript.json`
3. **Read the JSON sidecar** (the `.json` file) for beat definitions

For each beat in the script:

a. **Fuzzy-match** the beat's content against the transcripts. David improvises from pointers — the words won't be identical, but the meaning and key phrases will match. Look for:
   - Key phrases that are bolded in the script
   - The core idea/argument of each beat
   - Approximate position in the recording (beats are roughly sequential)

b. **Identify timecode ranges** in the source transcript(s) that correspond to each beat.

c. **Detect multiple takes** — if David repeated a section (you'll see similar content appearing twice in the transcript), mark each occurrence as a separate take.

d. **Flag missing beats** — if a beat's content doesn't appear in any transcript.

e. **Record confidence** — how confident you are in the match (0-100%).

**Output**: Write `video-content/production/{slug}/beats/beat_map.json`:

```json
[
  {
    "beat": 1,
    "name": "hook",
    "source_file": "video-content/production/{slug}/filename.mp4",
    "start": 12.5,
    "end": 48.2,
    "confidence": 94,
    "takes": [
      { "start": 12.5, "end": 48.2, "notes": "clean delivery" }
    ],
    "matched_phrases": ["key phrase from script that was found"],
    "missing_phrases": ["key phrase that was NOT found"]
  },
  {
    "beat": 2,
    "name": "setup",
    "source_file": "video-content/production/{slug}/filename.mp4",
    "start": 50.0,
    "end": 135.8,
    "confidence": 91,
    "takes": [
      { "start": 50.0, "end": 95.3, "notes": "stumble at 1:12" },
      { "start": 98.0, "end": 135.8, "notes": "cleaner second attempt" }
    ],
    "matched_phrases": ["..."],
    "missing_phrases": []
  }
]
```

Create the `beats/` directory if needed.

### Step 4: Run beat processing (CLI — steps 5-7)

```bash
videngine cut-beats {slug}
```

This handles: cut all takes → re-transcribe → VAD + emotion2vec scoring. Wait for completion.

### Step 5: Delivery comparison + take selection (agent intelligence — step 8)

Read `video-content/production/{slug}/beats/beat_analysis.json` (output of cut-beats).
Read the JSON sidecar for target VAD per beat.

For each beat:

a. **Compare actual VAD vs target VAD** from the script/sidecar.
   - Match threshold: each dimension within ±0.15 = ✅, within ±0.25 = ⚠️, beyond = ❌

b. **Compare emotion2vec label** against expected delivery.
   - Script says high energy positive → should read "happy" or "surprised", not "neutral"
   - Script says urgent/tense → should read "angry" or "fearful", not "happy"

c. **Select best take** when multiple exists:
   - Primary criterion: VAD match to target
   - Secondary criterion: emotion2vec label fit
   - Tertiary criterion: word completeness (does the take cover all key phrases?)
   - If no single take is clearly best, consider splicing at sentence boundaries (only where a clear pause/break exists in both takes)

d. **Flag issues**:
   - Missing beats
   - VAD significantly off target
   - Emotion mismatch
   - Incomplete content (missing key phrases)

### Step 6: Update manifest

Update `video-content/production/{slug}/manifest.md`:
- Tick remaining checkboxes (delivery comparison, readiness review)
- Add delivery analysis table
- Add take selection table
- Add issues section

### Step 7: Write readiness report

Append to the manifest (or write as a clearly marked section):

```markdown
## Readiness Report

**Generated**: {YYYY-MM-DD HH:MM}
**Beats**: {N}/{total} found
**Takes**: {N} total across all beats
**Delivery match**: {N}/{total} on target

### Beat Summary

| Beat | Name | Takes | Selected | VAD Target | VAD Actual | VAD Match | Emotion | Notes |
|------|------|-------|----------|------------|------------|-----------|---------|-------|
| 1 | Hook | 1 | take-1 | V0.25 A0.75 D0.70 | V0.30 A0.80 D0.65 | ✅ | happy 82% | clean |
| 3 | Body 1 | 2 | take-2 | V0.65 A0.45 D0.50 | V0.60 A0.50 D0.55 | ✅ | neutral 71% | take-2 better VAD |
| 7 | Climax | 1 | take-1 | V0.70 A0.75 D0.75 | V0.45 A0.35 D0.50 | ❌ | neutral 65% | flat delivery |

### Issues

{list any problems with recommended actions}

### Recommendation

{overall assessment — ready to edit, or needs re-recording of specific beats}
```

### Step 8: Summary

Print the readiness report to the console.

$ARGUMENTS
