"""Stage 3: Voice cloning via Chatterbox TTS."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import Config
from ..models import EditDecision


def _ensure_wav(audio_path: str, working_dir: str) -> str:
    """Convert audio to 16-bit WAV if needed. Returns path to WAV file."""
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


def _patch_perth() -> None:
    """Patch perth watermarker on platforms where the native ext is unavailable (aarch64)."""
    try:
        import perth
        if perth.PerthImplicitWatermarker is None:
            perth.PerthImplicitWatermarker = perth.DummyWatermarker
    except ImportError:
        pass


def _save_wav(wav_tensor, sample_rate: int, path: str) -> None:
    """Save a waveform tensor to WAV, with fallback for torchaudio >=2.10 (torchcodec)."""
    import soundfile as sf
    wav_np = wav_tensor.squeeze().cpu().numpy()
    sf.write(path, wav_np, sample_rate)


def run_voice(
    edit_decision: EditDecision,
    working_dir: str,
    config: Config,
) -> tuple[str, str]:
    """Generate voice-cloned narration for intro and outro.

    Returns (intro_wav_path, outro_wav_path).
    """
    work = Path(working_dir)
    intro_path = work / "narration_intro.wav"
    outro_path = work / "narration_outro.wav"

    try:
        import torch
        _patch_perth()
        from chatterbox.tts import ChatterboxTTS
    except ImportError:
        raise RuntimeError(
            "chatterbox-tts is not installed. Install with: pip install chatterbox-tts\n"
            "Or use --no-voice to skip voice cloning."
        )

    # Convert reference audio to WAV if needed (m4a, mp3, etc.)
    ref_audio = _ensure_wav(config.voice.reference_audio, working_dir)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)

    # Generate intro narration
    if edit_decision.intro_narration:
        wav = model.generate(edit_decision.intro_narration, audio_prompt_path=ref_audio)
        _save_wav(wav, model.sr, str(intro_path))

    # Generate outro narration
    if edit_decision.outro_narration:
        wav = model.generate(edit_decision.outro_narration, audio_prompt_path=ref_audio)
        _save_wav(wav, model.sr, str(outro_path))

    return str(intro_path), str(outro_path)
