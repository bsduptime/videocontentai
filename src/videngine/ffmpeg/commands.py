"""Pure functions returning FFmpeg command lists."""

from __future__ import annotations

from ..config import EncodingConfig


def extract_audio(input_path: str, output_path: str) -> list[str]:
    """Extract audio as 16kHz mono WAV for whisper."""
    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path,
    ]


def cut_segment(
    input_path: str,
    output_path: str,
    start: float,
    end: float,
    encoding: EncodingConfig,
) -> list[str]:
    """Cut a segment from the source video with re-encoding for frame accuracy."""
    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-c:v", encoding.codec,
        "-crf", str(encoding.crf),
        "-c:a", encoding.audio_codec,
        "-b:a", encoding.audio_bitrate,
        output_path,
    ]


def concat_segments(
    segment_paths: list[str],
    output_path: str,
    concat_list_path: str,
    encoding: EncodingConfig,
) -> tuple[str, list[str]]:
    """Concatenate segments via concat demuxer.

    Returns (concat_list_content, ffmpeg_command).
    """
    # Build concat list file content
    lines = [f"file '{p}'" for p in segment_paths]
    concat_content = "\n".join(lines)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c:v", encoding.codec,
        "-crf", str(encoding.crf),
        "-c:a", encoding.audio_codec,
        "-b:a", encoding.audio_bitrate,
        output_path,
    ]
    return concat_content, cmd


def scale_and_pad(
    input_path: str,
    output_path: str,
    target_width: int,
    target_height: int,
    encoding: EncodingConfig,
) -> list[str]:
    """Scale video to fit within target dimensions, padding if needed."""
    vf = (
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black"
    )
    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf,
        "-c:v", encoding.codec,
        "-crf", str(encoding.crf),
        "-c:a", encoding.audio_codec,
        "-b:a", encoding.audio_bitrate,
        output_path,
    ]


def center_crop(
    input_path: str,
    output_path: str,
    target_width: int,
    target_height: int,
    encoding: EncodingConfig,
) -> list[str]:
    """Center crop video to target aspect ratio."""
    vf = (
        f"crop=ih*{target_width}/{target_height}:ih,"
        f"scale={target_width}:{target_height}"
    )
    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf,
        "-c:v", encoding.codec,
        "-crf", str(encoding.crf),
        "-c:a", encoding.audio_codec,
        "-b:a", encoding.audio_bitrate,
        output_path,
    ]
