---
description: Pre-process video in video-content/input/{slug}/ — ingest, audio processing, transcription — then copy to production/{slug}/
allowed-tools: Bash, Read, Write, Glob, Grep
---

Pre-process all video files in `video-content/input/$ARGUMENTS/`, applying audio preprocessing and transcription, then copy everything to `video-content/production/$ARGUMENTS/`.

This command covers pipeline steps 1-3:
1. **Ingest** — validate input, inventory files
2. **Audio pre-processing** — denoise + compress + loudnorm per detected device profile
3. **Transcription** — Whisper with word-level timecodes per file

## Steps

### 1. Validate input

- Slug is passed as `$ARGUMENTS` (e.g. `/pre-process my-video-slug`)
- Check `video-content/input/{slug}/` exists and contains at least one video file (.mp4, .mov, .MOV, .mkv)
- Check for metadata files: expect a script `.md` and sidecar `.json` (warn if missing but don't fail)
- Check for `manifest.md` — if it exists in input, copy it; if not, it should already exist in `production/{slug}/` from the coaching step

### 2. Inventory files

For each video file, probe with ffprobe to get:
- Duration
- Resolution
- File size

For each video file, detect the recording device:
```python
from videngine.ffmpeg.probe import detect_recording_device
device = detect_recording_device(video_path)  # returns "iphone" or "macbook"
```

Report all files and detected devices to the user.

### 3. Create production directory

- Create `video-content/production/{slug}/` if it doesn't exist
- Create subdirectories: `audio/`, `transcripts/`
- Copy all non-video files (.md, .json) from input to production as-is

### 4. Apply audio preprocessing

For each video file, run the full audio chain using the detected profile:

```python
from videngine.audio_preprocess import preprocess_audio
from videngine.ffmpeg.commands import compress_audio, loudnorm_measure, loudnorm_apply
from videngine.config import load_config

config = load_config()
profile = config.audio.get_profile(device)  # "iphone" or "macbook"

# Step 1: DeepFilterNet3 denoise
atten = profile.denoise_atten_lim_db or None  # 0 = unlimited
preprocess_audio(input_video, denoised_video, working_dir, atten_lim_db=atten)

# Step 2: Compress with profile settings
compress_audio(denoised_video, compressed_video, config.encoding,
    threshold_db=profile.compress_threshold_db,
    ratio=profile.compress_ratio,
    attack_ms=profile.compress_attack_ms,
    release_ms=profile.compress_release_ms,
    knee_db=profile.compress_knee_db,
    makeup_db=profile.compress_makeup_db,
)

# Step 3: Two-pass EBU R128 loudnorm (-16 LUFS)
# Use loudnorm_measure then loudnorm_apply (same pattern as cut stage)
```

Save processed video files to `video-content/production/{slug}/` (replacing the raw video with the audio-processed version).

### 5. Transcribe each video

For each processed video file in production, run Whisper transcription:

```python
from videngine.stages.transcribe import run_transcribe
from videngine.config import load_config

config = load_config()
# working_dir per file: production/{slug}/transcripts/{filename_stem}/
transcript = run_transcribe(processed_video_path, working_dir, config)
```

This produces per file:
- `transcripts/{filename_stem}/transcript.json` — full transcript with word-level timecodes
- `transcripts/{filename_stem}/audio.wav` — extracted audio

After transcription, report per file: word count, duration, language detected.

### 6. Update manifest

Read `video-content/production/{slug}/manifest.md`. Update it by:

**Tick pipeline checkboxes:**
```markdown
- [x] Raw files received ✅ {YYYY-MM-DD HH:MM}
- [x] Audio pre-processing ✅ {YYYY-MM-DD HH:MM}
- [x] Transcription complete ✅ {YYYY-MM-DD HH:MM}
- [ ] Scene matching
- [ ] Beat cuts
- [ ] Beat transcription
- [ ] VAD scoring
- [ ] Delivery comparison
- [ ] Readiness review
```

**Add/update Files section** (after Pipeline Status):
```markdown
## Files
| File | Type | Device | Duration | Size |
|------|------|--------|----------|------|
| {filename} | {desk/mobile/screen-recording} | {iphone/macbook} | {MM:SS} | {size} |
```

Note: file `Type` (desk/mobile/screen-recording) may need manual tagging if it can't be auto-detected. If unsure, set to `unknown` and flag for the user to update.

**Add Audio section:**
```markdown
## Audio Processing
| File | Profile | Denoise | Compress | Loudnorm | Output |
|------|---------|---------|----------|----------|--------|
| {filename} | {iphone/macbook} | ✅ | ✅ | ✅ -16 LUFS | {output_filename} |
```

**Add Transcripts section:**
```markdown
## Transcripts
| File | Transcript | Words | Duration | Language |
|------|-----------|-------|----------|----------|
| {filename} | transcripts/{stem}/transcript.json | {count} | {MM:SS} | {lang} |
```

If `manifest.md` doesn't exist in production, **create it** with the following template (pulling beat info from the sidecar .json if available):

```markdown
# Production Manifest: {slug}

**Slug**: {slug}
**Date**: {YYYY-MM-DD}

## Pipeline Status
- [x] Raw files received ✅ {timestamp}
- [x] Audio pre-processing ✅ {timestamp}
- [x] Transcription complete ✅ {timestamp}
- [ ] Scene matching
- [ ] Beat cuts
- [ ] Beat transcription
- [ ] VAD scoring
- [ ] Delivery comparison
- [ ] Readiness review

## Files
{file table}

## Audio Processing
{audio table}

## Transcripts
{transcript table}

## Beats
{if sidecar exists, build beat table from sidecar beats array with columns: Beat, Name, Source Type, Segment Type, Delivery Energy, VAD Target, Mood, Music Presence, Input File, Takes, Status — all Input File and Takes columns set to "—", all Status set to "⬜ awaiting scene match"}

## Notes
```

Write the updated manifest.

### 7. Summary

Print:
```
## Pre-Processing Complete: {slug}

**Files processed**: {count}
**Devices detected**: {list}
**Audio profiles**: {list}
**Transcription**: {total words} words across {count} files

Pipeline status:
✅ Ingest
✅ Audio pre-processing
✅ Transcription
⬜ Scene matching (next step)

Production directory: video-content/production/{slug}/
Manifest: video-content/production/{slug}/manifest.md
```

$ARGUMENTS
