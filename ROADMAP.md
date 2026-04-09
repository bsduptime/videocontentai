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
- [x] Brand-aware AI prompt (brand name, voice/tone, terminology in selection prompt)

## Phase 3 — Thumbnails + Visual Assets

- [x] Claude-generated thumbnail concepts (hook text, archetype, visual direction)
- [x] Pillow compositing engine (gradient backgrounds, face composite, text rendering)
- [x] Branded thumbnail templates (colors, fonts, logo overlay per brand)
- [x] Multi-platform variants (YouTube 1280x720, Shorts 1080x1920, LinkedIn 1200x627)
- [x] Flux Kontext API integration for AI-generated base images with face consistency
- [x] Pillow-only fallback when API unavailable
- [x] Local GPU image generation (Flux/SD on Jetson) — assess quality vs API

## Phase 4 — Assembly Polish

- [x] Intro/outro template layering (1920x1920 square masters cropped per aspect ratio)
- [x] Watermark overlay (position, opacity, scale from config)
- [x] Per-format watermark placement (bottom-right for 16:9/4:5, top-left+180px for 9:16)
- [ ] Intro/outro narration audio layering
- [ ] Per-segment portrait crop focus hints (center/left_third/right_third)
- [x] Crossfade transitions between segments
- [ ] Rich progress bars for long FFmpeg operations

## Phase 5 — Distribution

- [ ] Output metadata per cut (title, description, hashtags, caption)
- [ ] Integration with content repo posting scripts (post-youtube.js, post-tiktok.js, etc.)
