"""ffprobe wrapper for extracting media information."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass
class MediaInfo:
    duration: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str | None
    audio_sample_rate: int | None
    has_audio: bool


def probe(file_path: str) -> MediaInfo:
    """Run ffprobe and return structured media info."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream["codec_type"] == "video" and video_stream is None:
            video_stream = stream
        elif stream["codec_type"] == "audio" and audio_stream is None:
            audio_stream = stream

    if video_stream is None:
        raise ValueError(f"No video stream found in {file_path}")

    # Parse FPS from r_frame_rate (e.g. "30/1" or "30000/1001")
    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

    duration = float(data.get("format", {}).get("duration", 0))

    return MediaInfo(
        duration=duration,
        width=int(video_stream["width"]),
        height=int(video_stream["height"]),
        fps=fps,
        video_codec=video_stream["codec_name"],
        audio_codec=audio_stream["codec_name"] if audio_stream else None,
        audio_sample_rate=int(audio_stream["sample_rate"]) if audio_stream else None,
        has_audio=audio_stream is not None,
    )
