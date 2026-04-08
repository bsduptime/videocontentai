# videngine

Automated video production pipeline. One long video in → multiple platform-ready cuts out, with AI-driven editorial decisions and voice-cloned narration.

## Pipeline

```
Source Video → Clean Source (denoise+compress) → Transcribe → AI Analysis
    → Cut → Watermark → [Background Replace] → Intro/Outro → Hook → Thumbnail
                                                                       ↓
                                                    YouTube / Instagram / LinkedIn / Shorts
```

| Stage | What it does | Tool |
|-------|-------------|------|
| **1. Transcribe** | Extract audio (48kHz), denoise, compress, transcribe, create clean source | DeepFilterNet3 + whisper.cpp (CUDA) |
| **2. Analyze** | Score segments, plan cuts, write narration scripts | Claude Opus |
| **3. Cut** | Extract segments from clean source, concat, loudness normalize, mix music | FFmpeg (stream copy + EBU R128) |
| **4. Watermark** | Logo overlay + visual effects (zoom, text) | FFmpeg (h264_nvmpi) |
| **5. Background** | Replace video background via person segmentation (optional) | RVM (ONNX) + FFmpeg |
| **6. Intro/Outro** | Prepend/append branded templates + voice narration | Chatterbox TTS + FFmpeg |
| **7. Hook Prepend** | Prepend hook clip to specified cuts | FFmpeg (stream copy) |
| **8. Thumbnail** | AI concept → image generation → text/branding overlay (YouTube + Instagram + LinkedIn) | Claude + Flux/PuLID + Pillow |

Each stage checkpoints to `job_state.json`. If anything fails, `videngine resume` picks up where it stopped.

### Audio Processing (Stage 1)

Audio is processed once on the full source file, not per-clip:

1. **Extract** at 48kHz (single extraction for both denoise and transcription)
2. **Denoise** via DeepFilterNet3 (full file — consistent noise profile)
3. **Compress** with device-specific profile (macbook or iphone)
4. **Downsample** to 16kHz → Whisper transcription (on clean audio)
5. **Create `source_clean.mp4`** — original video + denoised/compressed audio

All subsequent stages cut from the clean source. Only per-clip loudness normalization (EBU R128) remains in the cut stage.

### Background Replacement (Stage 5)

