# Chapter 6: Scoring System

The composite scoring rubric. Combines all diagnostic chapters into a single weighted score
that drives the publish/hold/fail verdict.

---

## 6.1 Scoring Dimensions

Eight dimensions, each scored 0-100, then weighted to produce a composite score.

| Dimension | Weight | What It Measures | Source Chapter |
|-----------|--------|-----------------|---------------|
| **Hook quality** | 20% | First-impression effectiveness | Ch.2 |
| **Pacing & rhythm** | 20% | Cut frequency, pattern interrupts, visual variety | Ch.3 |
| **Audio technical** | 15% | Loudness, peaks, voice/music ratio, artifacts | Ch.1 |
| **Emotional arc** | 15% | Peak-end rule, tension-release, mood alignment | Ch.4 |
| **Visual technical** | 10% | Resolution, encoding, artifacts, watermark | Ch.1 |
| **Platform readiness** | 10% | Safe zones, duration, format, algorithm signals | Ch.5 |
| **Structure** | 5% | Intro/outro, CTA, hook prepend, clean start/end | Ch.1 |
| **Accessibility** | 5% | Captions, text readability, sound-off test | Ch.1, Ch.2 |

### Composite Score Formula

```
composite = (hook * 0.20) + (pacing * 0.20) + (audio * 0.15) + (emotion * 0.15)
          + (visual * 0.10) + (platform * 0.10) + (structure * 0.05) + (access * 0.05)
```

---

## 6.2 Per-Dimension Scoring Guides

### Hook Quality (0-100)

Use the hook diagnostic checklist from Ch.2 (six criteria, total out of 100).

### Pacing & Rhythm (0-100)

| Score Range | Description |
|-------------|------------|
| 90-100 | Consistent rhythm matching content type. Burst sequences present. No static segments >5s. |
| 70-89 | Good overall pacing with minor dead spots. Pattern interrupts present but could be more varied. |
| 50-69 | Noticeable pacing issues. 1-2 static segments >10s. Insufficient pattern interrupt variety. |
| 30-49 | Significant pacing problems. Multiple static segments. No burst sequences in 3+ min content. |
| 0-29 | Monotonous. Single visual type throughout. No evidence of intentional pacing. |

### Audio Technical (0-100)

| Score Range | Description |
|-------------|------------|
| 90-100 | All audio checks pass. Loudness on target. Clean separation. No artifacts. |
| 70-89 | Minor issues (levels slightly off, one brief artifact). All within tolerance. |
| 50-69 | Noticeable issues. Music too loud in places. Levels inconsistent between segments. |
| 30-49 | Significant audio problems. Clipping, poor separation, or missing music. |
| 0-29 | Audio is broken. Multiple blockers. |

### Emotional Arc (0-100)

| Score Range | Description |
|-------------|------------|
| 90-100 | Clean arc with identifiable peaks. Strong ending. Mood-content aligned. T-R rhythm present. |
| 70-89 | Arc is present but could be stronger. Peak exists but isn't positioned optimally. |
| 50-69 | Arc is vague or broken. Emotional flatlines present. Mood alignment questionable. |
| 30-49 | No discernible arc. Extended flatlines. Mood contradicts content. |
| 0-29 | Emotionally incoherent. No peaks, weak ending, broken arc. |

### Visual Technical (0-100)

All video QC checks from Ch.1 scored as deductions from 100. Each BLOCKER = -30,
each ISSUE = -15, each NOTE = -5.

### Platform Readiness (0-100)

All platform checks from Ch.5 scored as deductions from 100. Each failed check deducts
based on its severity.

### Structure (0-100)

Score based on structural QC from Ch.1 section 1.4.

### Accessibility (0-100)

Score based on captions, text readability, and sound-off test from Ch.1 and Ch.2.

---

## 6.3 Verdict Logic

```
IF any BLOCKER exists:
    verdict = "HOLD" (minimum), regardless of score

IF composite >= 80 AND no BLOCKERs:
    verdict = "PUBLISH"

IF composite >= 65 AND composite < 80 AND no BLOCKERs:
    verdict = "PUBLISH WITH NOTES"

IF composite >= 45 AND composite < 65:
    verdict = "HOLD"

IF composite < 45:
    verdict = "FAIL"
```

---

## 6.4 Severity Triage Rules

### BLOCKER (Must Fix Before Publishing)

- Audio clipping (true peak > -1 dBTP)
- Wrong resolution or aspect ratio
- Duration outside cut spec range
- Corrupt or missing frames
- Mid-sentence cuts (words cut mid-syllable)
- Hook score < 40
- Static segment > 20 seconds
- Copyright-infringing content
- Visible personal data

### ISSUE (Should Fix, Holds Publishing if Multiple)

- Music too loud over voice (separation < 10 dB)
- Loudness outside -14 LUFS ±2
- Missing intro/outro on non-hook clips
- No pattern interrupt for >90s
- Static segment 10-20s
- Mood-content misalignment
- Text outside safe zone
- Missing captions on short-form
- Weak hook (score 40-59)

### NOTE (Minor, Creator's Discretion)

- Suboptimal bitrate
- Color inconsistency between segments
- Hook score 60-79 (acceptable but improvable)
- Missing thumbnail-worthy frame
- Slight audio level inconsistency
- Font size marginally small

### Accumulation Rule

- 3+ ISSUEs without BLOCKERs = "HOLD" (even if score is 65+)
- ISSUEs can be overridden by creator if acknowledged

---

## 6.5 Benchmarks by Content Type

Expected composite scores for different content types:

| Content Type | Target Score | Minimum Publishable |
|-------------|-------------|-------------------|
| YouTube long-form (educational) | 75+ | 60 |
| YouTube Shorts | 80+ | 65 |
| Hook clip | 70+ | 55 (lower bar — hooks are simple) |
| Highlight (30-60s) | 80+ | 65 |
| Deep dive (20+ min) | 70+ | 55 (pacing is harder at length) |

---

## 6.6 Comparison: Plan vs. Execution

The reviewer has access to the cut plan. Score the delta:

| Check | What to Compare | Severity if Mismatched |
|-------|----------------|----------------------|
| Duration | Plan's `total_estimated_duration` vs. actual | ISSUE if >20% difference |
| Segment coverage | Plan's selected segments vs. what's in the clip | ISSUE if segments missing |
| Mood | Plan's `mood` vs. music actually used | ISSUE if different |
| Visual effects | Plan's `visual_effects[]` vs. effects in clip | NOTE if effects missing |
| Narration | Plan's `intro_narration` vs. actual voiceover | ISSUE if voiceover missing or wrong |
