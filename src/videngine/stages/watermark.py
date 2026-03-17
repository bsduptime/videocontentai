"""Stage 4: Watermark — apply watermark overlay to raw clips."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import apply_watermark
from ..models import Branding


def run_watermark(
    clip_paths: dict[str, str],
    working_dir: str,
    config: Config,
    branding: Branding | None = None,
) -> dict[str, str]:
    """Apply watermark overlay to each raw clip.

    Uses branding watermark if provided, falls back to config.
    Returns {spec_name: watermarked_path}.
    """
    # Resolve watermark: branding > config
    watermark_file = ""
    if branding and branding.watermark:
        watermark_file = branding.watermark
    else:
        watermark_file = config.video.watermark

    if not watermark_file or not Path(watermark_file).exists():
        # No watermark — pass through
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

        cmd = apply_watermark(
            raw_path,
            watermark_file,
            str(watermarked_path),
            config.encoding,
            position=config.video.watermark_position,
            opacity=config.video.watermark_opacity,
            scale=config.video.watermark_scale,
        )
        _run_ffmpeg(cmd)
        outputs[spec_name] = str(watermarked_path)

    return outputs


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
