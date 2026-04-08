"""Stage 4.5: Background Replacement — segment person via RVM, composite onto new background."""

from __future__ import annotations

import logging
import shutil
import subprocess
import urllib.request
from pathlib import Path

import numpy as np

from ..config import BackgroundConfig, Config, EncodingConfig
from ..ffmpeg.commands import composite_with_matte

logger = logging.getLogger(__name__)

# RVM ONNX model info
_RVM_MODEL_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
_RVM_MODEL_NAME = "rvm_mobilenetv3_fp32.onnx"
_MODELS_DIR = Path.home() / ".videngine" / "models"


def _ensure_rvm_model() -> str:
    """Download RVM ONNX model if not already present. Returns model path."""
    _MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = _MODELS_DIR / _RVM_MODEL_NAME
    if model_path.exists():
        return str(model_path)

    logger.info("Downloading RVM model to %s ...", model_path)
    urllib.request.urlretrieve(_RVM_MODEL_URL, str(model_path))
    logger.info("RVM model downloaded.")
    return str(model_path)


def _generate_alpha_matte(
    input_path: str,
    matte_path: str,
    model_path: str,
    encoding: EncodingConfig,
    downsample_ratio: float = 0.25,
) -> None:
    """Run RVM on every frame and encode alpha matte as grayscale video.

    Uses onnxruntime with CUDA (falls back to CPU). The matte video is
    encoded as grayscale H.264 — white = foreground, black = background.
    """
    import cv2
    import onnxruntime as ort

    # Pick execution provider
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    available = ort.get_available_providers()
    use_providers = [p for p in providers if p in available]
    logger.info("ONNX providers: %s", use_providers)

    session = ort.InferenceSession(model_path, providers=use_providers)

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # RVM recurrent states (initialized to zero)
    rec = [np.zeros((1, 1, 1, 1), dtype=np.float32)] * 4  # r1, r2, r3, r4

    # Output writer — grayscale matte encoded as mp4
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(matte_path, fourcc, fps, (width, height), False)

    frame_count = 0
    log_interval = max(1, total_frames // 20)  # log every 5%

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Preprocess: BGR -> RGB, normalize to [0,1], NCHW
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inp = rgb.astype(np.float32) / 255.0
        inp = np.transpose(inp, (2, 0, 1))[np.newaxis]  # (1, 3, H, W)

        # Run RVM
        downsample = np.array([downsample_ratio], dtype=np.float32)
        outputs = session.run(
            None,
            {
                "src": inp,
                "r1i": rec[0],
                "r2i": rec[1],
                "r3i": rec[2],
                "r4i": rec[3],
                "downsample_ratio": downsample,
            },
        )

        # Outputs: fgr, pha, r1o, r2o, r3o, r4o
        pha = outputs[1]  # (1, 1, H, W) alpha matte [0, 1]
        rec = outputs[2:6]  # updated recurrent states

        # Convert alpha to grayscale uint8
        alpha = (pha[0, 0] * 255).clip(0, 255).astype(np.uint8)
        writer.write(alpha)

        frame_count += 1
        if frame_count % log_interval == 0:
            pct = frame_count / total_frames * 100
            logger.info("Matte generation: %d/%d frames (%.0f%%)", frame_count, total_frames, pct)

    cap.release()
    writer.release()
    logger.info("Alpha matte saved: %s (%d frames)", matte_path, frame_count)


def _generate_blur_background(
    input_path: str,
    bg_path: str,
    blur_strength: int,
    encoding: EncodingConfig,
) -> None:
    """Generate a blurred version of the original video for use as background."""
    # Ensure blur strength is odd (required by boxblur)
    bs = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        f"boxblur={bs}:{bs}",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-an",
        bg_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg blur failed:\n{result.stderr[-500:]}")


def run_background(
    clip_paths: dict[str, str],
    working_dir: str,
    config: Config,
) -> dict[str, str]:
    """Replace video backgrounds using RVM segmentation + FFmpeg compositing.

    Flow per clip:
      1. Run RVM to generate alpha matte video
      2. Generate or locate background (blur / solid / image)
      3. FFmpeg composite: background + original + matte → output

    Returns {spec_name: output_path}.
    """
    bg_config = config.background

    if not bg_config.enabled:
        # Pass through — copy input to output filename
        outputs: dict[str, str] = {}
        for spec_name, clip_path in clip_paths.items():
            clip_dir = Path(clip_path).parent
            out_path = clip_dir / "bg_replaced.mp4"
            shutil.copy2(clip_path, out_path)
            outputs[spec_name] = str(out_path)
        return outputs

    model_path = _ensure_rvm_model()

    outputs = {}
    for spec_name, clip_path in clip_paths.items():
        logger.info("Background replacement for %s", spec_name)
        clip_dir = Path(clip_path).parent
        matte_path = str(clip_dir / "alpha_matte.mp4")
        out_path = str(clip_dir / "bg_replaced.mp4")

        # Step 1: Generate alpha matte
        _generate_alpha_matte(
            clip_path,
            matte_path,
            model_path,
            config.encoding,
            downsample_ratio=bg_config.downsample_ratio,
        )

        # Step 2: Prepare background
        bg_source = _resolve_background(clip_path, clip_dir, bg_config, config.encoding)

        # Step 3: Composite
        cmd = composite_with_matte(
            clip_path,
            matte_path,
            bg_source,
            out_path,
            config.encoding,
            bg_type=bg_config.background_type,
            solid_color=bg_config.solid_color,
        )
        _run_ffmpeg(cmd)
        outputs[spec_name] = out_path
        logger.info("Background replaced: %s", out_path)

    return outputs


def _resolve_background(
    clip_path: str,
    clip_dir: Path,
    bg_config: BackgroundConfig,
    encoding: EncodingConfig,
) -> str:
    """Prepare the background source based on config type.

    Returns path to background video/image, or empty string for solid color.
    """
    bg_type = bg_config.background_type

    if bg_type == "blur":
        bg_path = str(clip_dir / "bg_blurred.mp4")
        _generate_blur_background(clip_path, bg_path, bg_config.blur_strength, encoding)
        return bg_path

    elif bg_type == "image":
        if not bg_config.background_image or not Path(bg_config.background_image).exists():
            raise FileNotFoundError(f"Background image not found: {bg_config.background_image}")
        return bg_config.background_image

    elif bg_type == "solid":
        # Solid color handled in FFmpeg filter — no file needed
        return ""

    else:
        raise ValueError(f"Unknown background type: {bg_type}")


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run an FFmpeg command, raising on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-500:]}")
