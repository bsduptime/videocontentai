"""Pure functions returning FFmpeg command lists."""

from __future__ import annotations

from ..config import EncodingConfig
from ..models import VisualEffect

# Font path for text overlays (DejaVu Sans Bold — confirmed present on Jetson)
_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


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
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
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
        "ffmpeg",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        input_path,
        "-to",
        f"{end - start:.3f}",
        "-c",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
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
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_path,
        "-c",
        "copy",
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
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        vf,
        *_video_encode_args(encoding),
        "-ac",
        "2",  # normalize to stereo
        *_audio_encode_args(encoding),
        output_path,
    ]


def compress_audio(
    input_path: str,
    output_path: str,
    encoding: EncodingConfig,
    threshold_db: float = -20.0,
    ratio: float = 3.0,
    attack_ms: float = 5.0,
    release_ms: float = 200.0,
    knee_db: float = 6.0,
    makeup_db: float = 2.0,
) -> list[str]:
    """Apply gentle dynamic compression to speech audio. Video stream-copied.

    Default settings are tuned for broadcast speech: light compression
    that tames peaks and brings up quiet passages slightly, making
    speech easier to understand without sounding over-processed.
    """
    af = (
        f"acompressor=threshold={threshold_db}dB"
        f":ratio={ratio}"
        f":attack={attack_ms}"
        f":release={release_ms}"
        f":knee={knee_db}"
        f":makeup={makeup_db}dB"
    )
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-af",
        af,
        "-c:v",
        "copy",
        *_audio_encode_args(encoding),
        output_path,
    ]


def loudnorm_measure(
    input_path: str,
    target_lufs: float = -16.0,
    true_peak: float = -1.5,
    lra: float = 11.0,
) -> list[str]:
    """Pass 1: measure loudness stats (outputs JSON to stderr)."""
    af = f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}" f":print_format=json"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-af",
        af,
        "-f",
        "null",
        "-",
    ]


def loudnorm_apply(
    input_path: str,
    output_path: str,
    encoding: EncodingConfig,
    target_lufs: float = -16.0,
    true_peak: float = -1.5,
    lra: float = 11.0,
    measured_i: float = -24.0,
    measured_tp: float = -2.0,
    measured_lra: float = 7.0,
    measured_thresh: float = -34.0,
    offset: float = 0.0,
) -> list[str]:
    """Pass 2: apply linear loudness correction. Video stream-copied."""
    af = (
        f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}"
        f":measured_I={measured_i}:measured_TP={measured_tp}"
        f":measured_LRA={measured_lra}:measured_thresh={measured_thresh}"
        f":offset={offset}:linear=true:print_format=summary"
    )
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-af",
        af,
        "-c:v",
        "copy",
        *_audio_encode_args(encoding),
        output_path,
    ]


def detect_scenes(
    input_path: str,
    scores_path: str,
    threshold: float = 0.05,
) -> list[str]:
    """Detect scene changes using select filter + metadata=print for scores.

    Uses a low threshold (0.05) to capture subtle screen recording transitions.
    Post-filtering at 0.08+ with dedup is done in the parsing stage.
    """
    vf = f"select='gt(scene,{threshold})',metadata=print:file={scores_path}"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        vf,
        "-an",
        "-f",
        "null",
        "-",
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
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-i",
        music_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        *_audio_encode_args(encoding),
        output_path,
    ]


def composite_with_matte(
    input_path: str,
    matte_path: str,
    bg_source: str,
    output_path: str,
    encoding: EncodingConfig,
    bg_type: str = "blur",
    solid_color: str = "#00FF00",
) -> list[str]:
    """Composite foreground onto a new background using an alpha matte video.

    Inputs:
      - input_path: original video (foreground + audio)
      - matte_path: grayscale alpha matte video (white = keep, black = replace)
      - bg_source: background video/image path (unused for solid color)
      - bg_type: "blur" (bg_source is blurred video), "image", or "solid"
      - solid_color: hex color for solid background

    The matte is used to blend: output = fg * alpha + bg * (1 - alpha).
    Audio is copied from the original.
    """
    if bg_type == "solid":
        # Generate solid color background using color source
        filter_complex = (
            f"color=c={solid_color}:s=1920x1080:r=30[bg];"
            f"[1:v]format=gray[matte];"
            f"[0:v][matte]alphamerge[fg];"
            f"[bg][fg]overlay=0:0:shortest=1[out]"
        )
        return [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-i",
            matte_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-map",
            "0:a",
            *_video_encode_args(encoding),
            "-c:a",
            "copy",
            output_path,
        ]

    # blur or image — bg_source is a file
    if bg_type == "image":
        # Static image: loop it to match video length, scale to match
        filter_complex = (
            "[1:v]scale=iw:ih,format=rgb24,loop=-1:size=1:start=0,"
            "setpts=N/FRAME_RATE/TB,scale=iw:ih[bg];"
            "[2:v]format=gray[matte];"
            "[0:v][matte]alphamerge[fg];"
            "[bg][fg]overlay=0:0:shortest=1[out]"
        )
    else:
        # Video background (blur, etc.)
        filter_complex = (
            "[2:v]format=gray[matte];"
            "[0:v][matte]alphamerge[fg];"
            "[1:v][fg]overlay=0:0:shortest=1[out]"
        )
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,  # 0: original (foreground + audio)
        "-i",
        bg_source,  # 1: background (image or video)
        "-i",
        matte_path,  # 2: alpha matte
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-map",
        "0:a",
        *_video_encode_args(encoding),
        "-c:a",
        "copy",
        output_path,
    ]


