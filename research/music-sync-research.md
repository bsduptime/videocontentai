# Music & Mood Sync Research for AI Video Editing Agent

Research compiled 2026-03-18. Actionable rules for the three mood categories: **drive** (confident/upbeat), **tension** (urgent/dramatic), **steady** (calm/background).

---

## 1. Syncing Cuts to Beat Drops

**Core technique:** Place video cuts on musical downbeats (the "1" of each bar), not on every single beat. Cutting on every beat feels frantic and amateur.

**Implementable rules:**
- Mark strong downbeats (bar boundaries) as primary cut points
- Mark weak beats (2, 3, 4) as secondary cut points for fast-paced sections only
- For beat drops (big energy changes in the track): place the most visually impactful shot change 1-2 frames BEFORE the beat hit, not after — the brain anticipates
- During build-ups (pre-drop), accelerate cut frequency: start at 1 cut/bar, move to 1 cut/beat, then 1 cut/half-beat
- After a drop, hold a single powerful shot for 2-4 beats before resuming cuts

**For our moods:**
- **drive**: Cut on every 2nd or 4th beat (half-bar to full-bar intervals)
- **tension**: Cut on beats during rising sections, hold shots during stingers
- **steady**: Cut on bar boundaries only (every 4 beats) — minimal sync needed

