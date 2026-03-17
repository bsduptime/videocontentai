"""Stage 3: Cut — extract segments from source, concatenate, and mix music."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import concat_segments, cut_segment, mix_background_music, scale_to_1080p
from ..ffmpeg.probe import probe
from ..models import CutPlan, CutSpec, Mood, MoodsConfig


def run_cut(
    cut_plans: list[CutPlan],
    source_file: str,
    working_dir: str,
    config: Config,
    cut_specs: list[CutSpec] | None = None,
) -> dict[str, str]:
    """Cut segments from source, concatenate, and mix background music.

    Uses stream copy (no re-encoding) for cut and concat.
    Only re-encodes if source needs scaling to 1080p.
    Returns {spec_name: raw_clip_path}.
    """
    work = Path(working_dir)
    clips_dir = work / "clips"

    # Check if source needs scaling
    source_info = probe(source_file)
    is_landscape = source_info.width >= source_info.height
    needs_scale = not _is_1080p(source_info.width, source_info.height)

    # Build spec lookup and load moods
    specs_by_name = {s.name: s for s in cut_specs} if cut_specs else {}
    moods = _load_moods(config)

    outputs: dict[str, str] = {}

    for plan in cut_plans:
        clip_dir = clips_dir / plan.spec_name
        clip_dir.mkdir(parents=True, exist_ok=True)
        segments_dir = clip_dir / "segments"
        segments_dir.mkdir(exist_ok=True)

        # Step 1: Cut segments (stream copy — fast)
        segment_paths = []
        for i, seg in enumerate(plan.segments):
            out_path = segments_dir / f"seg_{i:03d}.mp4"
            cmd = cut_segment(source_file, str(out_path), seg.start, seg.end)
            _run_ffmpeg(cmd)
            segment_paths.append(str(out_path))

        # Step 2: Concat segments (stream copy — fast)
        concat_path = clip_dir / "concat.mp4"
        concat_list_path = clip_dir / "concat_list.txt"
        concat_content, concat_cmd = concat_segments(
            segment_paths, str(concat_path), str(concat_list_path),
        )
        concat_list_path.write_text(concat_content)
        _run_ffmpeg(concat_cmd)

        # Step 3: Scale to 1080p only if needed (re-encodes)
        if needs_scale:
            scaled_path = clip_dir / "scaled.mp4"
            scale_cmd = scale_to_1080p(
                str(concat_path), str(scaled_path), config.encoding, is_landscape
            )
            _run_ffmpeg(scale_cmd)
            pre_music_path = scaled_path
        else:
            pre_music_path = concat_path

        # Step 4: Mix background music (re-encodes audio only, copies video)
        raw_path = clip_dir / "raw.mp4"
        music_path = _resolve_mood_music(plan.spec_name, specs_by_name, moods, config)

        if music_path and Path(music_path).exists():
            mix_cmd = mix_background_music(
                str(pre_music_path), music_path, str(raw_path),
                config.encoding, music_volume=config.video.music_volume,
            )
            _run_ffmpeg(mix_cmd)
        else:
            if pre_music_path != raw_path:
                shutil.copy2(pre_music_path, raw_path)

        outputs[plan.spec_name] = str(raw_path)

    return outputs


def _is_1080p(width: int, height: int) -> bool:
    """Check if resolution is already 1080p (landscape or portrait)."""
    return (width == 1920 and height == 1080) or (width == 1080 and height == 1920)


def _load_moods(config: Config) -> dict[str, Mood]:
    """Load moods from moods.json, returning {name: Mood}."""
    moods_path = Path(config.video.moods_file)
    if not moods_path.exists():
        return {}
    moods_config = MoodsConfig.model_validate_json(moods_path.read_text())
    return {m.name: m for m in moods_config.moods}


def _resolve_mood_music(
    spec_name: str,
    specs_by_name: dict[str, CutSpec],
    moods: dict[str, Mood],
    config: Config,
) -> str | None:
    """Resolve mood name → music file path."""
    spec = specs_by_name.get(spec_name)
    if not spec or not spec.mood:
        return None

    mood_name = spec.mood
    if mood_name not in moods:
        return None

    music_dir = Path(config.video.music_dir)
    for ext in (".mp3", ".wav", ".m4a", ".ogg"):
        candidate = music_dir / f"{mood_name}{ext}"
        if candidate.exists():
            return str(candidate)

    return None


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
