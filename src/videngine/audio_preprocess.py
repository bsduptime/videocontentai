"""Audio preprocessing: denoise via DeepFilterNet3.

Extracts audio from video, runs DeepFilterNet3 noise suppression,
and outputs a cleaned 48kHz WAV file.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import types
from pathlib import Path

logger = logging.getLogger(__name__)

# DeepFilterNet3 model singleton — loaded once, reused across calls
_df_model = None
_df_state = None


def _patch_torchaudio_compat() -> None:
    """Patch torchaudio.backend.common.AudioMetaData for torchaudio >= 2.1.

    DeepFilterNet's df.io imports from torchaudio.backend.common which was
    removed in torchaudio 2.1+. This creates a shim so the import succeeds.
    """
    if "torchaudio.backend.common" in sys.modules:
        return

    try:
        from torchaudio.backend.common import AudioMetaData  # noqa: F401

        return  # import works, no patch needed
    except (ImportError, ModuleNotFoundError):
        pass

    class AudioMetaData:
        def __init__(
            self, sample_rate=0, num_frames=0, num_channels=0, bits_per_sample=0, encoding=""
        ):
            self.sample_rate = sample_rate
            self.num_frames = num_frames
            self.num_channels = num_channels

    backend = types.ModuleType("torchaudio.backend")
    common = types.ModuleType("torchaudio.backend.common")
    common.AudioMetaData = AudioMetaData
    sys.modules["torchaudio.backend"] = backend
    sys.modules["torchaudio.backend.common"] = common


def _get_model():
    """Load DeepFilterNet3 model (singleton)."""
    global _df_model, _df_state

    if _df_model is not None:
        return _df_model, _df_state

    _patch_torchaudio_compat()
    from df.enhance import init_df

    logger.info("Loading DeepFilterNet3 model...")
    _df_model, _df_state, _ = init_df()
    logger.info("DeepFilterNet3 loaded (sample rate: %dHz)", _df_state.sr())

    return _df_model, _df_state


def extract_audio_48k(video_path: str, output_wav: str) -> None:
    """Extract audio from video as 48kHz mono WAV (for DeepFilterNet)."""
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "1",
            output_wav,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed:\n{result.stderr[-500:]}")


def denoise_audio(input_wav: str, output_wav: str, atten_lim_db: float | None = None) -> None:
    """Run DeepFilterNet3 noise suppression on a WAV file.

    Args:
        input_wav: Path to input 48kHz WAV.
        output_wav: Path to write denoised WAV.
        atten_lim_db: Max noise attenuation in dB. None = unlimited.
                      Use 12-15 for gentle denoising, None for aggressive.
    """
    import soundfile as sf
    import torch

    model, df_state = _get_model()

    _patch_torchaudio_compat()
    from df.enhance import enhance

    # Load audio via soundfile (bypasses torchaudio compatibility issues)
    audio_np, sr = sf.read(input_wav, dtype="float32")
    if sr != df_state.sr():
        raise ValueError(f"Expected {df_state.sr()}Hz, got {sr}Hz")

    # Convert to torch tensor: [channels, samples]
    if audio_np.ndim == 1:
        audio_tensor = torch.from_numpy(audio_np).unsqueeze(0)
    else:
        audio_tensor = torch.from_numpy(audio_np.T)

    enhanced = enhance(model, df_state, audio_tensor, atten_lim_db=atten_lim_db)

    # Save via soundfile
    enhanced_np = enhanced.squeeze().cpu().numpy()
    sf.write(output_wav, enhanced_np, df_state.sr(), subtype="PCM_16")

    logger.info("Denoised: %s → %s", Path(input_wav).name, Path(output_wav).name)


def replace_audio_track(
    video_path: str,
    audio_wav: str,
    output_path: str,
    compress: bool = False,
    threshold_db: float = -20.0,
    ratio: float = 3.0,
    attack_ms: float = 5.0,
    release_ms: float = 200.0,
    knee_db: float = 6.0,
    makeup_db: float = 2.0,
) -> None:
    """Replace a video's audio track with a WAV file. Video stream-copied.

    If compress=True, applies dynamic compression in the same encode pass.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_wav,
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "copy",
    ]

    if compress:
        af = (
            f"acompressor=threshold={threshold_db}dB"
            f":ratio={ratio}"
            f":attack={attack_ms}"
            f":release={release_ms}"
            f":knee={knee_db}"
            f":makeup={makeup_db}dB"
        )
        cmd += ["-af", af]

    cmd += [
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ac",
        "2",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Audio replace failed:\n{result.stderr[-500:]}")

    logger.info("Replaced audio: %s", Path(output_path).name)


def preprocess_audio(
    video_path: str,
    output_path: str,
    working_dir: str,
    atten_lim_db: float | None = None,
) -> str:
    """Full audio preprocessing pipeline: extract → denoise → replace.

    Args:
        video_path: Input video file.
        output_path: Output video with denoised audio.
        working_dir: Directory for intermediate files.
        atten_lim_db: DeepFilterNet attenuation limit (None = unlimited).

    Returns:
        Path to the output video.
    """
    work = Path(working_dir)
    raw_wav = str(work / "audio_raw_48k.wav")
    clean_wav = str(work / "audio_denoised_48k.wav")

    # Step 1: Extract audio at 48kHz for DeepFilterNet
    logger.info("Extracting audio at 48kHz...")
    extract_audio_48k(video_path, raw_wav)

    # Step 2: Denoise
    logger.info("Running DeepFilterNet3 noise suppression...")
    denoise_audio(raw_wav, clean_wav, atten_lim_db=atten_lim_db)

    # Step 3: Replace audio track in video
    logger.info("Replacing audio track with denoised audio...")
    replace_audio_track(video_path, clean_wav, output_path)

    return output_path
