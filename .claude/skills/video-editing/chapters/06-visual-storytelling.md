# Chapter 6: Visual Storytelling

B-roll timing, graphics, text overlays, transitions, screen recording editing, and the
visual rhythm that keeps viewers engaged.

---

## 6.1 B-Roll Selection and Timing

### When to Cut Away from Speaker

- Right after a key phrase (visually reinforce what was said)
- During pauses or breaths in speech (break monotony)
- To cover jump cuts or stumbles
- At emotional peaks to intensify with visuals
- As lead-in or transition between topics

### Duration Rules

| Content Pace | B-Roll Insert Duration |
|-------------|----------------------|
| Fast-paced / short-form | 2-4 seconds |
| Standard YouTube | 3-7 seconds |
| Slow / contemplative | 5-10 seconds |

### What to Show

- Visuals that directly illustrate the spoken point
- Product/tool being discussed
- Screen recording of the action described
- Reaction shots or close-ups of relevant details
- Return to speaker face within 5-8 seconds (eye-tracking: faces dominate gaze)

---

## 6.2 Lower-Third Graphics

### Timing

- Appear when a new speaker, location, or concept is introduced
- Timed to the exact second the speaker begins talking about the subject
- Duration: **4-6 seconds** (range: 3-7 seconds)
- Formula: time to read the text **twice**

### Design Rules

- Lower third of the frame (bottom 1/3)
- Left-aligned, 10% margin from edges
- Semi-transparent background bar for readability
- Max 2 lines: Name (bold) + Title/Context (regular)
- Smooth animate-in / animate-out (no abrupt pop)
- Consistent style across all videos for brand recognition

---

## 6.3 Text Overlay Hierarchy

### Font Sizes at 1080p

| Element | Size | Weight |
|---------|------|--------|
| Headlines/Titles | 80-120px | Bold |
| Stats/callouts | 60-80px | Bold, high contrast |
| Supporting text | 40-60px | Regular |
| Mobile minimum | 24px | — |

### Display Duration Rules

| Content | Duration |
|---------|----------|
| Single word/number | 1.5-2 seconds |
| Short phrase (2-5 words) | 2-3 seconds |
| Full sentence (6-12 words) | 4-6 seconds |
| Two-line subtitle | 6 seconds |
| Stats/data point | 3-5 seconds |
| Complex graphic/chart | 6-10 seconds |

### Formulas

- **Character-based**: duration = character_count / 17 (seconds, adults)
- **Word-based**: duration = word_count / 2.5 (seconds, accounting for video context)
- **Minimum display**: never less than 0.8 seconds
- **Buffer**: add 0.5 seconds after dialogue ends before removing text

### Placement

- Headlines: upper third or center
- Supporting text: lower third
- Stats/callouts: center or upper third with background box
- Max 30 characters per line, max 3 lines
- Sans-serif fonts only (Inter, Roboto, Montserrat, DejaVu Sans)

---

## 6.4 Transition Types

Hard cuts should be **90%+ of all transitions**. Every other transition is a deliberate
storytelling choice.

| Transition | When to Use | Rules |
|-----------|------------|-------|
| **Hard cut** | Default. Dialogue, urgency, surprise | 30-degree angle rule between shots |
| **Dissolve** | Time passing, montage, reflective | Never dissolve moving-to-static. Overuse cheapens. |
| **L-cut** | Continuity, reaction shots | Audio trails by 0.5-2.0s |
| **J-cut** | Anticipation, scene change | Audio leads by 0.5-1.5s |
| **Whip pan** | High energy, fast scene change | Match direction in both clips |
| **Fade to black** | End of major section, finality | Sparingly; signals hard chapter break |

---

## 6.5 Screen Recording / Demo Editing

### Zoom to Cursor

- Auto-zoom triggers on 2+ clicks within 3 seconds
- Zoom follows cursor while clicks continue
- Smooth ease-in/ease-out (avoid jerky)
- Zoom to 150-200% on click areas for clarity

### Highlight Techniques

- Concentric circle animation on each click
- Color spotlight on click location
- Numbered callouts for step sequences
- Callout boxes: appear 0.5s before action, disappear 1-2s after

### Layout Alternation

- Alternate between fullscreen demo, split-screen (demo + face), and face-only
- Change layout every 15-30 seconds to maintain variety
- Webcam PIP: 15-25% of frame area, bottom-right corner
- Circle or rounded rectangle shape for PIP webcam

---

## 6.6 Ken Burns / Zoom Effects

### When to Zoom In

