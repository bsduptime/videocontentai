"""Stage 4: Watermark — apply watermark overlay to raw clips."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import apply_watermark
from ..ffmpeg.probe import probe
from ..models import Branding, WatermarkPosition


def run_watermark(
    clip_paths: dict[str, str],
    working_dir: str,
    config: Config,
    branding: Branding | None = None,
) -> dict[str, str]:
    """Apply watermark overlay to each raw clip.

    Uses branding watermark and position settings if provided.
    Returns {spec_name: watermarked_path}.
    """
    watermark_file = ""
    if branding and branding.watermark:
        watermark_file = branding.watermark

    if not watermark_file or not Path(watermark_file).exists():
        outputs: dict[str, str] = {}
        for spec_name, raw_path in clip_paths.items():
            clip_dir = Path(raw_path).parent
            watermarked_path = clip_dir / "watermarked.mp4"
            shutil.copy2(raw_path, watermarked_path)
            outputs[spec_name] = str(watermarked_path)
        return outputs

    outputs = {}
    for spec_name, raw_path in clip_paths.items():
        clip_dir = Path(raw_path).parent
        watermarked_path = clip_dir / "watermarked.mp4"

        # Pick watermark position based on clip aspect ratio
        clip_info = probe(raw_path)
        is_landscape = clip_info.width >= clip_info.height
        wm_pos = _get_watermark_position(branding, is_landscape)

        cmd = apply_watermark(
            raw_path,
            watermark_file,
            str(watermarked_path),
            config.encoding,
            scale=wm_pos.scale,
            opacity=wm_pos.opacity,
            x=wm_pos.x,
            y=wm_pos.y,
        )
        _run_ffmpeg(cmd)
        outputs[spec_name] = str(watermarked_path)

    return outputs


def _get_watermark_position(branding: Branding, is_landscape: bool) -> WatermarkPosition:
    """Get watermark position for the given aspect ratio."""
    if is_landscape:
        return branding.watermark_16x9
    else:
        return branding.watermark_9x16


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
