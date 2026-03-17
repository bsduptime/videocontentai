"""Pure functions returning FFmpeg command lists."""

from __future__ import annotations

from ..config import EncodingConfig
from .filters import watermark_overlay


def _video_encode_args(encoding: EncodingConfig) -> list[str]:
    """Build video encoding args for either h264_nvmpi or libx264."""
    if encoding.codec == "h264_nvmpi":
        return ["-c:v", "h264_nvmpi"]
    else:
        return ["-c:v", encoding.codec, "-crf", str(encoding.crf)]


def _audio_encode_args(encoding: EncodingConfig) -> list[str]:
    """Build audio encoding args."""
    return ["-c:a", encoding.audio_codec, "-b:a", encoding.audio_bitrate]


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
) -> list[str]:
    """Cut a segment from source using stream copy (no re-encoding)."""
    return [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", input_path,
        "-to", f"{end - start:.3f}",
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        output_path,
    ]


def concat_segments(
    segment_paths: list[str],
    output_path: str,
    concat_list_path: str,
) -> tuple[str, list[str]]:
    """Concatenate segments via concat demuxer with stream copy."""
    lines = [f"file '{p}'" for p in segment_paths]
    concat_content = "\n".join(lines)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_path,
    ]
    return concat_content, cmd


def scale_to_1080p(
    input_path: str,
    output_path: str,
    encoding: EncodingConfig,
    is_landscape: bool = True,
) -> list[str]:
    """Scale to 1080p preserving aspect ratio. Re-encodes video and normalizes audio to stereo."""
    if is_landscape:
        vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
    else:
        vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"

    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf,
        *_video_encode_args(encoding),
        "-ac", "2",  # normalize to stereo
        *_audio_encode_args(encoding),
        output_path,
    ]


def mix_background_music(
    input_path: str,
    music_path: str,
    output_path: str,
    encoding: EncodingConfig,
    music_volume: float = 0.10,
) -> list[str]:
    """Mix background music under the video's speech audio.

    Normalizes both streams to stereo before mixing to avoid channel mismatch.
    Video stream is copied, only audio is re-encoded.
    """
    filter_complex = (
        f"[0:a]aformat=channel_layouts=stereo[speech];"
        f"[1:a]aloop=loop=-1:size=2e+09,afade=t=in:d=2,"
        f"aformat=channel_layouts=stereo,volume={music_volume}[music];"
        f"[speech][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        *_audio_encode_args(encoding),
        output_path,
    ]


def apply_watermark(
    input_path: str,
    watermark_path: str,
    output_path: str,
    encoding: EncodingConfig,
    position: str = "bottom_right",
    opacity: float = 0.3,
    scale: float = 0.08,
) -> list[str]:
    """Apply watermark overlay to a video. Re-encodes video, copies audio."""
    filter_graph = watermark_overlay(position=position, opacity=opacity, scale=scale)

    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", watermark_path,
        "-filter_complex", filter_graph,
        *_video_encode_args(encoding),
        "-c:a", "copy",
        output_path,
    ]


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
        *_video_encode_args(encoding),
        *_audio_encode_args(encoding),
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
        *_video_encode_args(encoding),
        *_audio_encode_args(encoding),
        output_path,
    ]
