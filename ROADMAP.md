# Roadmap

## Phase 1 — MVP (done)

Single-cut pipeline: transcribe → AI analysis → voice clone → assemble → render.

- [x] Project scaffolding + pyproject.toml
- [x] Pydantic data models (Transcript, EditDecision, JobState)
- [x] TOML config with env var overrides
- [x] ffprobe wrapper + FFmpeg command builders
- [x] Whisper transcription stage (audio extract + whisper-cli)
- [x] Claude Opus AI editing agent (structured output via tool use)
- [x] Chatterbox voice cloning stage (auto-converts m4a/mp3 refs)
- [x] FFmpeg assembly (cut + concat segments)
- [x] Multi-aspect-ratio render (16:9, 9:16, 4:5)
- [x] Pipeline orchestrator with stage checkpointing
- [x] CLI: process, resume, jobs, cleanup commands

## Phase 2 — Multi-Cut + Platform Awareness

One long video → suite of platform-optimized clips at different lengths.

- [x] Multi-cut analyze stage: Claude scores once, then plans each cut spec independently
- [x] Per-cut editorial lens (editorial_lens field per cut spec, passed to Claude)
- [x] Cut-level intro/outro narration planning (Claude generates narration text per cut)
- [ ] Brand-aware AI prompt (brand name, voice/tone, terminology in selection prompt)

## Phase 3 — Thumbnails + Visual Assets

- [ ] Face-consistent thumbnail generation (Flux PuLID / IP-Adapter)
- [ ] AI-described thumbnail scenes per cut
- [ ] Branded thumbnail templates (colors, logo, typography from brand)
- [ ] YouTube thumbnail + social preview image per cut

## Phase 4 — Assembly Polish

- [x] Intro/outro template layering (1920x1920 square masters cropped per aspect ratio)
- [x] Watermark overlay (position, opacity, scale from config)
- [x] Per-format watermark placement (bottom-right for 16:9/4:5, top-left+180px for 9:16)
- [ ] Intro/outro narration audio layering
- [ ] Per-segment portrait crop focus hints (center/left_third/right_third)
- [ ] Crossfade transitions between segments
- [ ] Rich progress bars for long FFmpeg operations

## Phase 5 — Distribution

- [ ] Output metadata per cut (title, description, hashtags, caption)
- [ ] Integration with content repo posting scripts (post-youtube.js, post-tiktok.js, etc.)
- [ ] Auto-publish as drafts to platforms
- [ ] Content tracking integration (tracking.json in content repo)

## Phase 6 — Jetson Optimization

- [x] Jetson setup script (setup-jetson.sh) — Python version detection, deps, model download
- [x] PyTorch CUDA on Jetson via NVIDIA wheel index (pypi.jetson-ai-lab.io)
- [x] Chatterbox TTS aarch64 compatibility (perth watermarker patch, soundfile save)
- [x] whisper.cpp static build with CUDA on ARM64
- [x] Disk management — venv + models on SD card via symlinks
- [ ] `videngine setup` command (interactive version of setup-jetson.sh)
- [ ] NVENC hardware encoding (h264_nvenc instead of libx264)
- [ ] GPU memory management for concurrent whisper + Chatterbox
- [ ] Batch processing (multiple source videos queued)
