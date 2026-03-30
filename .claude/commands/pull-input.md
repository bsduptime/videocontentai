---
description: Pull new recordings from Synology NAS, transcribe, match to scripts, sort into slug directories
allowed-tools: Bash, Read, Write, Glob, Grep
---

Pull new video recordings from the NAS, transcribe them, match against active scripts, and sort into the correct slug directories.

**Arguments**: `$ARGUMENTS` (optional — override NAS source path)

## Constants

```
NAS_HOST=nas
NAS_SOURCE=/volume1/photo/ContentInput/
LOCAL_INBOX=video-content/input/_inbox/
UNSORTED_DIR=video-content/input/_unsorted/
VIDEO_EXTENSIONS=(.mp4 .mov .mkv .avi .webm .m4v)
SCRIPTS_DIR=~/code/content/output/scripts/
TRACKING_FILE=~/code/content/output/tracking.json
MATCH_THRESHOLD=60
```

If `$ARGUMENTS` is provided, use it as the NAS source path instead of the default.

## Step 1: Prepare local directories

```bash
mkdir -p video-content/input/_inbox
mkdir -p video-content/input/_unsorted
```

## Step 2: Pull files from NAS

Pull video files from the Synology NAS via scp. The Jetson has passwordless SSH configured (alias: `ssh nas`). The NAS does not have rsync installed, so use scp.

First, list remote files:

```bash
ssh nas "ls /volume1/photo/ContentInput/" 2>&1
```

Then, for each video file (matching extensions: .mp4 .mov .mkv .avi .webm .m4v, case-insensitive):

```bash
scp "nas:/volume1/photo/ContentInput/FILENAME" video-content/input/_inbox/
ssh nas "rm /volume1/photo/ContentInput/FILENAME"
```

Copy the file first, then delete the remote copy only after a successful transfer.

**If SSH/scp fails** (connection error, path not found):
1. Try discovering the actual path: `ssh nas "ls /volume1/photo/"` and `ssh nas "ls /volume1/Photos/"` and `ssh nas "ls /volume1/homes/*/Photos/"`.
2. If no ContentInput directory exists anywhere, report to the user:
   > "No ContentInput directory found on NAS. Create it at `/volume1/photo/ContentInput/` (Synology Photos shared album) and drop recordings there."
3. Stop here — don't proceed without files.

**If inbox is empty after rsync** (no new files), report "Nothing new on NAS" and exit.

## Step 3: Inventory inbox files

List all video files pulled into the inbox. For each file, run `ffprobe` to get duration, resolution, and recording device:

```bash
cd /home/dbexpertai/code/videocontentai
source .venv/bin/activate
python3 -c "
from src.videngine.ffmpeg.probe import probe, detect_recording_device
import sys, json
f = sys.argv[1]
info = probe(f)
device = detect_recording_device(f)
print(json.dumps({'duration': info.duration, 'width': info.width, 'height': info.height, 'device': device}))
" "VIDEO_PATH"
```

Print a table:

```
| # | File | Duration | Resolution | Device |
|---|------|----------|------------|--------|
| 1 | VID_001.mp4 | 12:34 | 1920x1080 | iphone |
```

## Step 4: Transcribe each video

For each video file in the inbox, transcribe using the videngine Whisper pipeline.

```bash
cd /home/dbexpertai/code/videocontentai
source .venv/bin/activate
python3 -c "
from src.videngine.config import load_config
from src.videngine.stages.transcribe import run_transcribe
import sys
config = load_config()
video = sys.argv[1]
work_dir = sys.argv[2]
t = run_transcribe(video, work_dir, config)
print(f'Segments: {len(t.segments)}, Words: {sum(len(s.words) for s in t.segments)}, Duration: {t.duration_seconds:.1f}s')
" "VIDEO_PATH" "WORK_DIR"
```

For each video file:
- Create a working directory: `video-content/input/_inbox/{video_stem}/`
- Run the transcription command above
- The transcript will be saved as `video-content/input/_inbox/{video_stem}/transcript.json`
- Also copy the transcript next to the video as `video-content/input/_inbox/{video_stem}.transcript.json` (this is the convention that `pre-process` will detect to skip re-transcription)

## Step 5: Gather active scripts for matching

Collect all script content that recordings could match against. Scripts come from two sources:

### 5a: Existing slug directories with scripts

