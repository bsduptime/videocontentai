---
description: Replace video background using RVM segmentation — composite onto image or video background
allowed-tools: Bash, Read, Glob, Grep
---

Replace the background in a talking-head video using RVM (Robust Video Matting) and composite the subject onto a new background image or video.

**Arguments**: `$ARGUMENTS`

Expected format: `<input_video> <background> [output_path]`

- `input_video` — path to the source video (mp4, mov, mkv)
- `background` — path to the replacement background (image: png/jpg/webp, or video: mp4/mov/mkv)
- `output_path` — (optional) output path. Defaults to `{input_dir}/{input_name}_bg_replaced.mp4`

## Step 1: Parse and validate arguments

Parse `$ARGUMENTS` into `input_video`, `background`, and optionally `output_path`.

If fewer than 2 arguments, report usage and stop:
```
Usage: /replace-background <input_video> <background> [output_path]

Examples:
  /replace-background clip.mp4 studio.png
  /replace-background clip.mp4 loop_bg.mp4 output/final.mp4
```

Validate both input files exist. If either is missing, report and stop.

Detect the background type from the file extension:
- Image: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp` → `bg_type = "image"`
- Video: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm` → `bg_type = "video"`

If the extension doesn't match either, report "Unsupported background format" and stop.

If no `output_path` given, derive it:
```python
output_path = f"{input_dir}/{input_stem}_bg_replaced.mp4"
```

## Step 2: Probe input video

```bash
ffprobe -v quiet -show_entries stream=width,height,r_frame_rate,codec_name -show_entries format=duration -of json <input_video>
```

Print a summary:
```
Input:      {input_video}
Resolution: {width}x{height}
Duration:   {duration}s
FPS:        {fps}
Background: {background} ({bg_type})
Output:     {output_path}
```

Calculate estimated time: `frames = duration * fps`, roughly `frames / 2.5` seconds on CPU.
Print: `Estimated time: ~{est}s ({frames} frames at ~2.5 fps on CPU)`

## Step 3: Ensure RVM model

Check if the RVM ONNX model exists:

```bash
ls ~/.videngine/models/rvm_mobilenetv3_fp32.onnx
```

If missing, download it:
```bash
mkdir -p ~/.videngine/models
wget -q -O ~/.videngine/models/rvm_mobilenetv3_fp32.onnx \
  "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
```

## Step 4: Generate alpha matte

Create a working directory next to the output file:
```python
work_dir = f"{output_dir}/.bg_work_{input_stem}"
```

Run the matte generation using the pipeline module:

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from videngine.stages.background import _generate_alpha_matte
from videngine.config import EncodingConfig
_generate_alpha_matte(
    '$INPUT_VIDEO',
    '$WORK_DIR/alpha_matte.mp4',
    '$HOME/.videngine/models/rvm_mobilenetv3_fp32.onnx',
    EncodingConfig(),
    downsample_ratio=0.25,
)
print('Matte complete')
"
```

If it fails, report the error and stop.

## Step 5: Prepare background (if video)

If `bg_type` is "video", probe the background video to check its resolution matches the input. If the resolutions differ, scale the background to match:

```bash
ffmpeg -y -i <background> -vf "scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black" -c:v libx264 -crf 18 -an {work_dir}/bg_scaled.mp4
```

Use the scaled version as the background source. If resolutions already match, use the original.

For images, no preprocessing is needed — FFmpeg handles scaling in the filter.

## Step 6: Composite

Build and run the FFmpeg composite command based on background type.

**For image backgrounds:**
```bash
ffmpeg -y \
  -i <input_video> \
  -i <background> \
  -i {work_dir}/alpha_matte.mp4 \
  -filter_complex "[1:v]scale={width}:{height},format=rgb24,loop=-1:size=1:start=0,setpts=N/FRAME_RATE/TB[bg];[2:v]format=gray[matte];[0:v][matte]alphamerge[fg];[bg][fg]overlay=0:0:shortest=1[out]" \
  -map "[out]" -map "0:a" \
  -c:v libx264 -crf 20 -c:a copy \
  <output_path>
```

**For video backgrounds:**
```bash
ffmpeg -y \
  -i <input_video> \
  -i <bg_source> \
  -i {work_dir}/alpha_matte.mp4 \
  -filter_complex "[2:v]format=gray[matte];[0:v][matte]alphamerge[fg];[1:v][fg]overlay=0:0:shortest=1[out]" \
  -map "[out]" -map "0:a" \
  -c:v libx264 -crf 20 -c:a copy \
  <output_path>
```

If FFmpeg fails, report the error and stop.

## Step 7: Verify and report

Probe the output:
```bash
ffprobe -v quiet -show_entries format=duration,size -show_entries stream=width,height -of default=noprint_wrappers=1 <output_path>
```

Clean up work directory:
```bash
rm -rf {work_dir}
```

Print summary:
```
## Background Replacement Complete

Input:      {input_video}
Background: {background} ({bg_type})
Output:     {output_path}
Resolution: {width}x{height}
Duration:   {duration}s
File size:  {size_mb} MB
```

If the Jetson is on the LAN, also print a quick-view link:
```
Quick view: http://{lan_ip}:8000/{output_filename}
```

$ARGUMENTS
