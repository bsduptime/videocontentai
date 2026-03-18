"""Stage 3: Cut — extract segments from source, concatenate, and mix music."""

from __future__ import annotations

import json
import logging
import random
import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import (
    concat_segments,
    cut_segment,
    loudnorm_apply,
    loudnorm_measure,
    mix_background_music,
    scale_to_1080p,
)
from ..ffmpeg.probe import probe
from ..models import CutPlan, CutSpec, LoudnessMeasurement, Mood, MoodsConfig

logger = logging.getLogger(__name__)


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
    music_log: dict[str, dict] = {}
    loudness_log: dict[str, dict] = {}

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
            pre_norm_path = scaled_path
        else:
            pre_norm_path = concat_path

        # Step 3.5: Loudness normalize (two-pass EBU R128, audio re-encode, video copy)
        normalized_path = clip_dir / "normalized.mp4"
        measurement = _normalize_loudness(
            str(pre_norm_path), str(normalized_path), config,
        )
        if measurement:
            logger.info(
                "%-20s loudness: %.1f → %.1f LUFS",
                plan.spec_name,
                measurement.input_i,
                config.video.loudnorm_target_lufs,
            )
            loudness_log[plan.spec_name] = measurement.model_dump()
            pre_music_path = normalized_path
        else:
            logger.info("%-20s loudness: normalization skipped", plan.spec_name)
            loudness_log[plan.spec_name] = {"skipped": True}
            pre_music_path = pre_norm_path

        # Step 4: Mix background music (re-encodes audio only, copies video)
        raw_path = clip_dir / "raw.mp4"
        mood_name, music_path = _resolve_mood_music(plan, specs_by_name, moods, config)

        if music_path and Path(music_path).exists():
            music_file = Path(music_path).name
            logger.info("%-20s mood=%-8s file=%s", plan.spec_name, mood_name, music_file)
            music_log[plan.spec_name] = {"mood": mood_name, "file": music_file}
            mix_cmd = mix_background_music(
                str(pre_music_path), music_path, str(raw_path),
                config.encoding, music_volume=config.video.music_volume,
            )
            _run_ffmpeg(mix_cmd)
        else:
            logger.info("%-20s no music", plan.spec_name)
            music_log[plan.spec_name] = {"mood": mood_name or "", "file": ""}
            if pre_music_path != raw_path:
                shutil.copy2(pre_music_path, raw_path)

        outputs[plan.spec_name] = str(raw_path)

    # Write logs for easy review
    music_log_path = work / "music_log.json"
    music_log_path.write_text(json.dumps(music_log, indent=2))
    loudness_log_path = work / "loudness_log.json"
    loudness_log_path.write_text(json.dumps(loudness_log, indent=2))

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
    plan: CutPlan,
    specs_by_name: dict[str, CutSpec],
    moods: dict[str, Mood],
    config: Config,
) -> tuple[str | None, str | None]:
    """Resolve mood name → (mood_name, music file path).

    Randomly picks one of the mood's variant files.
    Agent's choice on plan takes priority; falls back to first option in spec.
    """
    # Prefer the mood the agent chose; fall back to first option in the spec
    mood_name = plan.mood
    if not mood_name:
        spec = specs_by_name.get(plan.spec_name)
        if not spec or not spec.mood_options:
            return None, None
        mood_name = spec.mood_options[0]

    if mood_name not in moods:
        return mood_name, None

    music_dir = Path(config.video.music_dir)
    mood = moods[mood_name]

    # Pick a random variant from the files list
    if mood.files:
        available = [f for f in mood.files if (music_dir / f).exists()]
        if available:
            chosen = random.choice(available)
            return mood_name, str(music_dir / chosen)

    # Fallback: search by mood name with common extensions
    for ext in (".mp3", ".wav", ".m4a", ".ogg"):
        candidate = music_dir / f"{mood_name}{ext}"
        if candidate.exists():
            return mood_name, str(candidate)

    return mood_name, None


def _normalize_loudness(
    input_path: str,
    output_path: str,
    config: Config,
) -> LoudnessMeasurement | None:
    """Two-pass EBU R128 loudness normalization. Returns measurement or None on failure."""
    target = config.video.loudnorm_target_lufs
    tp = config.video.loudnorm_true_peak
    lra = config.video.loudnorm_lra

    # Pass 1: measure
    cmd = loudnorm_measure(input_path, target, tp, lra)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("Loudnorm measure failed: %s", result.stderr[-200:])
        return None

    measurement = _parse_loudnorm_json(result.stderr)
    if not measurement:
        return None

    # Pass 2: apply
    cmd = loudnorm_apply(
        input_path, output_path, config.encoding,
        target_lufs=target, true_peak=tp, lra=lra,
        measured_i=measurement.input_i,
        measured_tp=measurement.input_tp,
        measured_lra=measurement.input_lra,
        measured_thresh=measurement.input_thresh,
        offset=measurement.target_offset,
    )
    _run_ffmpeg(cmd)
    return measurement


def _parse_loudnorm_json(stderr: str) -> LoudnessMeasurement | None:
    """Extract the loudnorm JSON block from FFmpeg stderr."""
    # FFmpeg outputs a JSON block after the loudnorm stats
    try:
        # Find the JSON block — it starts after a line containing just "{"
        lines = stderr.split("\n")
        json_start = None
        json_end = None
        for i, line in enumerate(lines):
            if line.strip() == "{":
                json_start = i
            if json_start is not None and line.strip() == "}":
                json_end = i
                break

        if json_start is None or json_end is None:
            return None

        json_text = "\n".join(lines[json_start : json_end + 1])
        data = json.loads(json_text)

        return LoudnessMeasurement(
            input_i=float(data["input_i"]),
            input_tp=float(data["input_tp"]),
            input_lra=float(data["input_lra"]),
            input_thresh=float(data["input_thresh"]),
            target_offset=float(data["target_offset"]),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("Failed to parse loudnorm JSON: %s", e)
        return None


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
