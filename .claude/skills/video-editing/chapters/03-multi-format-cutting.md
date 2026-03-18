# Chapter 3: Multi-Format Cutting

One recording → long-form + shorts + reels + clips. This chapter covers extraction strategy,
aspect ratio cropping, platform safe zones, and format-specific adaptation.

---

## 3.1 Extraction Pipeline

Target: **8-12 short clips per hour of source content**.

1. Transcribe with word-level timestamps
2. Score each segment: hook_potential, information_density, emotional_resonance, standalone_score
3. Tag segments: strong_hook, high_density, emotional, funny, contrarian, technical, story, filler
4. Select best segments per output format (different lengths per platform)
5. Generate independent hook for each short-form output
6. Apply platform-specific safe zones for all text/graphics

### Standalone Score

Penalize segments that:
- Reference prior content (pronouns without antecedents: "this", "that thing")
- Start mid-explanation
- Require visual context not in the clip

Prefer segments that re-state their premise. Target `standalone_score >= 7` for extraction.

### Making Context-Dependent Clips Standalone

- Add 2-3 second text intro card providing context
- Use caption/subtitle to clarify references
- Trim to start from the re-statement (speakers often summarize)
- Add CTA to full video for viewers wanting more context

---

## 3.2 Aspect Ratio Cropping: 16:9 → 9:16

Cropping 16:9 to 9:16 loses **over 50%** of the original frame. From 1920x1080, only a
607px-wide vertical strip is native 9:16 at full height.

### Three Crop Strategies

| Strategy | When to Use | Trade-off |
|----------|------------|-----------|
| **Center crop** | Subject is centered (talking head) | Fastest; loses all side content |
| **Smart reframe** | Subject or ROI is off-center | Tracks subject, pans crop window |
| **Split layout** | Full frame must be preserved | 16:9 in top portion, captions below |

### Speaker Framing Rules

- Position subject in center third of 16:9 frame during production
- For 9:16 crop: center on speaker's face/torso
- Rule of thirds still applies — subject eyes at upper-third line
- Head-and-shoulders is the natural framing for vertical
- Never crop if it cuts speaker's face at the edge

### The 1920x1920 Square Master Concept

Shoot or compose in 1:1 square, then crop to any target ratio:
- 16:9 = 1920x1080 horizontal strip from center
- 9:16 = 1080x1920 vertical strip from center
- 4:5 = 1080x1350 (Instagram feed)
- 1:1 = use as-is (1080x1080)

**For existing 16:9 footage**: The effective multi-format safe area is only the center
1080x1080 of a 1920x1080 frame. Everything outside that center square will be lost
in at least one output format.

---

## 3.3 Platform-Specific Safe Zones

All measurements for 1080x1920 canvas (9:16).

### Per-Platform Margins

| Platform | Top | Bottom | Left | Right | Safe Area |
|----------|-----|--------|------|-------|-----------|
| TikTok | 160px | 480px | 120px | 120px | 840x1280 |
| YouTube Shorts | 380px | 380px | 60px | 120px | 900x1160 |
| Instagram Reels | 250px | 320px | 120px | 120px | 840x1350 |
| Facebook Reels | 269px | 672px | 65px | 65px | 950x979 |

### Universal Safe Zone (Clears ALL Platforms)

```
Top:    380px  (YouTube Shorts is most restrictive)
Bottom: 480px  (TikTok is most restrictive)
Left:   120px
Right:  120px

Universal safe rect: x1=120, y1=380, x2=960, y2=1440
Dimensions: 840 x 1060 usable area
```

**Rule**: For text overlays on 9:16 content, place ALL text within this rect. Speaker face
should be in the upper-center of the safe zone.

### LinkedIn (1:1 Square)

- Resolution: 1080x1080
- Safe margins: 108px on all sides (central 80%)
- Usable text area: 864x864
- Takes up more feed space than 16:9 on mobile

---

## 3.4 Platform Duration Sweet Spots

