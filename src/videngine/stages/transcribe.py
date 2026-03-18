"""Stage 1: Audio extraction + whisper-cli transcription + visual analysis."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import detect_scenes, extract_audio
from ..ffmpeg.probe import probe
from ..models import SceneChange, Transcript, TranscriptSegment, VisualContext, VisualSegment, Word

logger = logging.getLogger(__name__)


def run_transcribe(source_file: str, working_dir: str, config: Config) -> Transcript:
    """Extract audio from video and run whisper-cli for transcription."""
    work = Path(working_dir)
    audio_path = work / "audio.wav"
    transcript_path = work / "transcript.json"

    # Step 1: Extract audio
    cmd = extract_audio(source_file, str(audio_path))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed:\n{result.stderr[-500:]}")

    # Step 2: Get source duration
    info = probe(source_file)

    # Step 3: Run whisper-cli
    whisper_cmd = [
        "whisper-cli",
        "-m", config.whisper.model_path,
        "-l", config.whisper.language,
        "-t", str(config.whisper.threads),
        "--output-json-full",
        "-of", str(work / "whisper_out"),
        "-f", str(audio_path),
    ]
    result = subprocess.run(whisper_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Whisper transcription failed:\n{result.stderr[-500:]}")

    # Step 4: Parse whisper output
    whisper_json_path = work / "whisper_out.json"
    if not whisper_json_path.exists():
        raise FileNotFoundError(f"Whisper output not found at {whisper_json_path}")

    raw = json.loads(whisper_json_path.read_text())
    transcript = _parse_whisper_output(raw, source_file, info.duration)

    # Save parsed transcript
    transcript_path.write_text(transcript.model_dump_json(indent=2))

    return transcript


def _parse_whisper_output(
    raw: dict, source_file: str, duration: float
) -> Transcript:
    """Parse whisper.cpp --output-json-full JSON into our Transcript model."""
    segments = []
    for i, seg in enumerate(raw.get("transcription", [])):
        words = []
        for token in seg.get("tokens", []):
            # whisper.cpp tokens have text, timestamps
            text = token.get("text", "").strip()
            if not text:
                continue
            words.append(Word(
                text=text,
                start=_ts_to_seconds(token.get("offsets", {}).get("from", 0)),
                end=_ts_to_seconds(token.get("offsets", {}).get("to", 0)),
                confidence=token.get("p", 1.0),
            ))

        segments.append(TranscriptSegment(
            id=i,
            start=_ts_to_seconds(seg.get("offsets", {}).get("from", 0)),
            end=_ts_to_seconds(seg.get("offsets", {}).get("to", 0)),
            text=seg.get("text", "").strip(),
            words=words,
        ))

    language = raw.get("result", {}).get("language", "en")

    return Transcript(
        source_file=source_file,
        duration_seconds=duration,
        language=language,
        segments=segments,
    )


def _ts_to_seconds(ms: int) -> float:
    """Convert whisper millisecond timestamp to seconds."""
    return ms / 1000.0


def run_visual_analysis(
    source_file: str,
    working_dir: str,
    score_threshold: float = 0.08,
    dedup_window: float = 2.0,
    frame_interval: float = 30.0,
) -> VisualContext:
    """Run scene change detection on the source video and build visual context."""
    work = Path(working_dir)
    info = probe(source_file)
    duration = info.duration

    # Run scene detection (low threshold to capture subtle transitions)
    scores_path = str(work / "scene_scores.txt")
    cmd = detect_scenes(source_file, scores_path)
    subprocess.run(cmd, capture_output=True, text=True)

    # Parse scores file and post-filter
    raw_changes = _parse_scene_scores(scores_path)
    scene_changes = _filter_and_dedup(raw_changes, score_threshold, dedup_window)

    # Build visual segments from gaps between scene changes
    visual_segments = _build_visual_segments(scene_changes, duration)

    context = VisualContext(
        source_file=source_file,
        duration_seconds=duration,
        frame_interval=frame_interval,
        scene_changes=scene_changes,
        visual_segments=visual_segments,
        total_scene_changes=len(scene_changes),
        avg_scene_duration=duration / max(len(scene_changes) + 1, 1),
    )

    # Save to working dir
    context_path = work / "visual_context.json"
    context_path.write_text(context.model_dump_json(indent=2))
    logger.info("Visual analysis: %d scene changes, avg %.1fs segments", len(scene_changes), context.avg_scene_duration)

    return context


def _parse_scene_scores(scores_path: str) -> list[SceneChange]:
    """Parse metadata=print output file for pts_time and scene_score pairs."""
    changes: list[SceneChange] = []
    pts_pattern = re.compile(r"pts_time:([\d.]+)")
    score_pattern = re.compile(r"lavfi\.scene_score=([\d.]+)")

    try:
        with open(scores_path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return changes

    i = 0
    while i < len(lines) - 1:
        pts_match = pts_pattern.search(lines[i])
        score_match = score_pattern.search(lines[i + 1])
        if pts_match and score_match:
            changes.append(SceneChange(
                timestamp=float(pts_match.group(1)),
                score=float(score_match.group(1)),
            ))
        i += 2

    return changes


def _filter_and_dedup(
    changes: list[SceneChange],
    score_threshold: float,
    dedup_window: float,
) -> list[SceneChange]:
    """Apply score threshold and deduplicate nearby changes."""
    filtered = [c for c in changes if c.score >= score_threshold]
    deduped: list[SceneChange] = []
    for c in filtered:
        if not deduped or c.timestamp - deduped[-1].timestamp > dedup_window:
            deduped.append(c)
        elif c.score > deduped[-1].score:
            deduped[-1] = c
    return deduped


def _build_visual_segments(
    scene_changes: list[SceneChange],
    total_duration: float,
) -> list[VisualSegment]:
    """Build visual segments from gaps between scene changes."""
    if not scene_changes:
        return [VisualSegment(
            start=0.0, end=total_duration, duration=total_duration,
            motion_level="low",
        )]

    segments: list[VisualSegment] = []
    boundaries = [0.0] + [sc.timestamp for sc in scene_changes] + [total_duration]

    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        dur = end - start
        if dur < 0.1:
            continue

        # Infer motion level from scene change scores at boundaries
        scores = []
        if i > 0 and i - 1 < len(scene_changes):
            scores.append(scene_changes[i - 1].score)
        if i < len(scene_changes):
            scores.append(scene_changes[i].score)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        if avg_score > 0.6:
            motion = "high"
        elif avg_score > 0.35:
            motion = "medium"
        else:
            motion = "low"

        segments.append(VisualSegment(
            start=round(start, 3),
            end=round(end, 3),
            duration=round(dur, 3),
            motion_level=motion,
        ))

    return segments
