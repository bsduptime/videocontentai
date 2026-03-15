"""Stage 1: Audio extraction + whisper-cli transcription."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import extract_audio
from ..ffmpeg.probe import probe
from ..models import Transcript, TranscriptSegment, Word


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
