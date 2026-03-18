---
name: cut
description: Process videos in source/to_cut/ through the multi-cut pipeline
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob, Grep
---

Process all videos waiting in `source/to_cut/` through the multi-cut pipeline. You ARE the AI editor — do the analysis yourself, then run FFmpeg for the mechanical steps.

## Directory convention

- `source/to_cut/dbexpertai/` — dbexpertai brand (tutorials, screen recordings)
- `source/to_cut/founder/` — founder personal brand (talking-head, opinions)
- `source/in_progress/` — files currently being processed
- `source/done/` — completed source files

Brand is detected from the subdirectory. Aspect ratio is detected from the video file.

## Brand → spec file mapping

| Brand | Landscape (16:9) | Portrait (9:16) |
|-------|-----------------|-----------------|
| dbexpertai | `config/cut_specs/landscape-dbexpertai.json` | `config/cut_specs/portrait-dbexpertai.json` |
| founder | `config/cut_specs/landscape-founder.json` | `config/cut_specs/portrait-founder.json` |

## For each video file, execute these steps:

### 1. Setup
- Detect brand from subdirectory (default: dbexpertai)
- Move file from `source/to_cut/{brand}/` to `source/in_progress/`
- Probe the video with ffprobe to get aspect ratio, duration, resolution
- Load the matching cut spec JSON file
- Create a job directory: `~/.videngine/jobs/{filename}-{timestamp}/`
- Create subdirectories: `cut_plans/`, `clips/`

### 2. Transcribe
- Run: `ffmpeg -y -i {source} -vn -acodec pcm_s16le -ar 16000 -ac 1 {job_dir}/audio.wav`
- Run whisper-cli with the model at `~/.videngine/models/ggml-large-v3-turbo.bin`:
  ```
  whisper-cli -m ~/.videngine/models/ggml-large-v3-turbo.bin -f {job_dir}/audio.wav --output-json-full -of {job_dir}/transcript -l en
  ```
- Parse the whisper JSON output into a clean transcript

### 3. Analyze (YOU do this — no API call)
Read the transcript, the cut spec file, and `visual_context.json` (scene changes from keyframe analysis). Use visual context to identify screen recording segments, natural cut points, and content type transitions. Scene changes = natural cut points; low-motion = likely screen content (keep intact). Then for each segment:

**Phase 1 — Score every segment:**
- Score 1-10 on editorial quality (hook potential, information density, emotional resonance, delivery)
- Tag with: `strong_hook`, `high_density`, `emotional`, `funny`, `contrarian`, `technical`, `story`, `filler`, `repetitive`
- Identify 3-5 overall themes
- Recommend hook candidate segment IDs
- Write to `{job_dir}/cut_plans/_analysis.json`

**Phase 2 — Create cut plans for each spec in the cuts array:**
For each cut spec, select the best segments that fit the duration range and editorial lens:
- Use word-level timestamps. Add 0.1s pre-padding, 0.3s post-padding
- Never cut mid-sentence
- For hook specs: pick a single attention-grabbing moment, leave narration empty
- For non-hook specs: write intro narration (1-2 sentences, first person) and outro narration
- Pick a `mood` from the spec's `mood_options` based on the emotional arc of the segments you selected (drive=confident/upbeat, tension=urgent/dramatic, steady=calm/background)
- List dropped segments with reasons for any scored 5+ that weren't included
- Write to `{job_dir}/cut_plans/{spec_name}.json`

### 4. Cut segments (FFmpeg — stream copy, no re-encoding)
For each cut plan:
```bash
# Cut each segment (stream copy — fast)
ffmpeg -y -ss {start} -i {source} -to {duration} -c copy -avoid_negative_ts make_zero {seg_output}

# Concat all segments (stream copy)
# Write concat list file, then:
ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy {clip_dir}/concat.mp4
```

### 4.5. Loudness normalize (EBU R128, two-pass)
After scaling to 1080p (if needed), normalize audio loudness to -16 LUFS using two-pass FFmpeg `loudnorm`:
- Pass 1 measures integrated loudness, true peak, and loudness range
- Pass 2 applies linear correction with video stream-copied
- Records measurements to `{job_dir}/loudness_log.json` alongside `music_log.json`
- ~2s per clip, negligible overhead

### 5. Mix background music
- Each cut plan has a `mood` field you chose during analysis — read it from the plan JSON
- Read `config/cut_specs/moods.json` to find the audio files for that mood (3 moods, 3 variants each)
- Randomly pick one variant from `assets/music/` (e.g. drive-1.wav, drive-2.wav, drive-3.wav)
- Log which file was used per cut to `{job_dir}/music_log.json` for easy review
- Mix under speech at 10% volume. Normalize both streams to stereo before mixing. Video stream copy, only audio re-encodes:
```bash
ffmpeg -y -i scaled.mp4 -i {music_file} \
  -filter_complex "[0:a]aformat=channel_layouts=stereo[speech];[1:a]aloop=loop=-1:size=2e+09,afade=t=in:d=2,aformat=channel_layouts=stereo,volume=0.10[music];[speech][music]amix=inputs=2:duration=first:dropout_transition=2[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k {clip_dir}/with_music.mp4
```

### 6. Apply watermark
- Use the watermark from the spec file's `branding.watermark` field
- Read position from `branding.watermark_16x9` or `branding.watermark_9x16` based on aspect ratio
- Each has: `scale`, `opacity`, `x`, `y` (ffmpeg overlay expressions)
- Re-encodes video with h264_nvmpi (filter needed), copies audio:
```bash
ffmpeg -y -i with_music.mp4 -i {watermark} \
  -filter_complex "[1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm];[0:v][wm]overlay={x}:{y}" \
  -c:v h264_nvmpi -c:a copy {clip_dir}/watermarked.mp4
```

### 7. Add intro/outro
- Use branding from the spec file: pick `intro_16x9`/`intro_9x16` and `outro_16x9`/`outro_9x16` based on aspect ratio
- Skip for hook clips
- Concat with stream copy (templates are pre-cropped to match resolution):
```bash
ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy {clip_dir}/with_intro_outro.mp4
```

### 8. Prepend hook
- Check each cut spec's `prepend_hook` field
- For cuts with `prepend_hook: true`, concat hook + clip (stream copy)
- For others (including the hook itself), just copy to final
```bash
ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy {clip_dir}/final.mp4
```

### 9. Finish up
- Move source file from `source/in_progress/` to `source/done/`
- Report all final clips with durations:
```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 {clip_dir}/final.mp4
```

## Arguments
Any text after `/cut` is passed as $ARGUMENTS. Supported:
- `--review` — pause after step 3 so user can review cut plans before proceeding
- `--dry-run` — show what would happen through step 3 only (analysis), don't run FFmpeg