Optional stage using [Robust Video Matting (RVM)](https://github.com/PeterL1n/RobustVideoMatting) for person segmentation. Disabled by default.

**Background types:**
- `blur` — blurred version of the original background
- `solid` — solid hex color (e.g. `#1a1a2e`)
- `image` — custom background image (PNG/JPG)

**Enable in config:**
```toml
[background]
enabled = true
background_type = "blur"    # "blur", "solid", "image"
blur_strength = 21
```

**Or per-run:** `VIDENGINE_BACKGROUND_ENABLED=true`

**Standalone command:** `/replace-background input.mp4 background.png [output.mp4]`

The RVM ONNX model (~14MB) auto-downloads on first use. For faster processing, install `onnxruntime-gpu` (CUDA provider gives ~10-20x speedup over CPU).

### Thumbnail Generation (Stage 8)

Generates platform-specific thumbnails per cut:

| Output | Size | Format | Design |
|--------|------|--------|--------|
| `thumbnail_youtube.png` | 1280x720 | PNG | Face + hook text + branding (rule of thirds) |
| `thumbnail_instagram.jpg` | 1080x1920 | JPEG 95% sRGB | Brand colors + centered text + dimmed frame (center-out for 1:1 grid crop) |
| `thumbnail_instagram_grid.jpg` | 1080x1080 | JPEG 95% sRGB | Grid preview — what people see on profile |
| `thumbnail_linkedin.png` | 1200x627 | PNG | Resized from YouTube |

Instagram covers are designed **center-out**: all critical content (text, logo) lives inside the center 1080x1080 square, which is what appears on the profile grid. The gradient background extends to fill 9:16 for the full Reel cover view.

## Brand System

Brand visuals are defined once per brand, separate from editorial cut specs.

### Brand Config

```
assets/brands/{brand_name}/
├── brand.json          ← colors, fonts, watermark, templates, thumbnail config
├── fonts/              ← brand-specific fonts (TTF/OTF)
└── logos/              ← logo variants (transparent PNG)
```

Example `brand.json`:
```json
{
  "name": "dbexpertai",
  "display_name": "DB Expert AI",
  "colors": {
    "primary": "#336791",
    "accent": "#F5A623",
    "background_dark": "#1a2332"
  },
  "fonts": {
    "heading": "Montserrat-Bold.ttf",
    "body": "BebasNeue-Regular.ttf"
  },
  "thumbnail": {
    "youtube": { "text_style": "line1_white_line2_red", "use_face": true },
    "instagram": { "text_style": "centered_bold", "use_face": false, "show_accent_strip": true }
  },
  "watermark": { "file": "dbexpertai-watermark.png" },
  "templates": { "intro_9x16": "dbexpert-intro-9x16.mp4" }
}
```

### Input Contract (manifest.json)

When processing a slug, the input directory can include a `manifest.json` that ties the recording to a brand:

```json
{
  "brand": "dbexpertai",
  "slug": "postgres-indexing-tips",
  "language": "en",
  "audio_profile": "iphone"
}
```

The pipeline loads brand config by name from `assets/brands/`. Manifest overrides (per-job colors, person description) are applied on top.

If no manifest exists, the pipeline reads `source.brand` from the cut spec file.

### Cut Specs

Cut specs define editorial format only — no brand visuals:

```
config/cut_specs/
├── landscape-dbexpertai.json    ← 16:9 screen recordings
├── portrait-dbexpertai.json     ← 9:16 iPhone recordings
├── landscape-founder.json       ← 16:9 talking head
├── portrait-founder.json        ← 9:16 talking head
└── moods.json                   ← mood → music file mappings
```

Each spec has: `pipeline` name, `source` context (brand, format, aspect ratio, audio profile, tone), and `cuts[]` (editorial formats with duration ranges, mood options, channel targets, and editorial lens).

## Claude Code Commands

| Command | What it does |
|---------|-------------|
| `/replace-background` | Replace video background (RVM + FFmpeg composite) |
| `/pull-input` | Pull recordings from NAS, transcribe, match to scripts, sort |
| `/push-output` | Push finished videos to NAS for review |
| `/check-readiness` | Full readiness check for a video slug |
| `/review-editing-plan` | QA review of a cut plan |
| `/sync` | Git stash/pull/push to main |

## Requirements

- Python 3.10+ (3.14 not supported — PyTorch requires ≤3.13)
- FFmpeg
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (`whisper-cli`) + `ggml-large-v3-turbo` model
- ANTHROPIC_API_KEY environment variable
- NVIDIA GPU recommended (CUDA for whisper.cpp + Chatterbox)

### Additional for background replacement

- `opencv-python-headless>=4.8`
- `onnxruntime>=1.16` (or `onnxruntime-gpu` for CUDA acceleration)
- `numpy>=1.24`

## Setup

```bash
git clone git@github.com:bsduptime/videocontentai.git
cd videocontentai

# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install
uv venv --python python3.10  # or python3.11
source .venv/bin/activate
uv pip install -e .

# For voice cloning (requires CUDA or Apple Silicon — not Intel Mac)
uv pip install chatterbox-tts

# Download whisper model
mkdir -p ~/.videngine/models
wget -O ~/.videngine/models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

### Jetson Orin Setup

```bash
# One-shot setup script (handles Python version detection, deps, model download)
./setup-jetson.sh

# PyTorch must come from NVIDIA's Jetson index (PyPI wheels are CPU-only)
uv pip install torch torchaudio --index-url https://pypi.jetson-ai-lab.io/jp6/cu126

# PyTorch 2.8+ needs nvidia-cudss-cu12
uv pip install nvidia-cudss-cu12
```

### Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Configuration

All settings in `config/default.toml`. Override with env vars prefixed `VIDENGINE_` (e.g. `VIDENGINE_BACKGROUND_ENABLED=true`).

Key config sections:

| Section | What it controls |
|---------|-----------------|
| `[paths]` | Working directory for jobs |
| `[whisper]` | Model path, language, threads |
| `[ai]` | Claude model, max tokens, temperature |
| `[voice]` | TTS engine, reference audio |
| `[video]` | Intro/outro templates, watermark, music, loudness targets |
| `[audio]` | Denoise toggle, device profiles (macbook/iphone) |
| `[background]` | Background replacement (disabled by default) |
| `[encoding]` | Video codec (h264_nvmpi on Jetson, libx264 fallback) |
| `[thumbnail]` | ComfyUI/Flux URLs, fallback mode |

## Target Platform

Production: NVIDIA Jetson Orin AGX (64GB, CUDA, ARM64 Linux).

Development on any Linux with CUDA, or macOS Apple Silicon. Intel Mac is not supported for ML stages (PyTorch dropped x86 macOS).
