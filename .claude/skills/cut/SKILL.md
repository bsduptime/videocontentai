---
name: cut
description: Process videos in video-content/input/ through the multi-cut pipeline
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob, Grep
---

Process all videos waiting in `video-content/input/` through the multi-cut pipeline. You ARE the AI editor — do the analysis yourself, then run FFmpeg for the mechanical steps.

## Directory convention

- `video-content/input/{slug}/` — drop video files here for processing
- `video-content/production/` — files currently being processed
- `video-content/output/` — completed output

Brand is detected from the subdirectory. Aspect ratio is detected from the video file.

## Brand → spec file mapping

| Brand | Landscape (16:9) | Portrait (9:16) |
|-------|-----------------|-----------------|
| dbexpertai | `config/cut_specs/landscape-dbexpertai.json` | `config/cut_specs/portrait-dbexpertai.json` |
| founder | `config/cut_specs/landscape-founder.json` | `config/cut_specs/portrait-founder.json` |

## For each video file, execute these steps:

### 1. Setup
- Detect brand from subdirectory (default: dbexpertai)
- Move file from `video-content/input/{slug}/` to `video-content/production/`
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

### 2.5. Visual context (content-based scene detection)
Detect scene changes using FFmpeg's pixel-difference `scene` filter with `metadata=print` to get scores (not keyframe/I-frame gaps — those are codec-level and miss UI transitions in screen recordings):
```bash
ffmpeg -y -i {source} \
  -vf "select='gt(scene,0.05)',metadata=print:file={job_dir}/scene_scores.txt" \
  -an -f null -
```
Use threshold `0.05` to capture all candidates including subtle screen recording transitions. Then post-filter:
- Parse `scene_scores.txt` for `pts_time` and `lavfi.scene_score` pairs
- Apply score threshold `0.08` (keeps real transitions, drops noise)
- Deduplicate: merge changes within dedup window (see below), keeping highest score
- Build `{job_dir}/visual_context.json`

Motion level is inferred from boundary scores: >0.6 = high, >0.35 = medium, ≤0.35 = low.

**Adaptive frame sampling** — interval and dedup window depend on `source.format` from the cut spec:

| source.format contains | Frame interval | Dedup window |
|------------------------|---------------|-------------|
| "screen" (screen recording) | **10s** | 1.5s |
| "talking" (talking-head) | **30s** | 2.0s |
| default / other | **15s** | 2.0s |

Then extract representative frames for visual analysis:
```bash
# Extract frames at scene changes + every {interval}s, scaled to 1280w for vision
ffmpeg -y -ss {timestamp} -i {source} -vframes 1 -q:v 3 -vf "scale=1280:-1" {job_dir}/frames/frame_{MM}m{SS}s.jpg
```
- Merge scene change timestamps with {interval}s intervals, deduplicate within dedup window
- Save timestamps to `{job_dir}/frames/frame_times.json`
- Record `frame_interval` in `visual_context.json`

### 2.6. Describe frames (YOU do this — read each frame image)
Read each extracted frame with the Read tool and write a description for each to `visual_context.json` under `frame_descriptions[]`. For each frame, describe:
- `screen`: what page/view is shown (e.g. "Fleet Overview dashboard", "SQL query modal")
- `visible_elements`: UI elements, text, data visible on screen
- `region_of_interest`: where the action/focus is (e.g. "right panel", "center modal")
- `visual_density`: low/medium/high/very high — how busy the screen is
- `overlay_opportunity`: boolean — is there enough empty space to overlay text/titles?
- `zoom_candidate`: string or null — if small but important UI text/stats could benefit from a zoom-in effect during editing

These descriptions let you make informed editing decisions:
- **overlay_opportunity = true** → candidate for text overlays (highlight sentences, stats, titles)
- **zoom_candidate** → consider pan-and-zoom effect to call attention to small UI elements
- **visual_density = very high** → keep these segments intact, don't overlay or cut mid-screen
- Match `region_of_interest` against transcript — if speaker says "look at this" while ROI is on a specific panel, that's a zoom-in moment

### 3. Analyze (YOU do this — no API call)
Read the transcript, the cut spec file, and `visual_context.json` (content-based scene changes). Use visual context to identify screen recording segments, natural cut points, and content type transitions. Scene changes = natural cut points; low-motion = likely screen content (keep intact). Then for each segment:

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
- Pick a `mood` from the spec's `mood_options` based on the emotional arc of the segments you selected (drive=confident/upbeat, steady=calm/background). For urgent/dramatic segments, use silence (no music) — delivery carries the energy.
- List dropped segments with reasons for any scored 5+ that weren't included
- Write to `{job_dir}/cut_plans/{spec_name}.json`

**Phase 3 — Plan visual effects per cut:**
After creating each cut plan, determine visual effects for segments within the cut. Write a `visual_effects[]` array into the cut plan JSON. Each effect has: `effect_type`, `start`, `end` (times relative to the assembled clip, not the source), and type-specific fields.

**Zoom effects** (Ken Burns via animated crop+scale):
- Trigger: `zoom_candidate` is set in a frame description that falls within a selected segment
- Map the frame's `region_of_interest` to FFmpeg coordinates using the ROI table:

| ROI description | zoom_target_x | zoom_target_y |
|----------------|---------------|---------------|
| "right panel/side" | `iw*2/3` | `ih/2` |
| "left panel/side" | `iw/3` | `ih/2` |
| "center" | `iw/2` | `ih/2` |
| "top/header" | `iw/2` | `ih/4` |
| "bottom" | `iw/2` | `ih*3/4` |

- `zoom_factor`: 1.3 (gentle), max 10s duration per zoom
- Never apply zoom on hook clips

**Text overlay effects** (drawtext):
- Trigger: `overlay_opportunity == true` in a frame AND cut plan has narration or a key quote
- Use the narration sentence or a short stat/quote as `overlay_text`
- Position: lower third, white text, black border
- Never apply on hook clips

**Rules:**
- Max 3 effects per cut
- Never overlap a zoom and text on the same time range
- If no effects are appropriate, leave `visual_effects` as an empty array

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

### 6. Apply watermark + visual effects
- Use the watermark from the spec file's `branding.watermark` field
- Read position from `branding.watermark_16x9` or `branding.watermark_9x16` based on aspect ratio
- Each has: `scale`, `opacity`, `x`, `y` (ffmpeg overlay expressions)
- Load `visual_effects[]` from the cut plan for this clip

**When visual effects exist** — merge zoom/text into the watermark re-encode (single h264_nvmpi pass):
```bash
ffmpeg -y -i with_music.mp4 -i {watermark} \
  -filter_complex "
    [0:v]crop=w='if(between(t,{z_start},{z_end}),iw-(iw-iw/{zf})*(t-{z_start})/({z_end}-{z_start}),iw)':h='...':x='...':y='...',
    scale=1920:1080,
    drawtext=text='{text}':enable='between(t,{t_start},{t_end})':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=48:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-text_h-100[main];
    [1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm];
    [main][wm]overlay={x}:{y}
  " \
  -c:v h264_nvmpi -c:a copy {clip_dir}/watermarked.mp4
```

**When no effects** — watermark only (unchanged):
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
- Move source file from `video-content/production/` to `video-content/output/`
- Report all final clips with durations:
```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 {clip_dir}/final.mp4
```

## Arguments
Any text after `/cut` is passed as $ARGUMENTS. Supported:
- `--review` — pause after step 3 so user can review cut plans before proceeding
- `--dry-run` — show what would happen through step 3 only (analysis), don't run FFmpeg
