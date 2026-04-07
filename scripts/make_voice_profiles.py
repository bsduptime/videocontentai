#!/usr/bin/env python3
"""Clean up recordings and extract best Chatterbox voice profile samples.

1. Trim bad takes / false starts using transcript analysis
2. Find the best 12-second segment (densest speech, no long pauses)
3. Convert to Chatterbox format (22050 Hz, mono, 16-bit PCM WAV)
"""

import json
import shutil
import subprocess
from pathlib import Path

RECORDINGS_DIR = Path("voice-profiles/recordings")
SAMPLES_DIR = Path("voice-profiles/samples")
TRANSCRIPTS_FILE = RECORDINGS_DIR / "transcripts.json"

CLIP_DURATION = 12  # seconds

# Manual trim points from transcript review.
# start: first clean speech, end: last clean speech
TRIM = {
    "drive": (7.8, 98.0),  # remove "Drive." label + discard take; remove trailing "Okay. Yeah."
    "drive-wonder": (6.9, 82.1),  # starts mid-sentence "that. I genuinely..."
    "tension": (6.0, 79.9),  # starts mid-sentence "talk about..."
    "tension-vulnerability": (0.0, 86.6),  # clean
    "steady": (0.0, 93.7),  # clean
    "steady-empathy": (0.0, 101.0),  # clean
    "high-intensity-drive": (0.0, 90.0),  # clean
    "reflective-calm": (9.4, 111.8),  # starts mid-sentence "better. That's..."
}


def find_best_segment(
    segments: list[dict], trim_start: float, trim_end: float
) -> tuple[float, float]:
    """Find the 12s window with the most speech (least silence)."""
    # Filter segments to trimmed region
    segs = []
    for s in segments:
        seg_start = max(s["start"], trim_start)
        seg_end = min(s["end"], trim_end)
        if seg_start < seg_end:
            segs.append({"start": seg_start, "end": seg_end})

    if not segs:
        return trim_start, trim_start + CLIP_DURATION

    best_speech = 0
    best_start = trim_start

    # Slide in 0.5s steps
    t = trim_start
    while t + CLIP_DURATION <= trim_end:
        window_end = t + CLIP_DURATION
        speech = 0
        for s in segs:
            overlap_start = max(s["start"], t)
            overlap_end = min(s["end"], window_end)
            if overlap_start < overlap_end:
                speech += overlap_end - overlap_start

        if speech > best_speech:
            best_speech = speech
            best_start = t

        t += 0.5

    return best_start, best_start + CLIP_DURATION


def extract_clip(src: Path, dst: Path, start: float, duration: float):
    """Extract and convert to Chatterbox format."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-ar",
            "22050",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            "-acodec",
            "pcm_s16le",
            str(dst),
        ],
        capture_output=True,
        check=True,
    )


def extract_clean(src: Path, dst: Path, start: float, end: float):
    """Extract full clean region (for keeping as cleaned recording)."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{end - start:.3f}",
            "-ar",
            "22050",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            "-acodec",
            "pcm_s16le",
            str(dst),
        ],
        capture_output=True,
        check=True,
    )


def main():
    with open(TRANSCRIPTS_FILE) as f:
        transcripts = json.load(f)

    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    clean_dir = RECORDINGS_DIR / "clean"
    clean_dir.mkdir(exist_ok=True)

    print(f"Building voice profiles → {SAMPLES_DIR}/\n")

    for name, (trim_start, trim_end) in TRIM.items():
        src = RECORDINGS_DIR / f"{name}.wav"
        if not src.exists():
            print(f"  SKIP {name}: not found")
            continue

        segments = transcripts.get(name, {}).get("segments", [])

        # Save full cleaned recording
        clean_file = clean_dir / f"{name}.wav"
        extract_clean(src, clean_file, trim_start, trim_end)
        clean_dur = trim_end - trim_start

        # Find best 12s segment
        seg_start, seg_end = find_best_segment(segments, trim_start, trim_end)

        # Extract sample
        sample_file = SAMPLES_DIR / f"{name}.wav"
        extract_clip(src, sample_file, seg_start, CLIP_DURATION)

        sample_kb = sample_file.stat().st_size / 1024
        print(
            f"  {name:30s}  clean: {clean_dur:5.1f}s  sample: {seg_start:5.1f}s–{seg_end:5.1f}s  ({sample_kb:.0f}KB)"
        )

    # Default reference = steady
    ref_dir = Path("assets/voice_refs")
    ref_dir.mkdir(parents=True, exist_ok=True)
    steady = SAMPLES_DIR / "steady.wav"
    if steady.exists():
        shutil.copy2(steady, ref_dir / "founder.wav")
        print(f"\nDefault reference: {ref_dir}/founder.wav → steady sample")

    print(f"\nDone. {len(list(SAMPLES_DIR.glob('*.wav')))} profiles in {SAMPLES_DIR}/")
    print(f"     {len(list(clean_dir.glob('*.wav')))} cleaned recordings in {clean_dir}/")


if __name__ == "__main__":
    main()
