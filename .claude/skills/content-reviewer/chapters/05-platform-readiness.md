# Chapter 5: Platform Readiness

Verify the finished clip meets platform-specific requirements before publishing.
This is not creative judgment — it's compliance checking.

---

## 5.1 Duration Compliance

| Platform | Cut Spec Field | Sweet Spot | Max | Severity if Wrong |
|----------|---------------|------------|-----|-------------------|
| YouTube Shorts | `channels: ["YouTube Short"]` | 50-58s | 180s | ISSUE if <15s or >180s |
| Instagram Reels | `channels: ["Instagram Reel"]` | 7-15s (viral) / 30-45s (value) | 1200s | NOTE |
| TikTok | `channels: ["TikTok"]` | 15-60s | 600s | NOTE |
| YouTube Video | `channels: ["YouTube Video"]` | 8-15 min | none | NOTE if <2 min |
| LinkedIn | `channels: ["LinkedIn Post"]` | 30-60s | 600s | NOTE |

Cross-reference clip duration against the cut spec's `min_duration` and `max_duration`.
Outside the spec range = BLOCKER.

---

## 5.2 Resolution and Format

| Platform | Required Ratio | Required Resolution | Codec |
|----------|---------------|-------------------|-------|
| YouTube (long-form) | 16:9 | 1920x1080 | h264 |
| YouTube Shorts | 9:16 | 1080x1920 | h264 |
| Instagram Reels | 9:16 | 1080x1920 | h264 |
| TikTok | 9:16 | 1080x1920 | h264 |
| LinkedIn (square) | 1:1 | 1080x1080 | h264 |

Wrong resolution or aspect ratio = BLOCKER.

---

## 5.3 Safe Zone Compliance (9:16 Content)

All text, graphics, and critical visual content must fall within platform safe zones.

### Universal Safe Zone (Clears ALL Platforms)

```
Pixel coordinates (1080x1920 canvas):
  Top:    380px  (YouTube Shorts UI)
  Bottom: 480px  (TikTok buttons)
  Left:   120px
  Right:  120px

Safe rect: x1=120, y1=380, x2=960, y2=1440
Usable area: 840 x 1060 pixels
```

### Per-Platform Safe Areas

| Platform | Top | Bottom | Left | Right | Safe Area |
|----------|-----|--------|------|-------|-----------|
| TikTok | 160px | 480px | 120px | 120px | 840x1280 |
| YouTube Shorts | 380px | 380px | 60px | 120px | 900x1160 |
| Instagram Reels | 250px | 320px | 120px | 120px | 840x1350 |

### What to Check

- Text overlays: are they within the universal safe rect?
- Lower-third graphics: do they clear the bottom 480px?
- Speaker's face: is it in the upper portion of the safe zone?
- Watermark: does it avoid being covered by platform UI?

Any critical content outside the safe zone = ISSUE. Content completely hidden by platform
UI = BLOCKER.

---

## 5.4 Algorithm Signal Checklist

Predict how platform algorithms will evaluate this content:

### YouTube (Satisfaction-Weighted, 2025+)

| Signal | Check | Why It Matters |
|--------|-------|---------------|
| Completion likelihood | Will viewers watch 50%+ based on pacing? | Satisfaction metric: shorter + completed > longer + abandoned |
| Session continuation | Does the ending drive continued watching? | YouTube rewards videos that keep users on platform |
| Hook holds 70%+ at 30s | See Ch.2 hook diagnosis | Early retention is the strongest algorithmic signal |
| Not misleading | Does content match title/description from cut plan? | Misleading = satisfaction survey damage |
| Rewatchability | Any moments worth replaying? | Rewatch signals high value |

### Short-Form Platforms (Shorts/Reels/TikTok)

| Signal | Check | Why It Matters |
|--------|-------|---------------|
| 3-second hold | Does the first frame stop the scroll? | 50-60% of viewers drop in first 3s |
| Completion rate | Can the viewer watch 70%+ without wanting to skip? | Primary algorithm signal on all short platforms |
| Loop potential | Does the ending connect smoothly to the beginning? | Loops inflate retention metrics (especially Reels) |
| Share-worthy moment | Is there a moment someone would DM to a friend? | Shares > saves > comments > likes in algorithm weight |
| Save-worthy value | Does it contain information worth bookmarking? | Saves signal lasting value |
| No watermarks | No TikTok/CapCut/competitor watermarks? | Instagram suppresses watermarked content |

---

## 5.5 Thumbnail Moment Verification

For every clip, verify that a thumbnail-worthy frame exists:

| Criterion | What to Look For |
|-----------|-----------------|
| Sharp (no motion blur) | Clear, in-focus frame |
| Face with expression | Emotion visible (surprise, excitement) |
| High contrast | Readable at 160x90px mobile thumbnail size |
| Clear focal point | Single subject, not cluttered |
| Text space | Room for overlay text without obscuring subject |
| Represents the content | Frame occurs during a relevant/interesting moment |

If no thumbnail-worthy frame exists in the first 30% of the clip = NOTE.
If no thumbnail-worthy frame exists at all = ISSUE.

---

## 5.6 Brand Safety Quick Check

Based on GARM (Global Alliance for Responsible Media) framework:

| Check | Pass | Severity if Failed |
|-------|------|-------------------|
| No offensive language without context | Clean or appropriately bleeped | ISSUE |
| No competitor disparagement | Factual comparisons only | NOTE |
| Sponsor disclosures present (if applicable) | FTC/ASA compliant | BLOCKER |
| No copyrighted music (beyond licensed tracks) | Only moods.json tracks used | BLOCKER |
| No visible personal data (emails, phone numbers) | Blurred or absent | BLOCKER |
| Content matches brand tone | Aligns with source.tone from cut spec | NOTE |
