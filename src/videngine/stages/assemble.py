"""Stage 4: Video assembly — cut, concat, watermark."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import concat_segments, cut_segment
from ..models import EditDecision


def run_assemble(
    edit_decision: EditDecision,
    source_file: str,
    working_dir: str,
    config: Config,
    intro_wav: str | None = None,
    outro_wav: str | None = None,
) -> str:
    """Cut segments, concatenate with intro/outro, apply watermark.

    Returns path to assembled master (16:9).
    """
    work = Path(working_dir)
    segments_dir = work / "segments"
    segments_dir.mkdir(exist_ok=True)

    # Step 1: Cut segments from source
    segment_paths = []
    for i, seg in enumerate(edit_decision.segments):
        out_path = segments_dir / f"seg_{i:03d}.mp4"
        cmd = cut_segment(
            source_file, str(out_path), seg.start, seg.end, config.encoding
        )
        _run_ffmpeg(cmd)
        segment_paths.append(str(out_path))

    # Step 2: Build concat list
    # For MVP: straight concat of segments (intro/outro templates added in Phase 2)
    all_parts = list(segment_paths)

    concat_list_path = work / "concat_list.txt"
    concat_content, concat_cmd = concat_segments(
        all_parts,
        str(work / "assembled_16x9.mp4"),
        str(concat_list_path),
        config.encoding,
    )
    concat_list_path.write_text(concat_content)
    _run_ffmpeg(concat_cmd)

    return str(work / "assembled_16x9.mp4")


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
