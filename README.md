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
| **Thumbnail** | Generate platform-specific thumbnails per cut | Claude + Flux Kontext API + Pillow |

Each stage checkpoints to `job_state.json`. If anything fails, `videngine resume` picks up where it stopped.

## Requirements

- Python 3.10+ (3.14 not supported — PyTorch requires ≤3.13)
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

## Content Production Pipeline

For the David K content pipeline, videngine handles post-production:

```bash
# Step 0: Pull recordings from NAS, transcribe, auto-sort into slugs
# Use /pull-input in Claude Code

# Step 1-3: Ingest + audio preprocessing + transcription (mechanical)
videngine pre-process {slug}

# Step 5-7: Cut beats + re-transcribe + VAD/emotion scoring (mechanical)
videngine cut-beats {slug}

# Full pipeline with agent (scene matching + readiness report):
# Use /check-readiness {slug} in Claude Code

# Push finished output to NAS for team review:
# Use /push-output {slug} in Claude Code
```

**Directory structure:**
```
video-content/
  input/_inbox/        ← staging area for NAS pulls (transient)
  input/_unsorted/     ← recordings that couldn't be matched to a script
  input/{slug}/        ← raw files + script + sidecar (ready for pre-process)
  production/{slug}/   ← processing workspace (wiped on each run)
  output/{slug}/       ← finished exports
```

**`/pull-input`** pulls videos from the Synology NAS (`ssh nas`), transcribes with Whisper, matches transcripts against coached scripts in `~/code/content/`, and sorts files into the correct slug directory. If `pre-process` finds a `.transcript.json` file alongside a video, it skips re-transcription.

See `.claude/commands/pull-input.md` and `.claude/commands/check-readiness.md` for agent-orchestrated pipelines.

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
| Intro template | `assets/intros/default-intro.mp4` | 1920x1920 square master, cropped per aspect ratio |
| Outro template | `assets/outros/default-outro.mp4` | 1920x1920 square master, cropped per aspect ratio |
| Voice reference | `assets/voice_refs/founder.m4a` | 10-30s of clear speech for voice cloning |

## Configuration

All settings in `config/default.toml`. Override with env vars prefixed `VIDENGINE_` (e.g. `VIDENGINE_AI_MODEL=claude-sonnet-4-20250514`).

## Target Platform

Production: NVIDIA Jetson Orin AGX (64GB, CUDA, ARM64 Linux).

Development on any Linux with CUDA, or macOS Apple Silicon. Intel Mac is not supported for ML stages (PyTorch dropped x86 macOS).
