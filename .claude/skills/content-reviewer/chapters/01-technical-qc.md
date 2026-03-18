# Chapter 1: Technical QC

Derived from broadcast QC standards (Clearcast, EBU), Netflix QC error codes, and automated
QC tools (Telestream Vidchecker, Interra Baton). Adapted for YouTube/social media delivery.

---

## 1.1 Severity Classification

Every technical issue gets a severity level:

| Severity | Label | Definition | Example |
|----------|-------|-----------|---------|
| 3 | **BLOCKER** | Content is broken or unacceptable for publishing | Audio clipping, corrupt frames, wrong aspect ratio |
| 2 | **ISSUE** | Noticeable problem that degrades experience | Music too loud over speech, inconsistent levels between segments |
| 1 | **NOTE** | Minor imperfection, fix at creator's discretion | Slight letterboxing, sub-optimal bitrate |

---

## 1.2 Audio QC Checklist

| Check | Pass Criteria | Severity if Failed |
|-------|--------------|-------------------|
| Integrated loudness | -14 LUFS ±2 (YouTube target) | ISSUE if ±2-4, BLOCKER if >±4 |
| True peak | <= -1.0 dBTP | BLOCKER if exceeded (audible clipping) |
| Voice-to-music separation | >= 10 dB during speech | ISSUE if 6-10 dB, BLOCKER if <6 dB |
| Dead air / unintentional silence | No gaps > 2s unless clearly intentional | ISSUE |
| Audio sync | Lip sync within ±40ms | BLOCKER if >80ms, ISSUE if 40-80ms |
| Channel layout | Stereo (2.0) for all outputs | BLOCKER if mono or missing channel |
| Audio artifacts | No clicks, pops, hiss, or digital distortion | BLOCKER if prominent, NOTE if subtle |
| Music presence | Background music present (unless spec says otherwise) | ISSUE if missing when mood was specified |

### How to Check

- **Loudness**: `ffmpeg -i {file} -af loudnorm=print_format=json -f null -` → read `input_i`
- **True peak**: Read `input_tp` from same command
- **Silence detection**: `ffmpeg -i {file} -af silencedetect=noise=-40dB:d=2 -f null -`
- **Voice-to-music**: Compare RMS during speech segments vs. music-only segments

---

## 1.3 Video QC Checklist

| Check | Pass Criteria | Severity if Failed |
|-------|--------------|-------------------|
| Resolution | Matches spec (1920x1080 or 1080x1920) | BLOCKER if wrong |
| Aspect ratio | Matches spec (16:9 or 9:16) | BLOCKER if wrong |
| Frame rate | Consistent, no dropped frames | ISSUE if variable, BLOCKER if <24fps |
| Codec | h264 (h264_nvmpi output) | NOTE if different but playable |
| Black frames | No unintentional black frames >0.5s | ISSUE if present |
| Freeze frames | No unintentional freeze >1s | BLOCKER if >2s, ISSUE if 1-2s |
| Corrupt frames | No visual artifacts, glitches, or macroblocking | BLOCKER if visible |
| Watermark | Present and correctly positioned (if branding requires it) | ISSUE if missing or misplaced |
| Color consistency | No unintentional grade shifts between segments | NOTE |

### How to Check

- **Resolution/codec**: `ffprobe -v quiet -show_entries stream=width,height,codec_name`
- **Black frames**: `ffmpeg -i {file} -vf blackdetect=d=0.5:pix_th=0.10 -f null -`
- **Freeze frames**: `ffmpeg -i {file} -vf freezedetect=n=0.003:d=1 -f null -`

---

## 1.4 Structure QC Checklist

| Check | Pass Criteria | Severity if Failed |
|-------|--------------|-------------------|
| Duration | Within cut spec min/max range | BLOCKER if outside range |
| Intro present | Branded intro present (unless hook clip) | ISSUE if missing on non-hook |
| Outro present | Branded outro present (unless hook clip) | ISSUE if missing on non-hook |
| Hook prepended | Hook prepended for specs with `prepend_hook: true` | ISSUE if missing |
| Clean start | No blank/black frames at start | ISSUE |
| Clean end | No trailing silence or black at end | NOTE |
| Mid-sentence cuts | No words cut mid-syllable | BLOCKER |

---

## 1.5 Caption/Accessibility

| Check | Pass Criteria | Severity if Failed |
|-------|--------------|-------------------|
| Captions available | Subtitle track present or burn-in captions | NOTE (recommended) |
| Caption accuracy | Matches spoken words | ISSUE if >5% error rate |
| Caption timing | Synced to speech within 200ms | ISSUE if drifting |
| Text readability | All overlay text readable at mobile resolution | ISSUE if too small or low contrast |

---

## 1.6 PSE (Photosensitive Epilepsy) Safety

Relevant for UK/EU distribution and general safety:

| Check | Pass Criteria | Severity |
|-------|--------------|----------|
| Flash frequency | No flashing >3 Hz | BLOCKER |
| Brightness transitions | No rapid luminance changes >20 cd/m² | ISSUE |
| Red flash | No saturated red flash sequences | BLOCKER |

These are broadcast standards (Ofcom/ITU) but good practice for all content.
