"""Stage 4: Watermark + Visual Effects — apply watermark, zoom, and text overlays."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import apply_watermark, apply_watermark_with_effects
from ..ffmpeg.probe import probe
from ..models import Branding, CutPlan, VisualEffect, WatermarkPosition

logger = logging.getLogger(__name__)


def run_watermark(
    clip_paths: dict[str, str],
    working_dir: str,
    config: Config,
    branding: Branding | None = None,
    cut_plans: list[CutPlan] | None = None,
) -> dict[str, str]:
    """Apply watermark overlay + visual effects to each raw clip.

    When a cut plan has visual_effects, merges zoom/text into the watermark
    re-encode pass (single h264_nvmpi encode). Falls back to watermark-only
    when no effects are present.

    Returns {spec_name: watermarked_path}.
    """
    # Index cut plans by spec name for effect lookup
    plans_by_name: dict[str, CutPlan] = {}
    if cut_plans:
        for plan in cut_plans:
            plans_by_name[plan.spec_name] = plan

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

        # Check for visual effects in the cut plan
        effects: list[VisualEffect] = []
        plan = plans_by_name.get(spec_name)
        if plan and plan.visual_effects:
            effects = plan.visual_effects

        if effects:
            logger.info("Watermark + %d visual effects for %s", len(effects), spec_name)
            cmd = apply_watermark_with_effects(
                raw_path,
                watermark_file,
                str(watermarked_path),
                config.encoding,
                effects=effects,
                scale=wm_pos.scale,
                opacity=wm_pos.opacity,
                x=wm_pos.x,
                y=wm_pos.y,
            )
        else:
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
