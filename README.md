# videngine

Automated video production pipeline. One long video in → multiple platform-ready cuts out, with AI-driven editorial decisions and voice-cloned narration.

## Pipeline

```
Raw Video → Transcribe → AI Edit Agent → Voice Clone → Assemble → Multi-Format Render
                                                                        ↓
                                                          16:9 / 9:16 / 4:5
```

| Stage | What it does | Tool |
|-------|-------------|------|
| **Transcribe** | Extract audio, generate word-level timestamps | whisper.cpp (CUDA) |
| **Analyze** | Select best segments, plan narrative, write narration scripts | Claude Opus (Anthropic API) |
| **Voice** | Clone founder's voice for intro/outro narration | Chatterbox TTS (CUDA) |
| **Assemble** | Cut segments, layer narration on templates, concat, watermark | FFmpeg |
| **Render** | Output multiple aspect ratios for each platform | FFmpeg |

Each stage checkpoints to `job_state.json`. If anything fails, `videngine resume` picks up where it stopped.

## Requirements

- Python 3.11+ (3.14 not supported — PyTorch requires ≤3.13)
- FFmpeg
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (`whisper-cli`) + `ggml-large-v3-turbo` model
- ANTHROPIC_API_KEY environment variable
- NVIDIA GPU recommended (CUDA for whisper.cpp + Chatterbox)

## Setup

```bash
git clone git@github.com:bsduptime/videocontentai.git
cd videocontentai

# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install
uv venv --python python3.11
source .venv/bin/activate
uv pip install -e .

# For voice cloning (requires CUDA or Apple Silicon — not Intel Mac)
uv pip install chatterbox-tts

# Download whisper model
mkdir -p ~/.videngine/models
wget -O ~/.videngine/models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

### Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

```bash
# Full pipeline
videngine process video.mp4 --project "podcast-ep42"

# Skip voice cloning
videngine process video.mp4 --no-voice

# Target specific duration and formats
videngine process video.mp4 --target-duration 120 --ratios 9x16,4x5

# Pause after AI analysis to review edit decisions
videngine process video.mp4 --review

# Resume a failed/interrupted job
videngine resume --latest
videngine resume <job-id>

# List jobs
videngine jobs
videngine jobs --status failed

# Cleanup old completed jobs
videngine cleanup --older-than 7d

# Dry run (show what would happen)
videngine process video.mp4 --dry-run
```

## Assets

Drop these into `assets/`:

| Asset | Path | Notes |
|-------|------|-------|
| Logo/watermark | `assets/watermarks/logo.png` | Transparent PNG |
| Intro template | `assets/intros/default.mp4` | Branded intro animation (3-5s) |
| Outro template | `assets/outros/default.mp4` | Branded outro with CTA space |
| Voice reference | `assets/voice_refs/founder.m4a` | 10-30s of clear speech for voice cloning |

## Configuration

All settings in `config/default.toml`. Override with env vars prefixed `VIDENGINE_` (e.g. `VIDENGINE_AI_MODEL=claude-sonnet-4-20250514`).

## Target Platform

Production: NVIDIA Jetson Orin AGX (64GB, CUDA, ARM64 Linux).

Development on any Linux with CUDA, or macOS Apple Silicon. Intel Mac is not supported for ML stages (PyTorch dropped x86 macOS).
