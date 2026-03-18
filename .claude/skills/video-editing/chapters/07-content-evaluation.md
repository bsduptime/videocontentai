# Chapter 7: Content Evaluation

The quality gate. This chapter turns the agent into a reviewer — scoring hooks, detecting
retention risks, grading pacing, and running a pre-publish checklist.

---

## 7.1 Retention Curve Pattern Recognition

When evaluating edited content (or analyzing past videos with analytics data):

| Curve Shape | Diagnosis | Editing Fix |
|-------------|-----------|-------------|
| **Cliff drop (0-8s)** | Thumbnail/title mismatch or weak hook | Cut intro to <3s, deliver value promise in first 5s |
| **Steep decline (0-60s)** | 55%+ lost in first minute | Restructure: action first, context second |
| **Gradual linear decline** | Pacing fatigue, no interrupts | Add stimulus change every 60-90s |
| **Mid-video cliff** | Energy dip or boring segment | Cut segment, add B-roll, or insert interrupt 15s before |
| **Flat line** | Gold standard | Replicate this structure |
| **Spike (upward bump)** | High-value rewatchable moment | Identify what made it compelling |
| **Dip then recovery** | Skippable segment | Cut or compress that segment |

**Key benchmark**: Average YouTube video retains 23.7%. Only 16.8% exceed 50% retention.
Improving retention 10 percentage points → 25%+ increase in impressions.

---

## 7.2 Video Quality Rubric (1-5 Scale)

| Dimension | 1 (Fail) | 3 (Acceptable) | 5 (Excellent) |
|-----------|----------|-----------------|---------------|
| **Hook** | No hook, slow start, >8s to value | Clear but generic | Curiosity gap + visual/verbal in <5s |
| **Pacing** | Static segments >15s | Cuts every 5-10s, some dead spots | Consistent rhythm, interrupts every 60-90s |
| **Audio** | Clipping, inconsistent levels | Stable levels, basic music | -14 LUFS, 10-15dB voice/music separation |
| **Visual variety** | Single static angle | Some angles, some B-roll | Dynamic cuts, B-roll, text, graphics |
| **Narrative arc** | No structure | Beginning/middle/end | Clear promise, rising tension, payoff, CTA |
| **Brand consistency** | Random style | Mostly consistent | Uniform palette, fonts, lower thirds |
| **Accessibility** | No captions | Auto-captions | Edited captions, visual emphasis |
| **CTA** | None or in first 15s | End-of-video CTA | Mid-video after value + end screen |

**Minimum publish threshold**: Average >= 3.0, no dimension below 2.

---

## 7.3 Hook Grading (0-100)

| Criterion | Points | Detection Method |
|-----------|--------|-----------------|
| **Value promise in first 5s** | 0-20 | Transcript: promise, tease, or question in first 5s of speech? |
| **Visual stimulus in first 3s** | 0-15 | Scene change, motion, face, or text overlay in first 3s? |
| **Curiosity gap** | 0-20 | Open question, tease, or incomplete narrative? |
| **No wasted frames** | 0-15 | No branded intro >3s, no "hey guys" greeting? |
| **Stakes by 15s** | 0-15 | Consequence language: "if you don't", "the problem is"? |
| **Audio energy** | 0-15 | Music present, pace >150 WPM, rising intonation? |

| Score | Grade | Action |
|-------|-------|--------|
| 80-100 | Ship it | Publish |
| 60-79 | Acceptable | Minor tweaks |
| 40-59 | Weak | Rework hook |
| <40 | Failed | Rewrite |

---

## 7.4 Retention Risk Detection

Automated flags the agent should check in every edited clip:

| Risk Signal | Detection | Severity |
|-------------|-----------|----------|
| Static visual segment >10s | Frame difference below threshold | HIGH |
| No scene change for >20s | Scene detection gap | CRITICAL |
| Audio energy drop >6dB for >5s | RMS measurement window | MEDIUM |
| No pattern interrupt for >90s | Count scene changes + text + music changes | HIGH |
| Talking head without B-roll >30s | Face detection + no scene change | MEDIUM |
| Dead air / silence >2s | Audio RMS below -40dB | HIGH |
| Filler words density >15% | Transcript word matching (um, uh, like, you know) | MEDIUM |
| Unresolved open loop | Question posed without answer within 120s | MEDIUM |
| Branded intro >5s | Template detection | HIGH |
| Audio clipping (true peak > -1dBTP) | Peak measurement | CRITICAL |

**Impact data**: Videos with pattern interrupts every 4 seconds average 58% retention vs.
41% for static talking-head.

---

## 7.5 Pacing Benchmarks by Content Type

| Content Type | Cuts/Minute | Visual Change Interval | Optimal Duration |
|-------------|-------------|----------------------|-----------------|
| YouTube Shorts (tutorial) | 15-30 | 2-4s | 25-40s |
| YouTube Shorts (comedy) | 15-30 | 2-4s | 18-28s |
| Long-form educational | 8-15 | 5-8s | 8-15 min |
| Long-form entertainment | 12-20 | 3-5s | 10-20 min |
| Long-form interview | 5-10 | 8-15s | 15-45 min |

