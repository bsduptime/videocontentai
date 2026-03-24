# Chapter 4: Emotional Arc Analysis

Map the viewer's emotional journey through the video. Identify where the arc breaks,
flattens, or contradicts the intended mood.

---

## 4.1 The Six Canonical Arcs

Reagan et al. (University of Vermont) data-mined 1,300+ narratives and identified six
fundamental emotional arc shapes. Every video follows one (or a broken version of one):

| Arc | Shape | Pattern | Best For |
|-----|-------|---------|----------|
| **Rags to Riches** | Steady rise | Problem → solution → success | Tutorials, case studies |
| **Tragedy** | Steady fall | Setup → escalating problems → failure | Cautionary tales, post-mortems |
| **Man in a Hole** | Fall → rise | Problem → struggle → resolution | Most YouTube content (default arc) |
| **Icarus** | Rise → fall | Success → hubris → failure | Contrarian takes, "what went wrong" |
| **Cinderella** | Rise → fall → rise | Hope → setback → triumph | Comeback stories, personal brand |
| **Oedipus** | Fall → rise → fall | Problem → false solution → real problem | Tension-driven hooks, drama |

### Diagnostic Use

1. Map valence (positive/negative emotional state) at each major segment
2. Identify which arc the video follows
3. Check: is the arc **clean** (smooth transitions) or **broken** (unintentional tone shifts)?
4. A broken arc predicts lower engagement — the viewer's emotional expectations are violated

---

## 4.2 Peak-End Rule Audit

Viewers judge a video by its **most intense moment** (peak) and its **final moment** (end).
The middle matters less than these two points.

### Peak Checklist

| Check | Pass | Fail |
|-------|------|------|
| At least one clear emotional peak exists | The video has a moment of genuine surprise, insight, humor, or tension | The video is uniformly "fine" — no moment stands out |
| Peak is not in the first 30 seconds | Peak is placed mid-video or in the climax zone (80-90% through) | The best moment is in the intro, then the video deflates |
| Each peak is emotionally distinct | Peaks vary (surprise, then humor, then insight) | Same emotional beat repeated |
| Peak intensity matches content type | Tutorial: "aha moment." Story: emotional climax. Demo: visual proof | Peak feels forced or absent |

### End Checklist

| Check | Pass | Fail |
|-------|------|------|
| Final 10 seconds are emotionally resonant | Satisfying conclusion, callback, or forward tease | Fizzles out, trails off, or ends abruptly |
| No "winding down" signals | Energy maintained through the end | "Anyway, that's all for today" energy drop |
| End creates desire for more | Points to next video, opens new question | Closes everything — no reason to continue |

### Severity

- No identifiable peak: ISSUE
- Peak in wrong position (too early): ISSUE
- Weak ending (energy drops, trails off): ISSUE
- Strong peak + strong ending: PASS — this video will be remembered favorably

---

## 4.3 Mood-Content Alignment

Compare the music mood (from cut plan) against the content's actual emotional tone:

| Mood | Expected Content Tone | Misalignment Example |
|------|----------------------|---------------------|
| **drive** (positive/high arousal) | Confident, upbeat, forward momentum | Drive music under somber/serious content |
| **silence** (negative/high arousal beats) | Urgent, dramatic, high stakes | Music playing under problem statements or stakes (should be silent) |
| **steady** (positive/low arousal) | Calm, educational, measured | Steady music under exciting/surprising content |

**Misalignment is not always wrong** — silence + calm delivery = "something is wrong" (intentional unease). But **unintentional** misalignment is an ISSUE.

### How to Diagnose

1. Read the cut plan's `mood` field
2. Watch the clip and note the dominant emotional tone of the speech
3. If the music mood contradicts the speech tone without clear creative intent, flag as ISSUE
4. Check: does the music end on drive or steady (positive)? Ending on silence is acceptable only if the final beat is immediately followed by a positive-mood re-entry.

---

## 4.4 Emotional Flatline Detection

An emotional flatline is a segment where neither the content nor the delivery creates any
emotional variation — monotone speech, static visuals, no music change, no narrative tension.

| Duration | Severity |
|----------|----------|
| 10-20s | NOTE — "emotional energy dips here" |
| 20-40s | ISSUE — "extended flatline — viewer disengagement risk" |
| >40s | ISSUE (HIGH) — "prolonged flatline — likely retention drop" |

### Signals of Flatline

- Speaking rate stays constant (no acceleration or pauses)
- No pitch variation in voice
- Music level and energy unchanged
- No visual changes (same framing, no overlays)
- Content is explanatory without examples, stories, or proof

---

## 4.5 Tension-Release Rhythm

Good videos alternate between tension (building curiosity, posing problems, creating stakes)
and release (delivering answers, showing proof, providing relief).

### Audit

1. Mark each segment as T (tension) or R (release)
2. Check the pattern: healthy videos alternate T-R-T-R
3. Flag: T-T-T (tension without release = viewer frustration)
4. Flag: R-R-R (release without tension = no reason to keep watching)
5. The video should end on R (satisfying resolution)

**Duration neglect**: A video with one great peak (T→R) and a strong ending is remembered
more favorably than 5 minutes of uniform "pretty good." Valleys make peaks stand out.
