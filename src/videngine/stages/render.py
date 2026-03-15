"""Stage 5: Multi-format rendering (16:9, 9:16, 4:5)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import center_crop, scale_and_pad
from ..models import EditDecision

RATIO_SPECS = {
    "16x9": (1920, 1080),
    "9x16": (1080, 1920),
    "4x5": (1080, 1350),
}


def run_render(
    assembled_path: str,
    working_dir: str,
    config: Config,
    ratios: list[str] | None = None,
) -> dict[str, str]:
    """Render the assembled video into multiple aspect ratios.

    Returns dict of ratio → output path.
    """
    work = Path(working_dir)
    requested = ratios or ["16x9"]
    outputs: dict[str, str] = {}

    for ratio in requested:
        if ratio not in RATIO_SPECS:
            raise ValueError(f"Unknown ratio: {ratio}. Valid: {list(RATIO_SPECS)}")

        target_w, target_h = RATIO_SPECS[ratio]
        out_path = str(work / f"final_{ratio}.mp4")

        if ratio == "16x9":
            # Master is already 16:9, just scale/pad to exact resolution
            cmd = scale_and_pad(
                assembled_path, out_path, target_w, target_h, config.encoding
            )
        else:
            # Portrait/square: center crop from landscape
            cmd = center_crop(
                assembled_path, out_path, target_w, target_h, config.encoding
            )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Render failed for {ratio}:\n{result.stderr[-500:]}"
            )

        outputs[ratio] = out_path

    return outputs