**Pacing structure check (long-form)**:
- Minutes 0-3: High energy, cuts every 10-20s? ✓/✗
- Minutes 3-7: Stabilized, 25-40s spacing? ✓/✗
- Minutes 8+: Burst-calm rhythm present? ✓/✗

---

## 7.6 Thumbnail Moment Detection

Score extracted frames for thumbnail potential (0-100):

| Criterion | Points | Detection |
|-----------|--------|-----------|
| **Sharpness** | 0-20 | Laplacian variance (no motion blur) |
| **Face with expression** | 0-20 | Face detection + emotion (surprise/excitement scores high) |
| **High contrast** | 0-15 | Histogram spread, luminance delta |
| **Color saturation** | 0-10 | Mean saturation in HSV |
| **Low clutter** | 0-15 | Object count <= 3, clear subject isolation |
| **Represents content** | 0-10 | Frame from high-retention segment |
| **Text space available** | 0-10 | Clear zones for overlay text |

Prefer frames from the first 30% of video (they represent the "promise"). Viewers decide
to click in 0.3 seconds. 70% of YouTube views are on mobile (small thumbnails).

---

## 7.7 Common Editing Mistakes (Auto-Detectable)

| Mistake | Detection | Auto-fixable? |
|---------|-----------|---------------|
| Inconsistent audio levels between clips | LUFS per segment, >3 LUFS variance | Yes (loudnorm) |
| Music too loud over voice | Voice-to-music ratio <10dB | Yes (ducking) |
| Audio clipping | True peak > -1dBTP | Yes (limiter) |
| Dead air >2s | Audio RMS measurement | Yes (trim) |
| Filler words | Transcript matching | Yes (auto-cut) |
| Excessive transitions | Count non-cuts >2/min | No (flag) |
| No captions | Missing subtitle track | Yes (auto-generate) |
| Missing end screen | No elements in last 20s | No (flag) |
| Jump cuts without visual variety | Face-to-face cuts, <0.5s gap, no B-roll | No (flag) |

**Most impactful mistake**: Bad audio. "Nothing gets me to skip a video faster than loud
music or audio that's clipping."

---

## 7.8 Pre-Publish Quality Gate

Pass/fail checklist for every clip before it ships:

### Audio (Must Pass All)
- [ ] Integrated loudness: -14 LUFS ±1
- [ ] True peak: <= -1 dBTP
- [ ] Voice-to-music ratio: >= 10dB separation
- [ ] No silence gaps > 2s (unless intentional)

### Hook (Must Pass All)
- [ ] Hook score >= 60/100
- [ ] First 8s contains value promise
- [ ] No branded intro > 3s

### Pacing (Must Pass All)
- [ ] Cuts/min within benchmark for content type
- [ ] No static segment > 15s
- [ ] Pattern interrupt at least every 90s

### Visual (Must Pass All)
- [ ] Thumbnail candidate score >= 60/100
- [ ] Captions present
- [ ] Text overlays within safe zones

### Structure
- [ ] End screen present (last 20s contains CTA)
- [ ] CTA not in first 15s
- [ ] Filler word density < 5%
- [ ] Total duration within spec range

---

## 7.9 Composite Quality Score

Weighted scoring combining all evaluation dimensions:

| Category | Weight | Metric |
|----------|--------|--------|
| Hook Quality | 25% | Hook score (0-100) |
| Pacing & Retention Risk | 25% | Inverse of risk flags + benchmark adherence |
| Audio Technical | 20% | LUFS compliance + voice/music ratio + no clipping |
| Visual Quality | 15% | Scene variety + thumbnail candidate score |
| Structure & CTA | 10% | Narrative arc + CTA placement + end screen |
| Accessibility | 5% | Captions + filler removal |

### Final Score Interpretation

| Score | Action |
|-------|--------|
| 90-100 | Publish immediately |
| 75-89 | Publish with minor notes |
| 60-74 | Review flagged items before publishing |
| <60 | Do not publish — rework required |

---

## 7.10 Evaluation Report Format

When evaluating a completed edit, output a structured report:

```json
{
  "clip": "highlight",
  "duration": 45.2,
  "composite_score": 78,
  "hook_score": 82,
  "pacing_score": 75,
  "audio_score": 85,
  "visual_score": 70,
  "structure_score": 80,
  "accessibility_score": 90,
  "risk_flags": [
    {"timestamp": 23.5, "risk": "static_segment", "duration": 12.3, "severity": "HIGH",
     "fix": "Add B-roll or zoom at 23.5s to break static talking head segment"}
  ],
  "strengths": [
    "Strong hook (stat + contrarian template match)",
    "Audio levels well-balanced throughout"
  ],
  "improvements": [
    "Add pattern interrupt at 23.5s (12s static segment)",
    "Outro could link to related video"
  ],
  "publish_ready": true
}
```
