# Chapter 3: Retention Diagnosis

Predict where viewers will drop off by analyzing pacing, visual variety, and pattern
interrupt distribution. The reviewer works from the finished clip, not from analytics.

---

## 3.1 Retention Curve Prediction

Without post-publish data, predict the retention curve shape from editing patterns:

| Editing Pattern | Predicted Curve Shape | Severity |
|----------------|----------------------|----------|
| Weak or missing hook (0-8s) | Cliff drop | BLOCKER |
| Long branded intro (>5s before value) | Steep early decline | ISSUE |
| No visual change for >15s | Localized dip at that timestamp | ISSUE |
| No pattern interrupt for >90s | Gradual linear decline | ISSUE |
| Single visual type throughout | Steady decline | ISSUE |
| Strong hook + consistent pacing | Flat or gradual decline | PASS |
| Hook + burst-calm rhythm | Flat with small bumps | PASS (ideal) |

---

## 3.2 Pacing Audit

Measure visual change frequency throughout the clip and compare to benchmarks.

### Expected Change Frequency

| Content Type | Target Interval | Tolerance |
|-------------|----------------|-----------|
| Short-form (<60s) | 2-4 seconds | Max 6s without change |
| Long-form talking head | 15-25 seconds | Max 30s without change |
| Screen recording / tutorial | 10-20 seconds | Max 25s without change |
| Action / energetic | 3-7 seconds | Max 10s without change |

### How to Audit

1. Watch the clip and timestamp every visual change (cut, zoom, B-roll, graphic, text overlay)
2. Calculate intervals between changes
3. Flag any interval that exceeds the tolerance for the content type
4. Flag any 90-second window without a pattern interrupt

### Pacing Arc Check (Long-Form, 3+ Minutes)

| Phase | Expected | Diagnosis if Missing |
|-------|----------|---------------------|
| Opening (0-60s) | Highest energy, changes every 10-15s | ISSUE — "front-loaded energy missing" |
| Body (1-7 min) | Steady rhythm, 15-25s intervals | NOTE if slightly slow |
| Burst sequences | 5-10 rapid cuts every 2-3 min | ISSUE — "no re-engagement moments" |
| Final 30s | Energy maintained or rising | ISSUE — "energy drops before end" |

---

## 3.3 Static Segment Detection

A static segment is any continuous period where the visual content does not meaningfully
change (same framing, same angle, no overlays, no movement).

| Duration | Severity | Diagnosis |
|----------|----------|-----------|
| 5-10s | NOTE | Acceptable if speech is compelling |
| 10-15s | ISSUE | "Static segment — likely retention dip" |
| 15-20s | ISSUE (HIGH) | "Extended static segment — viewer attention at risk" |
| >20s | BLOCKER | "Critical static segment — viewers will leave" |

Detection method: frame-by-frame difference analysis. If pixel difference stays below
threshold for >10 seconds, flag it.

---

## 3.4 Pattern Interrupt Audit

Count and classify pattern interrupts throughout the clip:

| Type | Examples | Impact Level |
|------|----------|-------------|
| Audio + visual simultaneous | Music shift + cut | Highest |
| Content category break | Meme insert, animation in talking-head | High |
| Scale change | Wide → close-up or vice versa | Medium-high |
| Color/grade shift | Temperature change, desaturation | Medium |
| Text overlay / graphic | Stat, title, callout | Medium |
| Angle change | Same subject, different angle | Low-medium |
| Zoom (Ken Burns) | Slow zoom in/out | Low-medium |
| Sound effect | Whoosh, ding, transition sound | Low |

### Audit Rules

- **Minimum**: At least 1 pattern interrupt per 90 seconds
- **Ideal**: Visual change every 15-25 seconds with higher-impact interrupts every 60-90s
- **Opening 60s**: Should have the highest interrupt density
- **Variety**: Flag if the same type of interrupt is used >3 times consecutively
  (the brain adapts — repeated identical interrupts lose impact per Von Restorff)

---

## 3.5 Information Density Assessment

Too dense = cognitive overload (viewers stop processing). Too sparse = boredom (viewers leave).

| Signal | Diagnosis |
|--------|-----------|
| >4 on-screen elements simultaneously | "Cognitive overload risk — too many competing elements" |
| Text overlay that duplicates narration verbatim | "Redundancy violation (Mayer) — complement, don't repeat" |
| Complex visual (code, dashboard) without highlighting | "No signaling — viewer doesn't know where to look" |
| >30s of speech with no visual support | "Information without illustration — retention risk" |
| Rapid-fire stats/claims without breathing room | "Information density too high — needs segmentation" |

---

## 3.6 Engagement Continuation Signals

Predict whether the video will generate session continuation (YouTube's key satisfaction signal):

| Signal | Present? | Impact |
|--------|----------|--------|
| Clear CTA to next video | ✓/✗ | Strong — directly drives session |
| End screen with related content | ✓/✗ | Strong — YouTube's designed mechanism |
| Unresolved thread pointing to next video | ✓/✗ | Strongest — curiosity drives continuation |
| Abrupt ending without closure | ✓/✗ | Negative — viewer leaves YouTube |
| "Subscribe" CTA before value delivered | ✓/✗ | Negative — premature ask damages trust |
