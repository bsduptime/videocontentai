# Chapter 5: Music & Mood Sync

Integrates with `config/cut_specs/moods.json` (drive/steady). Covers beat sync,
ducking, silence, emotional math, and volume levels.

---

## 5.1 Mood System: drive / steady (+ silence)

| Mood | Valence | Arousal | BPM | Editing Style |
|------|---------|---------|-----|---------------|
| **drive** | positive | high | 120 | Confident, upbeat, forward momentum. Tips, demos, hot takes, hooks. |
| **steady** | positive | low | 80 | Calm, unobtrusive, behind narration. Tutorials, deep dives. |

Drive at 120 BPM, steady at 80 BPM (2:3 ratio) for rhythmic compatibility. Problem statements, stakes, and negative-valence hooks use **silence** (no music) — delivery carries the urgency. Negative high-arousal music hurts recall.

---

## 5.2 Beat-Synced Cutting

Cut on **bar boundaries** (every 4 beats), not every individual beat.

| Mood | BPM | Bar duration | Cut alignment |
|------|-----|-------------|---------------|
| drive | 120 | 2.0s | Cut every 2-4 seconds (1-2 bars) |
| steady | 80 | 3.0s | Cut every 5-10 seconds (2-3 bars) |

### Rules

- Place the most impactful visual cut **1-2 frames before** the beat hit (anticipation).
- Align segment transitions to strong beats (beat 1 of a bar).
- Music transition points should align with script segment boundaries.
- For builds/crescendos: accelerate cut frequency as music intensity rises.

---

## 5.3 Volume Levels by Content State

The current pipeline uses flat `volume=0.10` (~-20dB). This should vary:

### Dynamic Volume Table

| Content State | Music Volume | dB Below Voice | Pipeline Value |
|--------------|-------------|----------------|----------------|
| Speech (tutorial/steady) | 8-10% | -20 to -22 dB | 0.08-0.10 |
| Speech (drive/energy) | 12-15% | -16 to -18 dB | 0.12-0.15 |
| Speech (stakes/drama) | 0% | muted (silence) | 0.00 |
| B-roll (no speech) | 30-50% | -6 to -10 dB | 0.30-0.50 |
| Intro/outro (no speech) | 40-60% | -4 to -8 dB | 0.40-0.60 |
| Strategic silence | 0% | muted | 0.00 |

### Industry Standards

- **W3C standard**: -20dB minimum separation between speech and music
- **BBC guideline**: "Viewers never complain about music being too low"
- **YouTube standard**: -14 LUFS integrated loudness target
- **Voice-to-music ratio**: minimum 10dB separation during speech

---

## 5.4 Audio Ducking Timing

Replace flat volume with dynamic ducking keyed to whisper word timestamps.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Duck onset | 200ms BEFORE speech | Use whisper word start timestamps |
| Attack time | 50-100ms | How fast volume drops |
| Duck level | -20 to -22 dB below voice | Depends on mood (see table above) |
| Release onset | 300ms AFTER last word | Wait for natural pause |
| Release time | 400-600ms | Slow fade back up |
| Minimum duck duration | 500ms | Don't duck for single words between music |

### Implementation Priority

Highest-ROI change: dynamic volume by speech state using existing whisper timestamps.
Detect speech segments from word timestamps → duck music during speech → raise during gaps.

---

## 5.5 Silence as a Tool

Strategic silence creates more impact than any music track.

| Scenario | Silence Duration | Technique |
|----------|-----------------|-----------|
| Before major reveal | 0.5-1.5s | Drop music, hold visual, then hit |
| After shocking statement | 1-2s | Let the statement land |
| Natural breathing room | 0.3s micro-pauses | Between topic shifts |
| Maximum silence in YouTube | 3s | Never exceed — viewer assumes buffering |

### When to Use Silence

- Before the single most important statement in a segment
- After a contrarian claim (let cognitive dissonance settle)
- During a visual reveal (let eyes absorb without audio competition)
- Transition from stakes/urgency to calm (relief beat)

### When NOT to Use Silence

- In short-form content (<60s) — no time for silence to register
- During hook sections — momentum must be maintained
- For more than 3 seconds on YouTube — viewers bounce

---

## 5.6 The Emotional Math

Music wins emotionally; speech wins informationally. Default is congruent (matching mood).
Incongruent combinations create specific effects:

| Music | Delivery | Combined Effect |
|-------|----------|----------------|
| drive + drive delivery | High energy | Confident, exciting, uplifting |
| drive + calm delivery | Understated confidence | Authority without hype |
| silence + urgent delivery | Maximum urgency | "This is critical" — voice carries all energy |
| silence + calm delivery | Unease | "Something is wrong" — quiet, unsettling |
| steady + steady delivery | Background calm | Tutorial default — content speaks |
| steady + drive delivery | Rising energy | Building momentum against calm backdrop |

### Rules

- Always **end cuts on drive or steady** (leave viewer on positive/calm note)
- Match music energy to highest-energy moment in the segment, not the average
- If delivery is flat, use music to compensate (higher energy music lifts flat speech)
- If delivery is excellent, music can be lower — don't compete

---

## 5.7 Music Transition Points

| Transition | Music Action |
|-----------|-------------|
| Topic shift | Change instrument layering or introduce new element |
| Energy shift (calm → intense) | Build: add drums, raise volume over 2-4 seconds |
| Energy shift (intense → calm) | Drop: remove layers, lower volume over 4-8 seconds |
| Hook to body | Clear transition — new music cue or beat drop |
| Segment boundary | Align music phrase ending with segment ending |
| Outro | Fade out over last 5-10 seconds |

---

## 5.8 YouTube Creator Music Patterns

| Creator | Pattern |
|---------|---------|
| **MrBeast** | Changes music every 30-60s. Louder mix than most. Music is an active storytelling element. |
| **Veritasium** | Instrument drops signal narrative shifts. Strategic silence at revelations. |
| **MKBHD** | Music barely perceptible during speech. Louder during B-roll. Clean, minimal. |
| **Ali Abdaal** | Consistent background music, smooth transitions. Music reinforces editing style. |

---

## 5.9 Intro/Outro Music Patterns

### Intro (First 30s)
- Music enters at full energy from frame 1 (or with a 1-2s build)
- Ducks immediately when speech starts
- Sets the emotional context before words do

### Outro (Last 30s)
- Music rises as speech concludes
- Peak energy at the CTA moment
- Fade or clean cut at the very end (no trailing audio)
- For videos linking to next video: music bridges the end-screen

### Between Segments
- Brief music swell (1-2s) at segment boundaries
- Volume bump during transitions/B-roll between topics
- Return to ducked level when speech resumes
