# Chapter 2: Hook Extraction

The agent has transcription and frame extraction. This chapter teaches WHAT to look for
when identifying hooks, how to score them, and how to write overlay text that complements
the spoken hook.

---

## 2.1 What Makes a Great Hook

You have 5-10 seconds for long-form, 1-3 seconds for short-form. Over 33% of viewers drop
in the first 30 seconds if the hook fails.

### The First 30 Seconds Structure

| Timestamp | Function |
|-----------|----------|
| 0:00-0:05 | Attention grab (shock, tease, question, or clip) |
| 0:05-0:15 | Clarify promise (what this video will deliver) |
| 0:15-0:30 | Establish stakes, context, or start journey |

### MrBeast Hook Rules (Leaked Production Doc)

1. Deliver the core premise in 3-8 seconds. No preamble, no "hey guys", no logos.
2. The first minute must prove the thumbnail's promise.
3. Structure: Hook → Story → No dull moments → Satisfying payoff → Abrupt ending.
4. The "Wow Factor": within 30 seconds, show something visually impressive.
5. Minutes 1-3 require "crazy progression" — compress multiple events.
6. Three-minute re-engagement: something so impressive it re-hooks drifters.

---

## 2.2 Seven Hook Templates

Classify candidate segments against these templates. A segment matching multiple templates
scores higher.

### A) Question Hook
- **Pattern**: Opens with a direct question the audience cares about
- **Transcript signal**: Sentence ending in "?" or "Have you ever...", "What if...", "Why does..."
- **Why it works**: Brain naturally wants to close the loop
- **Best for**: Long-form educational content

### B) Stat/Number Hook
- **Pattern**: Opens with a shocking or counterintuitive statistic
- **Transcript signal**: Number/percentage + surprise context ("only", "actually", "most people don't know")
- **Why it works**: Impossible-sounding numbers make people freeze
- **Best for**: LinkedIn, educational YouTube

### C) Story Hook (Cold Open)
- **Pattern**: Drops viewer into the middle of a moment — no preamble
- **Transcript signal**: Past tense narrative, sensory details, "So there I was...", "Last Tuesday..."
- **Why it works**: Personal and raw, like overhearing a conversation
- **Best for**: Founder brand, personal content

### D) Demonstration Hook
- **Pattern**: Shows the result/action immediately, then explains
- **Transcript signal**: Often minimal speech — relies on visual spectacle
- **Audio signal**: Reaction sounds, gasps, sudden audio events
- **Best for**: Screen recordings, tutorials, before/after demos

### E) Transformation Hook
- **Pattern**: Flash the "after" state first, then reveal the "before"
- **Transcript signal**: "From X to Y", "went from...", time-bound results
- **Why it works**: Viewer instantly wonders "How did they get there?"
- **Best for**: Case studies, tutorials, benchmarks

### F) Contrarian/Challenge Hook
- **Pattern**: Opens by contradicting common belief
- **Transcript signal**: "Everyone thinks...", "The biggest mistake...", "Stop doing...", "X is actually wrong"
- **Why it works**: Creates cognitive dissonance, forces re-evaluation
- **Best for**: Hot takes, opinion content, thought leadership

### G) Urgency/FOMO Hook
- **Pattern**: Creates time pressure or exclusivity
- **Transcript signal**: "Before it's too late", "right now", "just discovered", "they don't want you to know"
- **Why it works**: Loss aversion is stronger than gain motivation
- **Best for**: News, trend content, product launches

### Template Selection by Platform

| Platform | Best templates |
|----------|---------------|
| YouTube long-form | A (Question), B (Stat), E (Transformation), F (Contrarian) |
| YouTube Shorts | D (Demonstration), G (Urgency), E (Transformation) |
| TikTok | D (Demonstration), G (Urgency), C (Story) |
| Instagram Reels | D (Demonstration), C (Story), E (Transformation) |
| LinkedIn | B (Stat), F (Contrarian), E (Transformation) |

---

## 2.3 Hook Scoring Rubric

Five-factor scoring system. Each factor scored 0-20, total out of 100.

| Factor | Points | How to Evaluate |
|--------|--------|-----------------|
| **Attention grab** | 0-20 | Does the first 5s force stop-scroll? Strong opening statement? |
| **Curiosity loop** | 0-20 | Reason to keep watching? Unanswered question, teased outcome? |
| **Value promise** | 0-20 | Does viewer understand what they'll get from watching? |
| **Pacing** | 0-20 | Delivery speed appropriate? 2.5-3.5 words/sec? No dead air? |
| **Title match** | 0-20 | Does hook deliver on the promise of the title/topic? |

### Grading Scale

