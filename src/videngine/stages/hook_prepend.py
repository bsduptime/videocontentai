"""Stage 6: Hook Prepend — prepend hook clip to cuts that request it."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import concat_segments
from ..models import CutSpec


def run_hook_prepend(
    clip_paths: dict[str, str],
    working_dir: str,
    config: Config,
    cut_specs: list[CutSpec] | None = None,
) -> dict[str, str]:
    """Prepend hook clip to cuts that have prepend_hook=true in their spec.

    Returns {spec_name: final_path}.
    """
    specs_by_name = {s.name: s for s in cut_specs} if cut_specs else {}

    # Find the hook clip
    hook_path = None
    hook_name = None
    for spec_name, path in clip_paths.items():
        spec = specs_by_name.get(spec_name)
        if spec and spec.is_hook:
            hook_path = path
            hook_name = spec_name
            break

    outputs: dict[str, str] = {}

    for spec_name, clip_path in clip_paths.items():
        clip_dir = Path(clip_path).parent
        final_path = clip_dir / "final.mp4"
        spec = specs_by_name.get(spec_name)

        # Hook clip itself → just copy
        if spec_name == hook_name:
            shutil.copy2(clip_path, final_path)
            outputs[spec_name] = str(final_path)
            continue

        # Only prepend if this cut's spec says prepend_hook=true and we have a hook
        should_prepend = hook_path is not None and spec is not None and spec.prepend_hook

        if should_prepend:
            concat_list_path = clip_dir / "hook_concat.txt"
            concat_content, concat_cmd = concat_segments(
                [hook_path, clip_path],
                str(final_path),
                str(concat_list_path),
            )
            concat_list_path.write_text(concat_content)
            _run_ffmpeg(concat_cmd)
        else:
            shutil.copy2(clip_path, final_path)

        outputs[spec_name] = str(final_path)

    return outputs


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