```bash
find video-content/input/ -maxdepth 2 -name "*.md" -not -path "*/_inbox/*" -not -path "*/_unsorted/*"
```

Read each `.md` file found — these are coached scripts already placed in slug dirs.

### 5b: Content repo scripts (tracking.json)

Read `~/code/content/output/tracking.json`. For each entry with `script_status` of "coached" or "approved":
- Read the script file at `~/code/content/{script}` (the path from the tracking entry)
- Read the sidecar at `~/code/content/{script_sidecar}` if it exists
- Extract the slug (the key in tracking.json, e.g. `2026-03-20-anthropic-ai-job-gap`)
- Extract beat names and content from the sidecar JSON

Build a list of candidate scripts:

```
[
  {
    "slug": "2026-03-20-anthropic-ai-job-gap",
    "title": "AI Can Theoretically Do 75% of a Programmer's Job...",
    "brand": "davidk",
    "beats": ["hook text...", "setup text...", "body text..."],
    "full_text": "complete script markdown content"
  },
  ...
]
```

If no scripts are found at all, move everything to `_unsorted/` and report that no scripts are available to match against.

## Step 6: Match transcripts to scripts

For each transcribed video, compare the transcript text against each candidate script.

### Matching strategy

Use **semantic keyword matching** (no external dependencies needed):

1. **Extract key phrases** from each script: bold text (`**phrase**`), beat names, title words, unique technical terms, proper nouns.

2. **For each transcript × script pair**, calculate a match score:
   - Count how many key phrases from the script appear in the transcript (case-insensitive, allow partial word matches for compound terms)
   - Weight bold phrases higher (2x) since they represent coached delivery points
   - Normalize: `score = (weighted_matches / total_weighted_phrases) * 100`

3. **Rank matches** and pick the best:
   - Score >= 60: **auto-match** — high confidence
   - Score 30-59: **tentative match** — flag for review but still sort
   - Score < 30: **no match** — send to `_unsorted/`

4. **Sequential position heuristic**: If multiple videos match the same script, and the script has sequentially numbered beats, check whether transcript timestamps suggest these are different takes of the same script (both match) vs. different scripts. If genuinely the same script, put both into the same slug.

### Important considerations

- David improvises from pointers, so expect paraphrasing. Key technical terms and proper nouns are the strongest signals.
- A single recording session may cover one script or multiple scripts. Match each file independently.
- Short recordings (<2 min) might be individual beat takes rather than full scripts — still try to match.

## Step 7: Sort files into slug directories

For each matched video:

### Matched (score >= 30):

1. Create the slug directory if it doesn't exist: `video-content/input/{slug}/`
2. Move the video file: `video-content/input/_inbox/{file}` → `video-content/input/{slug}/`
3. Move the transcript: `video-content/input/_inbox/{stem}.transcript.json` → `video-content/input/{slug}/`
4. If the script `.md` and sidecar `.json` aren't already in the slug dir, copy them from the content repo

### Unmatched (score < 30):

1. Move to: `video-content/input/_unsorted/{file}`
2. Move transcript alongside: `video-content/input/_unsorted/{stem}.transcript.json`

### Clean up

Remove empty working directories from `_inbox/`:

```bash
find video-content/input/_inbox/ -type d -empty -delete
```

## Step 8: Summary report

Print a summary table:

```
## Pull Input Summary

| # | File | Duration | Match | Score | Destination |
|---|------|----------|-------|-------|-------------|
| 1 | VID_001.mp4 | 12:34 | 2026-03-20-anthropic-ai-job-gap | 78% | input/2026-03-20-anthropic-ai-job-gap/ |
| 2 | VID_002.mp4 | 8:22 | 2026-03-20-non-engineers-building-ai | 65% | input/2026-03-20-non-engineers-building-ai/ |
| 3 | VID_003.mp4 | 3:15 | (no match) | 12% | input/_unsorted/ |

Files pulled: 3
Auto-matched: 2
Unsorted: 1

Next steps:
- Review unsorted files manually
- Run `/check-readiness {slug}` for matched slugs
```

If any matches were tentative (30-59%), add a warning:

```
⚠ Tentative matches (30-59% confidence) — verify these are correct before processing:
  - VID_002.mp4 → 2026-03-20-non-engineers-building-ai (42%)
```

$ARGUMENTS
