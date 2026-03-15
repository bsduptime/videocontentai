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

- [ ] Multi-cut analyze stage: Claude plans all cuts in one pass
  - YouTube long (3-10 min, 16:9)
  - YouTube Short (30-60s, 9:16)
  - Reel (30-60s, 9:16) — Instagram, Facebook, TikTok
  - LinkedIn (60-120s, 4:5)
  - X clip (30-90s, 16:9)
  - Story (15-30s, 9:16)
- [ ] Platform-aware render specs from MEDIA-SPECS (codec, bitrate, resolution per platform)
- [ ] Brand-aware AI prompt (voice/tone, terminology, content motions from brand skill)
- [ ] Per-cut editorial lens (hook-heavy for reels, narrative for YouTube, insight for LinkedIn)
- [ ] Cut-level intro/outro narration (different scripts per cut)

## Phase 3 — Thumbnails + Visual Assets

- [ ] Face-consistent thumbnail generation (Flux PuLID / IP-Adapter)
- [ ] AI-described thumbnail scenes per cut
- [ ] Branded thumbnail templates (colors, logo, typography from brand)
- [ ] YouTube thumbnail + social preview image per cut

## Phase 4 — Assembly Polish

- [ ] Intro/outro template layering with narration audio
- [ ] Watermark overlay (position, opacity, scale from config)
- [ ] Per-segment portrait crop focus hints (center/left_third/right_third)
- [ ] Crossfade transitions between segments
- [ ] Rich progress bars for long FFmpeg operations

## Phase 5 — Distribution

- [ ] Output metadata per cut (title, description, hashtags, caption)
- [ ] Integration with content repo posting scripts (post-youtube.js, post-tiktok.js, etc.)
- [ ] Auto-publish as drafts to platforms
- [ ] Content tracking integration (tracking.json in content repo)

## Phase 6 — Jetson Optimization

- [ ] `videngine setup` command (download models, verify deps, check CUDA)
- [ ] NVENC hardware encoding (h264_nvenc instead of libx264)
- [ ] GPU memory management for concurrent whisper + Chatterbox
- [ ] Batch processing (multiple source videos queued)