| Platform | Max Length | Sweet Spot | Why |
|----------|----------|------------|-----|
| YouTube Shorts | 3 min | **50-58s** | 50-60s range = 22x more views than <10s |
| Instagram Reels | 20 min | **7-15s** (viral) / **30-45s** (value) | 7s loops 3x = 300% retention signal |
| TikTok | 10 min | **15-60s** | <60s dominates for virality |
| LinkedIn | 10 min | **30-60s** | Professional, value-first |
| YouTube long-form | No limit | **8-15 min** | 5-10 min = 31.5% peak retention |

---

## 3.5 Platform-Specific Adaptation

The same clip is NOT posted identically everywhere. Each platform gets a format-native version.

### What Works Per Platform

| Element | YouTube Shorts | TikTok | Instagram Reels | LinkedIn |
|---------|---------------|--------|-----------------|----------|
| Hook style | Educational promise | Trend/shock | Aesthetic visual | Professional insight |
| Content type | Tutorials, tips | Entertainment, raw | Lifestyle, visual | Case studies, data |
| Captions | Essential | Expected | Recommended | Essential |
| Music | Optional | Trending sounds | Trending audio | Minimal |
| Polish level | Medium-high | Low-medium | Medium-high | Medium |
| CTA style | "Subscribe" | "Follow for more" | "Save this" | "Comment below" |

### Format-Specific Extraction

From the same source moment, generate:
- **YouTube Short**: ~55s, educational hook, complete thought, clean ending
- **TikTok**: ~30s, fastest pacing, front-load payoff
- **Instagram Reel**: ~15s OR ~30s, optimize for seamless loop, aesthetic first frame
- **LinkedIn (1:1)**: ~45-60s, professional framing, text-heavy captions

---

## 3.6 Independent Hooks for Short-Form

Long-form intros build context (15-30s). Short-form hooks must capture in under 3 seconds.
The "slow build" approach that works for long-form is **death for Shorts**.

### Five Short-Form Hook Formulas

| Formula | Pattern | Example |
|---------|---------|---------|
| Pattern interrupt | Contradiction or unexpected visual | "I made more money after stopping daily posts" |
| Direct promise | Specific measurable outcome | "This 5-second edit doubled my watch time" |
| Question hook | Information gap | "Why do your Shorts die at 40%?" |
| Self-identifying | Make viewer feel understood | "Struggling with consistency?" |
| Contradiction + promise | Counterintuitive + proof | "Longer Shorts get more views — I'll prove it" |

### Hook Implementation Rules

- Complete hook in 2-2.5 seconds
- Opening visual: high-contrast, in-focus, movement-based
- Text overlay: short, high-contrast, on-screen 2+ seconds
- Delivery: slightly faster than normal, confident (not rushed)
- 5-10 words maximum
- NEVER start with setup context — start with the strongest statement

---

## 3.7 Vertical Video Editing (9:16 Specific)

### Text Rules
- Max 2 lines, ~37 characters per line
- Font size: 48-72px at 1080w (significantly larger than landscape)
- White text with black border/shadow
- Center-aligned (never left/right aligned in vertical)
- Position in lower quarter, below speaker's face

### Framing Rules
- Subject fills more frame than landscape
- Tight framing: head-and-shoulders to waist
- Subject in vertical center, slightly above middle
- Critical content in central 80%
- Leave headroom for platform UI at top

### Pacing Rules
- Increase cut frequency by ~30% compared to landscape
- 24fps for cinematic, 30fps for text/UI heavy
- Motion graphics: larger and simpler than landscape equivalents
- Vertical format drives 58% better engagement than horizontal

---

## 3.8 Per-Platform Output Specs

| Platform | Ratio | Resolution | Duration | Safe Zone (px from edges) |
|----------|-------|-----------|----------|--------------------------|
| YouTube (long) | 16:9 | 1920x1080 | 8-20 min | Standard broadcast safe |
| YouTube Shorts | 9:16 | 1080x1920 | 50-58s | T:380 B:380 L:60 R:120 |
| TikTok | 9:16 | 1080x1920 | 15-60s | T:160 B:480 L:120 R:120 |
| Instagram Reels | 9:16 | 1080x1920 | 7-45s | T:250 B:320 L:120 R:120 |
| LinkedIn | 1:1 | 1080x1080 | 30-60s | 108px all sides |
| Facebook Reels | 9:16 | 1080x1920 | 15-60s | T:269 B:672 L:65 R:65 |
