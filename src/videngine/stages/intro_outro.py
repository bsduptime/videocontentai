"""Stage 5: Intro/Outro — prepend/append branded templates with voice narration."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..config import Config
from ..ffmpeg.commands import concat_segments
from ..ffmpeg.probe import probe
from ..models import Branding, CutPlan


def run_intro_outro(
    clip_paths: dict[str, str],
    cut_plans: list[CutPlan],
    working_dir: str,
    config: Config,
    no_voice: bool = False,
    branding: Branding | None = None,
) -> dict[str, str]:
    """Add intro/outro templates to clips, with optional voice narration.

    Picks the correct aspect ratio template from branding.
    Uses stream copy for concat — no re-encoding.
    Hook clips are passed through unchanged.
    Returns {spec_name: path}.
    """
    work = Path(working_dir)
    plans_by_name = {p.spec_name: p for p in cut_plans}

    # Load TTS model once if voice is enabled
    tts_model = None
    ref_audio = None
    if not no_voice:
        tts_model, ref_audio = _load_tts(config, working_dir)

    outputs: dict[str, str] = {}

    for spec_name, watermarked_path in clip_paths.items():
        plan = plans_by_name[spec_name]
        clip_dir = Path(watermarked_path).parent
        output_path = clip_dir / "with_intro_outro.mp4"

        # Hook clips skip intro/outro
        if _is_hook(plan):
            shutil.copy2(watermarked_path, output_path)
            outputs[spec_name] = str(output_path)
            continue

        # Detect aspect ratio from clip to pick the right template
        clip_info = probe(watermarked_path)
        is_landscape = clip_info.width >= clip_info.height

        # Resolve intro/outro templates from branding
        intro_path = _resolve_template(branding, is_landscape, "intro")
        outro_path = _resolve_template(branding, is_landscape, "outro")

        # Generate voice narration if enabled
        intro_wav = None
        outro_wav = None
        if tts_model is not None and ref_audio is not None:
            if plan.intro_narration:
                intro_wav = str(clip_dir / "narration_intro.wav")
                _generate_narration(tts_model, plan.intro_narration, ref_audio, intro_wav)
            if plan.outro_narration:
                outro_wav = str(clip_dir / "narration_outro.wav")
                _generate_narration(tts_model, plan.outro_narration, ref_audio, outro_wav)

        # Build parts list: [intro] + clip + [outro]
        parts = []

        if intro_path:
            if intro_wav:
                mixed_intro = str(clip_dir / "intro_mixed.mp4")
                _mix_audio(intro_path, intro_wav, mixed_intro)
                parts.append(mixed_intro)
            else:
                parts.append(intro_path)

        parts.append(watermarked_path)

        if outro_path:
            if outro_wav:
                mixed_outro = str(clip_dir / "outro_mixed.mp4")
                _mix_audio(outro_path, outro_wav, mixed_outro)
                parts.append(mixed_outro)
            else:
                parts.append(outro_path)

        if len(parts) == 1:
            shutil.copy2(watermarked_path, output_path)
        else:
            # Concat with stream copy — templates are pre-cropped to match
            concat_list_path = clip_dir / "intro_outro_concat.txt"
            concat_content, concat_cmd = concat_segments(
                parts, str(output_path), str(concat_list_path),
            )
            concat_list_path.write_text(concat_content)
            _run_ffmpeg(concat_cmd)

        outputs[spec_name] = str(output_path)

    return outputs


def _resolve_template(
    branding: Branding | None,
    is_landscape: bool,
    kind: str,
) -> str | None:
    """Pick the right intro or outro template for the aspect ratio."""
    if not branding:
        return None

    if kind == "intro":
        path = branding.intro_16x9 if is_landscape else branding.intro_9x16
    else:
        path = branding.outro_16x9 if is_landscape else branding.outro_9x16

    if path and Path(path).exists():
        return path
    return None


def _is_hook(plan: CutPlan) -> bool:
    """Check if a cut plan is for a hook clip."""
    return "hook" in plan.spec_name.lower()


def _load_tts(config: Config, working_dir: str):
    """Load TTS model and prepare reference audio. Returns (model, ref_audio_path) or (None, None)."""
    try:
        import torch
        try:
            import perth
            if perth.PerthImplicitWatermarker is None:
                perth.PerthImplicitWatermarker = perth.DummyWatermarker
        except ImportError:
            pass

        from chatterbox.tts import ChatterboxTTS
    except ImportError:
        return None, None

    ref_audio = _ensure_wav(config.voice.reference_audio, working_dir)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)
    return model, ref_audio


def _ensure_wav(audio_path: str, working_dir: str) -> str:
    """Convert audio to 16-bit WAV if needed."""
    path = Path(audio_path)
    if path.suffix.lower() == ".wav":
        return audio_path

    wav_path = Path(working_dir) / f"voice_ref{path.suffix}_converted.wav"
    if wav_path.exists():
        return str(wav_path)

    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-acodec", "pcm_s16le",
        "-ar", "22050",
        "-ac", "1",
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Voice ref conversion failed:\n{result.stderr[-500:]}")
    return str(wav_path)


def _generate_narration(model, text: str, ref_audio: str, output_path: str) -> None:
    """Generate voice-cloned narration and save as WAV."""
    import soundfile as sf

    wav = model.generate(text, audio_prompt_path=ref_audio)
    wav_np = wav.squeeze().cpu().numpy()
    sf.write(output_path, wav_np, model.sr)


def _mix_audio(video_path: str, audio_path: str, output_path: str) -> None:
    """Mix narration audio over a video, keeping original audio underneath."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        "[0:a]volume=0.3[bg];[1:a]volume=1.0[narr];[bg][narr]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]
    _run_ffmpeg(cmd)


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