**Source:** [Vegas Creative Software — Cut to the Beat](https://www.vegascreativesoftware.com/us/post-production/how-to-edit-video-footage-to-the-beats-of-music/), [Toolfarm — Edit to the Beat](https://www.toolfarm.com/tutorial/edit-to-the-beat/), [Beat2Cut Guide](https://beat2cut.com/blog/beat-sync-video-editing-complete-guide/)

---

## 2. Music Energy Matching vs. Contrast

**Matching (congruent):** Music energy matches speaker/visual energy. This is the default — it reinforces what the viewer already feels. Use 80% of the time.

**Contrast (contrapuntal/anempathetic):** Music energy opposes the visual mood. This is a deliberate artistic choice for irony, unease, or emphasis. Use sparingly (max 20% of content).

**Implementable rules:**

| Speaker delivery | Music mood | Emotional result | When to use |
|-----------------|------------|-----------------|-------------|
| High energy, fast | **drive** | Amplified excitement | Product reveals, wins, successes |
| High energy, fast | **steady** | Grounding, authority | Expert making complex seem easy |
| High energy, fast | **tension** | Chaos, urgency | Breaking news, critical warnings |
| Calm, measured | **drive** | Optimism despite calm delivery | Vision statements, future plans |
| Calm, measured | **steady** | Trust, credibility | Tutorials, how-tos, explanations |
| Calm, measured | **tension** | Something's wrong, unease | Exposing problems, investigations |
| Emotional, vulnerable | **steady** | Intimacy, sincerity | Personal stories, reflections |
| Emotional, vulnerable | **tension** | Dramatic weight | Challenges, struggles, stakes |
| Emotional, vulnerable | **drive** | Overcoming, triumph | Comeback stories (use at resolution) |

**Contrast rule:** When the speaker's words say one thing but the music says another, the viewer trusts the MUSIC's emotional signal. Use contrast only when you want the viewer to feel something the speaker isn't explicitly saying.

**Source:** [Pond5 — 7 Ways Music Creates Mood Onscreen](https://blog.pond5.com/12233-7-ways-to-use-music-to-create-mood-and-meaning-onscreen/), [TV Tropes — Soundtrack Dissonance](https://tvtropes.org/pmwiki/pmwiki.php/Main/SoundtrackDissonance), [Artyfile — How Music Shapes Emotions](https://artyfile.com/blog/the-science-behind-the-magic-how-music-shapes-emotions)

---

## 3. Audio Ducking Timing

**Current state:** The pipeline uses a flat `volume=0.10` for music. This section defines rules for dynamic ducking.

### Target dB levels (speech-relative)

| Content state | Music level relative to speech | Absolute music target |
|--------------|-------------------------------|----------------------|
| Speech active | -20 dB to -24 dB below speech | -38 to -42 dB RMS |
| Speech pause (< 2s) | -12 dB below speech level | -30 dB RMS |
| No speech (> 2s) | -6 dB below speech level | -24 dB RMS |
| Intro/outro (no speech) | 0 dB (full level) | -18 dB RMS |

### Ducking timing parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Duck-down attack** | 50-100ms | How fast music drops when speech starts |
| **Duck-down hold** | 200ms | Pre-roll: start ducking 200ms BEFORE speech onset |
| **Duck-up release** | 400-600ms | How fast music returns after speech ends |
| **Duck-up delay** | 300ms | Wait after last word before starting release |
| **Minimum duck duration** | 500ms | Don't duck for isolated words shorter than this |

### Implementation approach for FFmpeg
Instead of flat volume, use the `sidechaincompress` filter keyed to speech:
```
[speech]asplit[sc][speech_out];
[music][sc]sidechaincompress=threshold=0.01:ratio=6:attack=50:release=500[ducked_music];
[speech_out][ducked_music]amix=inputs=2:duration=first[aout]
```

Or for simpler per-segment control: analyze word timestamps from Whisper, generate volume automation keyframes, apply with FFmpeg `volume` filter using `enable='between(t,start,end)'`.

**Source:** [Audacity Auto Duck Manual](https://manual.audacityteam.org/man/auto_duck.html), [Boris FX — Audio Ducking](https://borisfx.com/blog/what-is-audio-ducking-and-how-is-it-used/), [Adobe — Auto Ducking in Premiere](https://helpx.adobe.com/premiere-pro/using/auto-ducking.html)

---

## 4. Silence as an Editing Tool

**Key insight:** Intentional silence is NOT dead air. Strategic silence before a key point increases its perceived importance by 2-3x (the "Veritasium pause").

### When to drop music entirely

| Moment type | Silence duration | Effect |
|-------------|-----------------|--------|
| Before a major reveal | 0.5-1.5s | Builds anticipation |
| After a shocking statement | 1.0-2.0s | Lets it land |
| Emotional vulnerability | 2-5s | Creates intimacy |
| Before the hook punchline | 0.3-0.8s | Maximizes impact |
| Topic transition (palette cleanser) | 0.5-1.0s | Resets attention |

### Rules for the AI agent
- Keep natural micro-pauses of 0.3s for breathing room between sentences — do NOT remove these
- Remove dead air > 1.0s UNLESS it follows a high-scoring emotional/contrarian segment (score >= 7)
- When a segment is tagged `emotional` or `contrarian`, insert 0.5s silence before and after
- For hook clips: drop music 0.5s before the punchline moment, resume 1s after
- Never have silence longer than 3s in YouTube content (viewers leave)

**Source:** [AIR Media-Tech — Advanced Retention Editing](https://air.io/en/youtube-hacks/advanced-retention-editing-cutting-patterns-that-keep-viewers-past-minute-8), [Wisecut — Jump Cuts and Silence Removal](https://www.wisecut.ai/post/why-and-how-youtubers-use-jump-cuts-and-remove-silence-in-videos)

---

## 5. Music Transition Points

### When to change music track or energy level

| Transition trigger | Action | Technique |
|-------------------|--------|-----------|
| Topic shift (detected from transcript) | Crossfade to new track | 2-3s crossfade between tracks |
| Emotional turn (e.g., problem → solution) | Change mood category | J-cut: new music starts 1s before visual transition |
| Segment boundary (intro → main content) | Energy shift | Fade out intro music over 1.5s, 0.5s silence, fade in main music |
| Build to climax | Increase energy within same mood | Layer in percussion/bass, or switch to higher-energy variant |
| Resolution/conclusion | Decrease energy | Remove layers or switch to calmer variant |
| Screen recording → talking head | Subtle shift | Drop music 2-3 dB during dense screen content, restore for talking head |

### Crossfade rules
- **Crossfade duration:** 1.5-3.0s (shorter = more energetic, longer = smoother)
- **Never** hard-cut between two different music tracks (sounds like an error)
- **J-cut audio:** Start new music 0.5-1.0s before the visual cut for smoother transitions
- **L-cut audio:** Let outgoing music tail 0.5-1.0s into new section for continuity

### FFmpeg crossfade between music segments
```
[music1]afade=t=out:st={end-2}:d=2[m1];
[music2]afade=t=in:d=2,adelay={start_ms}|{start_ms}[m2];
[m1][m2]amix=inputs=2:duration=longest[music_out]
```

**Source:** [Epidemic Sound — Transition Between Songs](https://www.epidemicsound.com/blog/how-to-transition-between-songs-in-your-video-with-adobe/), [Pro Sound Effects — Audio Editing Transitions](https://blog.prosoundeffects.com/how-to-elevate-scene-transitions-with-audio-editing), [ProTunes — Seamless Audio Transitions](https://protunesone.com/blog/how-to-create-a-seamless-audio-transition-in-your-video-edits/)

---

## 6. The Emotional Math

### Mood + Delivery = Viewer Emotion

Music operates through the amygdala (emotional processing) while speech operates through the prefrontal cortex (rational processing). When they conflict, music wins emotionally but speech wins informationally. This creates specific combinations:

**Drive mood (major key, 110-130 BPM, upbeat)**
- + confident delivery = "I trust this person, they know what they're doing"
- + excited delivery = "This is genuinely exciting, I should pay attention"
- + calm delivery = "There's positive energy under the surface, something good is coming"
- + vulnerable delivery = "They're overcoming something" (use at story resolution only)

**Tension mood (minor key, 90-120 BPM, dramatic)**
- + confident delivery = "This is serious but under control"
- + excited delivery = "Something critical is happening RIGHT NOW"
- + calm delivery = "Something is deeply wrong" (most unsettling combination)
- + vulnerable delivery = "The stakes are real and personal"

**Steady mood (neutral key, 80-100 BPM, ambient)**
- + confident delivery = "Competent, professional, trustworthy"
- + excited delivery = "Grounded enthusiasm" (good for tutorials showing results)
- + calm delivery = "Safe learning environment" (default for tutorials)
- + vulnerable delivery = "Intimate, authentic" (personal stories)

### Key rule for the AI agent
- The **default** should be congruent (matching) music
- Use contrast ONLY when a segment is tagged `contrarian` or when transitioning from problem → solution (tension during problem, drive at the solution)
- Minor key + calm speaker = maximum unease. Use for "here's what most people get wrong" sections
- Major key at segment resolution = satisfaction. Always end the last segment of a cut on drive or steady, never tension

**Source:** [Film Independent — Psychology of Film Music](https://www.filmindependent.org/blog/know-score-psychology-film-music/), [Educational Voice — Music Scoring Emotional Impact](https://educationalvoice.co.uk/the-role-of-music-scoring/), [Frontiers in Psychology — Soundtracks Shape What We See](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.02242/full)

---

## 7. BPM and Pacing

### BPM ranges per mood

| Mood | BPM range | Cut frequency (avg shot length) |
|------|-----------|-------------------------------|
| **drive** | 110-130 BPM | 3-5s per shot |
| **tension** | 90-120 BPM | 2-4s per shot (faster during builds) |
| **steady** | 80-100 BPM | 5-10s per shot |

### The BPM-to-cut-frequency relationship

**It's not linear.** The relationship is:
- **Cuts on beat boundaries** are what create the sync feeling, not raw cut speed
- At 120 BPM, one beat = 0.5s. Cutting every beat = 0.5s shots (too fast for YouTube talking head)
- Practical rule: **cut every 2-8 beats** depending on content type

| Content type | Cuts per bar (4 beats) | Approx ASL at 120 BPM |
|-------------|----------------------|----------------------|
| High energy montage | 2-4 cuts/bar | 0.5-1.0s |
| Action/reveal | 1 cut/bar | 2.0s |
| Standard talking head | 1 cut/2 bars | 4.0s |
| Tutorial/explanation | 1 cut/4 bars | 8.0s |
| Screen recording | 0 cuts (hold) | 10-30s |

### Neuroscience note
Humans naturally sync to rhythms between 100-130 BPM (resting heart rate during mild exertion). Music in this range creates unconscious body engagement without requiring attention.

**For the agent:** When selecting mood, consider the average segment length in the cut plan. Short segments (< 3s average) pair with drive. Long segments (> 6s average) pair with steady. Mixed lengths pair with tension (which has natural builds and drops).

**Source:** [Artlist — How to Choose BPM for Video](https://artlist.io/blog/music-bpm/), [Silverman Sound — BPM to FPS Calculator](https://www.silvermansound.com/bpm-to-fps-calculator), [Scruffycity — Music and Montage](https://scruffycityfilmfest.com/music-and-montage-how-rhythm-controls-the-cut-in-film)

---

## 8. Music in YouTube Specifically

### MrBeast patterns
- **Frequent music changes** — music track changes every 30-60s to maintain energy progression
- Music is always present (never silent except for brief dramatic pauses)
- Heavy use of **sound effect stingers** (whooshes, hits, rises) to bridge music transitions
- Music builds to each "reveal moment" then drops to let the reaction breathe
- Background music is LOUD compared to most creators — closer to -15 dB under speech than -20 dB

### Veritasium patterns
- **Custom scoring** — music written to match the emotional arc of each specific video
- Music provides "emotional context to otherwise cerebral content without distracting from learning"
- Uses **instrument drops** — removing and re-introducing instruments signals narrative shifts (e.g., dramatic story → factual explanation)
- Music disappears entirely during key revelations (strategic silence)
- Much quieter background music than MrBeast — prioritizes speech clarity

### MKBHD patterns
- **Lo-fi/electronic** consistent aesthetic — music reinforces the "clean, premium" brand
- Music is notably quiet — barely perceptible during speech, serves as texture not emotion
- Uses Epidemic Sound library — consistent sonic palette across videos
- Music comes forward during B-roll product shots, ducks hard for talking head
- Outro music is distinctly louder and more present (signaling "video ending")

### Common patterns across top YouTube creators
1. **First 5-15s:** Music at higher energy to hook, then duck under speech
2. **B-roll segments:** Music volume increases 3-6 dB (becomes the star)
3. **Talking head:** Music at minimum level or absent
4. **Transitions:** Brief music swell (0.5-1s) to bridge sections
5. **Last 30s:** Music energy increases, signaling conclusion
6. **End screen:** Music is primary audio, no speech competition

**Source:** [VideoHero — Learn from MrBeast](https://www.videohero.com/blog/MrBeast-and-video-editing), [Jonny Hyman — Veritasium Scores](https://jonnyhyman.com/projects/music/veritasiums), [Epidemic Sound — Best of MKBHD](https://www.epidemicsound.com/music/themes/creators-picks/best-of-mkbhd/), [Daniel Scrivner — MrBeast Production Handbook](https://www.danielscrivner.com/how-to-succeed-in-mrbeast-production-summary/)

---

## 9. Intro/Outro Music Patterns

### Intro (first 15-30 seconds)

| Time | Music state | Purpose |
|------|------------|---------|
| 0-3s | Full energy, hook-level | Grab attention immediately |
| 3-5s | Sustain or slight dip | Let branded intro animation play |
| 5-10s | Duck under speech | Speaker begins hook statement |
| 10-15s | Minimal/ducked | Hook content — speech dominates |
| 15-30s | Gradual fade to working level | Transition to main content |

**Rule:** The intro music should NEVER be the same energy level as the body music. It should be noticeably higher energy in the first 3-5s, then settle.

### Outro (last 30 seconds)

| Time (from end) | Music state | Purpose |
|-----------------|------------|---------|
| -30s | Begin gradual volume increase | Signal approaching end |
| -20s | Music at 2x normal volume | Emotional resolution |
| -10s | Music dominant, speech wrapping | Call to action over music |
| -5s | Music only | End screen, subscribe prompt |
| -2s | Fade out OR hard end on beat | Clean button ending |

**Two ending styles:**
1. **Fade out** (3-5s) — for steady/calm content, tutorials
2. **Hard stop on downbeat** — for drive/tension content, more professional feel

**Rule:** Always end on a musically resolved moment (not mid-phrase). Either fade out gradually or cut on a bar boundary.

**Source:** [Epidemic Sound — Intros & Outros](https://www.epidemicsound.com/music/themes/storytelling-techniques/intros-outros/), [Storyblocks — Intro and Outro Music](https://www.storyblocks.com/resources/blog/youtube-intros-outros)

---

## 10. Background Music Volume Levels

### Industry standards (specific numbers)

| Standard/Platform | Target overall loudness |
|-------------------|------------------------|
| YouTube | -14 LUFS (auto-normalized) |
| Apple Podcasts | -16 LUFS |
| Spotify | -14 LUFS |
| Broadcast TV (EBU R128) | -23 LUFS |
| Our pipeline (current) | -16 LUFS (good choice) |

### Speech-to-music ratio

| Source/Standard | Music level below speech |
|----------------|------------------------|
| **W3C accessibility (WCAG)** | At least -20 dB below speech |
| **BBC guideline** | -18 to -24 dB below speech |
| **Pro podcast mixing** | -20 to -22 dB below speech |
| **YouTube talking head** | -18 to -24 dB below speech |
| **YouTube high-energy** | -12 to -18 dB below speech |
| **B-roll only (no speech)** | -6 to -12 dB below overall target |

### Translating to our pipeline's volume parameter

Current: `volume=0.10` (10% amplitude = approximately -20 dB). This is correct for steady/tutorial content.

| Content context | volume parameter | Approx dB below speech |
|----------------|-----------------|----------------------|
| Tutorial with speech (steady) | 0.08-0.12 | -22 to -18 dB |
| Talking head with speech (drive) | 0.10-0.15 | -20 to -16 dB |
| Energetic/MrBeast style (drive) | 0.15-0.20 | -16 to -14 dB |
| B-roll segment (no speech) | 0.30-0.50 | -10 to -6 dB |
| Intro (first 3s, no speech) | 0.40-0.60 | -8 to -4 dB |
| Outro (last 5s, no speech) | 0.40-0.60 | -8 to -4 dB |
| Dramatic pause (tension) | 0.20-0.30 | -14 to -10 dB |

### The BBC rule
"Viewers never complain about background music being 'too low,' but will quickly criticize when music is too loud." When in doubt, go quieter.

**Source:** [Kevin Muldoon — Audio Levels for YouTube](https://www.kevinmuldoon.com/audio-levels-youtube/), [W3C WCAG — G56 Technique](https://www.w3.org/WAI/WCAG22/Techniques/general/G56.html), [Gearspace — Mixing Background Music](https://gearspace.com/board/post-production-forum/1431800-tips-mixing-background-music-youtube-podcast.html), [Pure Audio Insight — Background Music Volume](https://pureaudioinsight.com/blogs/content-production/background-music-volume-how-loud-should-it-be)

---

## Implementation Priority for the Pipeline

Based on current state (flat `volume=0.10` mix) and impact, here's the recommended order:

1. **Dynamic volume by content state** — Different volume for speech vs. no-speech segments using Whisper word timestamps. Highest ROI change.
2. **Mood-specific volume defaults** — drive louder (0.12), tension moderate (0.10), steady quieter (0.08).
3. **Intro/outro music boost** — First 3s and last 5s at higher volume when no speech is present.
4. **Audio ducking with sidechaincompress** — Replace flat volume with dynamic ducking keyed to speech detection.
5. **Strategic silence insertion** — Drop music before high-scoring emotional/contrarian segments.
6. **Beat-aligned cutting** — Analyze music BPM, adjust segment boundaries by +/- 0.5s to land on beats.
7. **Music transitions** — Crossfade between mood variants at major topic shifts within a single cut.