| Scenario | Zoom Speed | Zoom Factor | Duration |
|----------|-----------|-------------|----------|
| Key statement emphasis | Slow dramatic | 110-130% | 5-10s |
| Humor / punchline | Fast | 150-200% | 0.3-0.8s |
| Detail emphasis | Medium | 130-150% | 2-5s |
| Still image engagement | Slow pan+zoom | 110-120% | 5-10s |

### Zoom Targets

- Face/eyes → emotional emphasis
- Hands/product → detail emphasis
- Text/screen → readability
- Environment → establishing context

### Rules

- Vary direction: if zoom-in on one shot, zoom-out or pan on next
- Each shot: max 5 seconds before a cut or zoom change
- Burst sequences: 5-10 quick cuts every 2-3 minutes, then calm
- Fast zoom on punchlines = MrBeast signature technique

---

## 6.7 Visual Pacing: The Visual Metronome

Alternate visual types in a rhythm: Speaker → B-roll → Graphic → Speaker → Demo → Speaker.
Never stay on one visual type too long.

### Change Frequency by Content

| Content Type | Change Interval |
|-------------|----------------|
| YouTube Shorts / Reels | Every 2-4 seconds |
| Fast-paced YouTube (MrBeast) | Every 3-5 seconds |
| Standard talking head | Every 15-25 seconds |
| Educational / tutorial | Every 20-40 seconds |

### The Oscillation Principle

Alternate calm segments with punchy cut clusters. This mimics natural conversation rhythm:

1. **First 8 seconds**: Hook — tightest pacing, high-value visuals
2. **First 30 seconds**: Fast pacing, frequent visual changes
3. **Every 1-2 minutes**: Reset attention with pacing shift
4. **Every 2-3 minutes**: Burst sequence (5-10 quick cuts), then return to calm

---

## 6.8 Branded Intro/Outro

### Intro Rules

- **1-3 seconds** for branded sting (logo + jingle)
- Under 2 seconds is ideal for retention
- NEVER exceed 10 seconds total including hook
- Hook BEFORE branded sting, not after
- Skip intro entirely for videos under 4 minutes

### Outro Rules

- **8-10 seconds** for CTA + end screen
- YouTube end-screen requires minimum 5 seconds, max 20
- Don't be overly promotional — light branding only
- Set up the problem viewers still have → point to next video
- Retention benchmark: 70-80% when properly teeing up next video

### Pipeline Integration

- `branding.intro_16x9` / `branding.intro_9x16` — pre-rendered templates
- Current pipeline: 1.2s cylinder intro, 1s lid outro
- Concat with stream copy (templates pre-cropped to match resolution)
- Skip for hook clips (`is_hook: true`)

---

## 6.9 Split Screen and Picture-in-Picture

### When to Use

| Format | Use Case |
|--------|---------|
| **Split screen** | Before/after, simultaneous reactions, cause-and-effect |
| **PIP** | Screen recording + face, reference while discussing |

### Sizing

| Layout | Main | Secondary |
|--------|------|-----------|
| Split 50/50 | Equal weight | Equal weight |
| Split 70/30 | Primary content | Context/reference |
| PIP webcam | Full screen | 15-25% of frame, corner |
| PIP reference | Full screen | 25-35% of frame |

### Rules

- PIP position: bottom-right (default), leave 5-10% margin from edges
- Don't hold same layout > 30-60 seconds — alternate
- Animate layout changes: scale + position ease, 0.3-0.5s
- Avoid obscuring subtitles, UI elements, or faces

---

## 6.10 Quick Reference: Numbers for Implementation

| Parameter | Value |
|-----------|-------|
| B-roll insert duration | 3-7 seconds |
| Lower third duration | 4-6 seconds |
| Branded intro (sting) | 1-3 seconds |
| Branded outro | 8-10 seconds |
| Text reading speed | 17 chars/sec or ~2.5 words/sec |
| Min text display | 0.8 seconds |
| Two-line text display | 6 seconds |
| Visual change (long-form) | Every 15-25 seconds |
| Visual change (short-form) | Every 2-4 seconds |
| Burst sequence interval | Every 2-3 minutes |
| PIP webcam size | 15-25% of frame |
| Headline font (1080p) | 80-120px |
| Body font (1080p) | 40-60px min |
| Fast zoom duration | 0.3-0.8 seconds |
| Slow zoom duration | 5-10 seconds |
| Hard cuts % of transitions | 90%+ |
| Max chars per text line | 30 |
| Max simultaneous text lines | 3 |