def apply_watermark(
    input_path: str,
    watermark_path: str,
    output_path: str,
    encoding: EncodingConfig,
    scale: float = 0.40,
    opacity: float = 0.9,
    x: str = "W-w-65",
    y: str = "H-h-40",
) -> list[str]:
    """Apply watermark overlay to a video. Re-encodes video, copies audio."""
    filter_graph = (
        f"[1:v]scale=iw*{scale}:-1,format=rgba,"
        f"colorchannelmixer=aa={opacity}[wm];"
        f"[0:v][wm]overlay={x}:{y}"
    )

    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-i",
        watermark_path,
        "-filter_complex",
        filter_graph,
        *_video_encode_args(encoding),
        "-c:a",
        "copy",
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
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        vf,
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
    vf = f"crop=ih*{target_width}/{target_height}:ih," f"scale={target_width}:{target_height}"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        vf,
        *_video_encode_args(encoding),
        *_audio_encode_args(encoding),
        output_path,
    ]


def _escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    # Order matters: backslash first, then the rest
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace(";", "\\;")
    return text


def _build_zoompan(effect: VisualEffect, fps: int = 60) -> str:
    """Build a zoompan filter for a Ken Burns zoom effect within a time window.

    Uses zoompan with d=1 (one output per input frame) so it acts as a
    per-frame crop+scale. Outside the effect window, zoom=1 (no zoom).
    During the effect, zoom ramps from 1.0 to zoom_factor.

    The zoompan filter uses 'on' (output frame number) for expressions.
    We convert time-based start/end to frame numbers using the given fps.
    """
    zf = effect.zoom_factor
    zx, zy = effect.zoom_target_x, effect.zoom_target_y

    # Convert time to frame numbers
    f_start = int(effect.start * fps)
    f_end = int(effect.end * fps)
    f_dur = f_end - f_start

    # z: zoom level. 1.0 outside window, ramps 1.0→zf during window, holds zf after
    # progress = (on - f_start) / f_dur, clamped 0→1
    z_expr = (
        f"if(lt(on,{f_start}),1," f"if(lt(on,{f_end}),1+{zf - 1}*(on-{f_start})/{f_dur}," f"1))"
    )

    # x/y: pan toward target as zoom increases
    # zoompan x/y are in input pixel coordinates (top-left of the crop window)
    # Default center: x = iw/2 - iw/zoom/2, y = ih/2 - ih/zoom/2
    # Target: x = target_x - iw/zoom/2, y = target_y - ih/zoom/2
    # Lerp from center to target using same progress
    x_center = "iw/2-iw/zoom/2"
    y_center = "ih/2-ih/zoom/2"
    x_target = f"({zx})-iw/zoom/2"
    y_target = f"({zy})-ih/zoom/2"

    x_expr = (
        f"if(lt(on,{f_start}),{x_center},"
        f"if(lt(on,{f_end}),"
        f"{x_center}+({x_target}-({x_center}))*(on-{f_start})/{f_dur},"
        f"{x_center}))"
    )
    y_expr = (
        f"if(lt(on,{f_start}),{y_center},"
        f"if(lt(on,{f_end}),"
        f"{y_center}+({y_target}-({y_center}))*(on-{f_start})/{f_dur},"
        f"{y_center}))"
    )

    return f"zoompan=z='{z_expr}'" f":x='{x_expr}'" f":y='{y_expr}'" f":d=1:s=1920x1080:fps={fps}"


def _build_drawtext(effect: VisualEffect) -> str:
    """Build a drawtext filter string for a text overlay effect."""
    text = _escape_drawtext(effect.overlay_text)
    return (
        f"drawtext=text='{text}'"
        f":enable='between(t,{effect.start},{effect.end})'"
        f":fontfile={_FONT_PATH}"
        f":fontsize=48"
        f":fontcolor=white"
        f":borderw=2:bordercolor=black"
        f":x=(w-text_w)/2:y=h-text_h-100"
    )


def apply_watermark_with_effects(
    input_path: str,
    watermark_path: str,
    output_path: str,
    encoding: EncodingConfig,
    effects: list[VisualEffect],
    scale: float = 0.40,
    opacity: float = 0.9,
    x: str = "W-w-65",
    y: str = "H-h-40",
) -> list[str]:
    """Apply watermark + visual effects (zoom, text overlays) in a single re-encode.

    Combines crop (zoom), drawtext (text), scale, and watermark overlay into one
    filter_complex so we only encode once with h264_nvmpi.
    """
    # Separate effects by type
    zooms = [e for e in effects if e.effect_type == "zoom"]
    texts = [e for e in effects if e.effect_type == "text_overlay"]

    # Build video filter chain on [0:v]
    video_filters: list[str] = []

    if zooms:
        # zoompan handles zoom + scale to 1920x1080 in one step
        # Only first zoom is used (zoompan is a single-instance filter)
        video_filters.append(_build_zoompan(zooms[0]))
    else:
        # No zoom — just scale to 1920x1080
        video_filters.append("scale=1920:1080")

    # Add text overlays (drawtext uses 't' which works correctly)
    for text_effect in texts:
        video_filters.append(_build_drawtext(text_effect))

    video_chain = ",".join(video_filters)

    filter_graph = (
        f"[0:v]{video_chain}[main];"
        f"[1:v]scale=iw*{scale}:-1,format=rgba,"
        f"colorchannelmixer=aa={opacity}[wm];"
        f"[main][wm]overlay={x}:{y}"
    )

    return [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-i",
        watermark_path,
        "-filter_complex",
        filter_graph,
        *_video_encode_args(encoding),
        "-c:a",
        "copy",
        output_path,
    ]