| Score | Grade | Action |
|-------|-------|--------|
| 80-100 | Excellent | Ship it |
| 60-79 | Acceptable | Minor adjustments |
| 40-59 | Weak | Rework the hook |
| <40 | Failed | Rewrite completely |

### PVSS Framework (Alternative)

**P**romise (what they'll get) → **V**alidation (why trust you) → **S**tructure (how it's
organized) → **S**takes (what they'll miss). Apply when the hook needs both information and
credibility.

---

## 2.4 Audio Energy Detection

Three measurable audio signals that indicate hook-worthy moments in raw footage:

### A) RMS Energy Peaks
- Segments where RMS exceeds the mean by >1.5 standard deviations
- Correspond to moments of emphasis, excitement, or raised voice

### B) Pitch (F0) Variation
- Excitement correlates with: higher mean F0, wider F0 range, rising intonation
- A segment where F0 mean is >20% above the speaker's baseline = heightened energy

### C) Speaking Rate Acceleration
- Segments where words-per-second increases >20% above baseline = enthusiasm
- Combined with RMS peak = strong hook indicator

### Composite Energy Score

```
energy_score = (rms_z_score * 0.4) + (f0_deviation * 0.3) + (rate_deviation * 0.3)
```

Segments scoring >1.5 are hook candidates. Cross-reference with transcript pattern matching.

---

## 2.5 Hook Extraction from Long-Form

### Transcript Pattern Matching (Ranked by Hook Strength)

1. **Statistics/numbers**: "75% of...", "I made $X in Y days"
2. **Contrarian statements**: "Everyone thinks X, but actually..."
3. **Strong declaratives**: "This changed everything", "Here's what nobody tells you"
4. **Story openings**: "So there I was...", "Last week something happened..."
5. **Questions**: "Have you ever wondered...", "What if I told you..."
6. **Transformation markers**: "Before/after", "went from X to Y"

### Extraction Scoring Formula

```
hook_score = (pattern_match_strength * 0.4)
           + (audio_energy_score * 0.3)
           + (not_in_first_60s * 0.1)
           + (standalone_comprehensibility * 0.2)
```

Take top 3-5 candidates. Select the one with highest combined score that is self-contained
(understandable without prior context).

### Cold Open Rules

- Extract 7-15 seconds for long-form hooks
- 2-3 clips max in a montage, total under 20 seconds
- Must leave something unresolved that the main video answers
- Must start on a clean cut point (scene change or sentence boundary)
- Must NOT start with setup — start with the strongest statement

---

## 2.6 Text Overlay on Hooks

60%+ of mobile viewers watch with sound off — text must convey the hook independently.

### What to Show
- **Keyword emphasis**: Animate only the 1-3 words that carry meaning
- Do NOT duplicate the full spoken sentence — complement it
- Show what reinforces the hook: the stat, the claim, the question

### Timing
- Text appears synchronized with spoken word or 0.1-0.3s before (creates anticipation)
- Hold time: minimum 1.5 seconds per text element
- Character-based: duration = character_count / 17 seconds

### Placement
- Lower third for captions/subtitles
- Upper third or center for hook statements and key phrases
- Leave 10% margins on all sides for platform UI elements
- Avoid center-frame if there is a face

### Style
- Bold, high-contrast (white with black outline or dark background strip)
- Font size: minimum ~5% of frame height (48px+ at 1080p)
- Animate by phrase, not word-by-word (except emphasis on one key word)
- Color-highlight the single most important word in each phrase

### AI Implementation

From the hook transcript, extract the 1-3 highest-signal words per sentence (numbers,
superlatives, action verbs, proper nouns). Time overlay start to word onset timestamp
minus 100ms. Hold for max(1.5s, word_duration + 0.5s).

---

## 2.7 Short-Form vs. Long-Form Hooks

| Dimension | Short-form (Shorts/Reels/TikTok) | Long-form (YouTube) |
|-----------|----------------------------------|---------------------|
| Hook window | 1-3 seconds | 5-10 seconds |
| What decides fate | Scroll-or-stay in first frame | Click-through, then 30s retention |
| Hook style | Pattern interrupt, visual shock, text | Curiosity gap, premise, value promise |
| Text dependency | Essential (60%+ watch muted) | Helpful but audio-primary |
| Retention benchmark | 65%+ 3s hold = 4-7x impressions | 70%+ at 30s = strong |

**Short-form rule**: The hook must be comprehensible and compelling within 3 seconds. Prefer
visual/action moments over setup-heavy verbal hooks. Always include text overlay.

**Each short-form output needs its own hook** — independent of the long-form intro. The same
source moment may need different hooks for different platforms.
