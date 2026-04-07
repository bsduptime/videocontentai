"""Stage 7: Thumbnail generation — AI concept + image compositing."""

from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from ..ai.client import AIClient
from ..ai.thumbnail_prompts import THUMBNAIL_SYSTEM_PROMPT, build_thumbnail_user_prompt
from ..config import Config
from ..models import (
    Branding,
    CutPlan,
    SourceContext,
    ThumbnailConcept,
    ThumbnailTemplate,
)

logger = logging.getLogger(__name__)

# Project root — three levels up from this file (stages/ → videngine/ → src/ → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Platform output dimensions
YOUTUBE_SIZE = (1280, 720)  # 16:9
SHORTS_SIZE = (1080, 1920)  # 9:16
LINKEDIN_SIZE = (1200, 627)  # ~1.91:1

# Safe zone margins (fraction of canvas)
_SAFE_MARGIN = 0.06  # 6% from edges
_BOTTOM_RIGHT_AVOID = 0.12  # timestamp zone


def run_thumbnail(
    cut_plans: list[CutPlan],
    source_file: str,
    working_dir: str,
    config: Config,
    branding: Branding | None = None,
    source_context: SourceContext | None = None,
) -> dict[str, str]:
    """Generate thumbnails for each cut plan.

    Returns {spec_name: path_to_youtube_thumbnail}.
    """
    work = Path(working_dir)
    client = AIClient(config.ai)
    template = branding.thumbnail if branding else ThumbnailTemplate()

    # Load face reference (Image for Pillow fallback, path for ComfyUI/PuLID)
    brand = source_context.brand if source_context else ""
    face_ref = _load_face_reference(brand, config.thumbnail.face_reference_dir)
    face_ref_path = _find_face_reference_path(brand, config.thumbnail.face_reference_dir)

    # Load watermark/logo for branding overlay
    logo = _load_logo(branding)

    outputs: dict[str, str] = {}

    for plan in cut_plans:
        spec_dir = work / "clips" / plan.spec_name / "thumbnails"
        spec_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate concept via Claude
        concept = _generate_concept(plan, client, source_context, template=template)
        concept_path = spec_dir / "concept.json"
        concept_path.write_text(concept.model_dump_json(indent=2))
        logger.info("Thumbnail concept for %s: %s", plan.spec_name, concept.hook_text)

        # 2. Generate base image: ComfyUI+PuLID → Flux cloud API → Pillow fallback
        base = None
        if not config.thumbnail.fallback_only:
            # Try local ComfyUI first (with PuLID face if available, ~48s; without ~24s)
            base = _generate_comfyui_image(concept, config, face_ref_path=face_ref_path)
            if base:
                logger.info("Generated base image via local ComfyUI for %s", plan.spec_name)

            # Fall back to Flux Kontext cloud API
            if base is None and os.environ.get("BFL_API_KEY") and face_ref is not None:
                base = _generate_base_image(concept, face_ref, config)
                if base:
                    logger.info("Generated base image via Flux API for %s", plan.spec_name)

        # Final fallback: Pillow gradient + face composite
        if base is None:
            logger.info("Using Pillow fallback for %s", plan.spec_name)
            base = _fallback_base_image(concept, face_ref, template)

        base.save(spec_dir / "base_image.png")

        # 3. Compose: text + branding on base image
        composed = _render_text(base.copy(), concept, template)
        if logo:
            composed = _apply_branding(composed, logo, template)

        # 4. Render platform variants
        variants = _render_variants(composed, base, concept, template, logo, spec_dir)
        outputs[plan.spec_name] = str(variants["youtube"])

    return outputs


# --- Concept generation ---


def _generate_concept(
    plan: CutPlan,
    client: AIClient,
    source_context: SourceContext | None,
    template: ThumbnailTemplate | None = None,
) -> ThumbnailConcept:
    """Call Claude to generate a thumbnail concept."""
    user_prompt = build_thumbnail_user_prompt(plan, source_context, template=template)
    raw = client.generate_thumbnail_concept(THUMBNAIL_SYSTEM_PROMPT, user_prompt)
    return ThumbnailConcept.model_validate(raw)


# --- Image generation ---


def _generate_comfyui_image(
    concept: ThumbnailConcept,
    config: Config,
    face_ref_path: str | None = None,
) -> Image.Image | None:
    """Generate base image via local ComfyUI + Flux Schnell.

    If face_ref_path is provided and PuLID nodes are available, generates
    the scene with the creator's face integrated (matching lighting/style).
    Otherwise falls back to background-only generation.
    """
    url = config.thumbnail.comfyui_url

    # Check if ComfyUI is reachable
    try:
        resp = httpx.get(f"{url}/system_stats", timeout=5.0)
        if resp.status_code != 200:
            return None
    except Exception:
        logger.debug("ComfyUI not reachable at %s", url)
        return None

    use_pulid = False
    if face_ref_path:
        # Check if PuLID nodes are available
        try:
            info_resp = httpx.get(f"{url}/object_info/ApplyPulidFlux", timeout=5.0)
            if info_resp.status_code == 200:
                # Copy face reference into ComfyUI input dir (volume-mounted)
                import shutil

                comfyui_input = Path("/mnt/sdcard/comfyui-input")
                if comfyui_input.exists():
                    shutil.copy2(face_ref_path, comfyui_input / "face_ref.png")
                    use_pulid = True
                    logger.info("Using PuLID for face-integrated generation")
                else:
                    logger.warning("ComfyUI input dir not found at %s", comfyui_input)
        except Exception:
            logger.debug("PuLID not available, falling back to plain Flux")

    if use_pulid:
        workflow = _build_pulid_workflow(concept)
    else:
        workflow = _build_flux_workflow(concept)

    return _comfyui_submit_and_poll(url, workflow)


def _build_flux_workflow(concept: ThumbnailConcept) -> dict:
    """Build a plain Flux Schnell workflow (background only, no face)."""
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "flux1-schnell.safetensors", "weight_dtype": "fp8_e4m3fn"},
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "clip_l.safetensors",
                "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
                "type": "flux",
            },
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": concept.flux_prompt, "clip": ["2", 0]},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": YOUTUBE_SIZE[0], "height": YOUTUBE_SIZE[1], "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": hash(concept.hook_text) % 2**32,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
        "save": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": "videngine_thumb"},
        },
    }


def _build_pulid_workflow(concept: ThumbnailConcept) -> dict:
    """Build a PuLID + Flux Schnell workflow (face integrated into scene)."""
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "flux1-schnell.safetensors", "weight_dtype": "fp8_e4m3fn"},
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "clip_l.safetensors",
                "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
                "type": "flux",
            },
        },
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {
            "class_type": "PulidFluxModelLoader",
            "inputs": {"pulid_file": "pulid_flux_v0.9.1.safetensors"},
        },
        "5": {"class_type": "PulidFluxInsightFaceLoader", "inputs": {"provider": "CUDA"}},
        "6": {"class_type": "PulidFluxEvaClipLoader", "inputs": {}},
        "7": {"class_type": "LoadImage", "inputs": {"image": "face_ref.png"}},
        "8": {
            "class_type": "ApplyPulidFlux",
            "inputs": {
                "model": ["1", 0],
                "pulid_flux": ["4", 0],
                "eva_clip": ["6", 0],
                "face_analysis": ["5", 0],
                "image": ["7", 0],
                "weight": 0.85,
                "start_at": 0.0,
                "end_at": 1.0,
            },
        },
        "9": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": concept.flux_prompt, "clip": ["2", 0]},
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": YOUTUBE_SIZE[0], "height": YOUTUBE_SIZE[1], "batch_size": 1},
        },
        "11": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["8", 0],
                "positive": ["9", 0],
                "negative": ["9", 0],
                "latent_image": ["10", 0],
                "seed": hash(concept.hook_text) % 2**32,
                "steps": 4,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "save": {
            "class_type": "SaveImage",
            "inputs": {"images": ["12", 0], "filename_prefix": "videngine_pulid"},
        },
    }


def _comfyui_submit_and_poll(url: str, workflow: dict) -> Image.Image | None:
    """Submit a ComfyUI workflow and poll for the result image."""
    import io

    try:
        with httpx.Client(timeout=600.0) as http:
            resp = http.post(
                f"{url}/prompt",
                json={"prompt": workflow},
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            prompt_id = resp.json()["prompt_id"]
            logger.info("ComfyUI prompt queued: %s", prompt_id)

            # Poll for completion (model load can take minutes on cold start)
            for _ in range(120):  # up to 10 minutes
                time.sleep(5)
                hist_resp = http.get(f"{url}/history/{prompt_id}")
                hist_resp.raise_for_status()
                history = hist_resp.json()

                if prompt_id not in history:
                    continue

                status = history[prompt_id].get("status", {})
                if status.get("status_str") == "error":
                    logger.error("ComfyUI generation failed: %s", status.get("messages", ""))
                    return None

                outputs = history[prompt_id].get("outputs", {})
                if "save" in outputs:
                    images = outputs["save"].get("images", [])
                    if not images:
                        return None

                    img_info = images[0]
                    view_resp = http.get(
                        f"{url}/view",
                        params={
                            "filename": img_info["filename"],
                            "subfolder": img_info.get("subfolder", ""),
                            "type": img_info.get("type", "output"),
                        },
                    )
                    view_resp.raise_for_status()
                    return Image.open(io.BytesIO(view_resp.content)).convert("RGB")

            logger.error("ComfyUI timed out after 10 minutes")
            return None

    except Exception:
        logger.exception("ComfyUI error")
        return None


def _generate_base_image(
    concept: ThumbnailConcept,
    face_ref: Image.Image,
    config: Config,
) -> Image.Image | None:
    """Generate base image via Flux Kontext API with face reference."""
    api_key = os.environ.get("BFL_API_KEY", "")
    if not api_key:
        return None

    # Encode face reference as base64
    import io

    buf = io.BytesIO()
    face_ref.save(buf, format="PNG")
    face_b64 = base64.b64encode(buf.getvalue()).decode()
    image_data_url = f"data:image/png;base64,{face_b64}"

    try:
        with httpx.Client(timeout=120.0) as http:
            # Submit generation request
            response = http.post(
                config.thumbnail.flux_api_url,
                headers={"X-Key": api_key},
                json={
                    "prompt": concept.flux_prompt,
                    "input_image": image_data_url,
                    "aspect_ratio": "16:9",
                    "safety_tolerance": 2,
                    "output_format": "png",
                },
            )
            response.raise_for_status()
            result = response.json()

            # Poll for result
            task_id = result.get("id")
            if not task_id:
                logger.error("Flux API returned no task ID: %s", result)
                return None

            for _ in range(60):  # up to 2 minutes
                time.sleep(2)
                status_resp = http.get(
                    f"https://api.bfl.ai/v1/get_result?id={task_id}",
                    headers={"X-Key": api_key},
                )
                status_resp.raise_for_status()
                status = status_resp.json()

                if status.get("status") == "Ready":
                    image_url = status["result"]["sample"]
                    img_resp = http.get(image_url)
                    img_resp.raise_for_status()
                    return Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                elif status.get("status") in ("Error", "Failed"):
                    logger.error("Flux generation failed: %s", status)
                    return None

            logger.error("Flux API timed out after 2 minutes")
            return None

    except Exception:
        logger.exception("Flux API error")
        return None


def _fallback_base_image(
    concept: ThumbnailConcept,
    face_ref: Image.Image | None,
    template: ThumbnailTemplate,
) -> Image.Image:
    """Create a base image using Pillow: gradient background + face composite."""
    w, h = YOUTUBE_SIZE
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # Parse colors
    primary = _hex_to_rgb(template.primary_color)
    accent = _hex_to_rgb(concept.accent_color)

    # Gradient background: primary → darker shade
    dark = tuple(max(0, c - 60) for c in primary)
    for y in range(h):
        ratio = y / h
        r = int(primary[0] * (1 - ratio) + dark[0] * ratio)
        g = int(primary[1] * (1 - ratio) + dark[1] * ratio)
        b = int(primary[2] * (1 - ratio) + dark[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Accent strip at bottom (above timestamp zone)
    strip_h = int(h * 0.008)
    strip_y = int(h * 0.85)
    draw.rectangle([(0, strip_y), (w, strip_y + strip_h)], fill=accent)

    # Composite face reference on right side (looking left → gaze directs to text/visuals)
    if face_ref:
        face = face_ref.copy()
        # Scale face to fill ~85% of height
        target_h = int(h * 0.85)
        aspect = face.width / face.height
        target_w = int(target_h * aspect)
        face = face.resize((target_w, target_h), Image.LANCZOS)

        # Position: right side, vertically centered
        x = w - target_w - int(w * 0.02)
        y = (h - target_h) // 2

        # If face has alpha channel, use it as mask
        if face.mode == "RGBA":
            img.paste(face, (x, y), face)
        else:
            img.paste(face, (x, y))

    return img


# --- Text rendering ---


def _render_text(
    img: Image.Image,
    concept: ThumbnailConcept,
    template: ThumbnailTemplate,
) -> Image.Image:
    """Render hook text onto the image.

    Supports two styles via template.text_style:
    - "plain": all lines white with black stroke
    - "line1_white_line2_red": line 1 white with stroke, line 2+ white on red bar
    """
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # Load font with dynamic sizing, scaled by template
    font = _load_font(template.font_impact, w, concept.hook_text, template.font_scale)

    # Calculate text position in safe zone
    margin_x = int(w * 0.04)

    if concept.text_position == "upper_right":
        bbox = draw.textbbox((0, 0), concept.hook_text, font=font)
        text_w = bbox[2] - bbox[0]
        x = w - margin_x - text_w
    else:
        x = margin_x

    y = int(h * 0.05)
    stroke_w = max(4, int(font.size * 0.06))

    lines = concept.hook_text.upper().split("\n")
    use_red_bar = template.text_style == "line1_white_line2_red" and len(lines) > 1

    line_y = y
    for i, line in enumerate(lines):
        if use_red_bar and i > 0:
            # Red background bar for lines after the first
            left, top, right, bottom = font.getbbox(line)
            text_w = right - left
            pad_x = int(font.size * 0.2)
            pad_y = int(font.size * 0.15)
            rect_y1 = line_y + top - pad_y
            rect_y2 = line_y + bottom + pad_y
            draw.rectangle(
                [(x - pad_x, rect_y1), (x + text_w + pad_x, rect_y2)],
                fill=(220, 20, 20),
            )
            draw.text((x, line_y), line, font=font, fill=(255, 255, 255))
        else:
            # White text with black stroke
            draw.text(
                (x, line_y),
                line,
                font=font,
                fill=(255, 255, 255),
                stroke_width=stroke_w,
                stroke_fill=(0, 0, 0),
            )
        bbox = draw.textbbox((x, line_y), line, font=font)
        line_y = bbox[3] + int(h * 0.01)

    return img


def _resolve_asset(path_str: str) -> Path:
    """Resolve an asset path, trying relative to project root first."""
    p = Path(path_str)
    if p.exists():
        return p
    resolved = _PROJECT_ROOT / p
    if resolved.exists():
        return resolved
    return p  # return as-is, let caller handle missing


def _load_font(
    font_path: str, canvas_width: int, text: str, scale: float = 1.0
) -> ImageFont.FreeTypeFont:
    """Load font with dynamic sizing to fit within 45% of canvas width."""
    target_width = int(canvas_width * 0.45)
    font_size = int(canvas_width * 0.08 * scale)
    resolved_path = str(_resolve_asset(font_path))

    try:
        # Binary search for best font size
        for _ in range(10):
            font = ImageFont.truetype(resolved_path, font_size)
            bbox = font.getbbox(text.upper())
            text_width = bbox[2] - bbox[0]
            if abs(text_width - target_width) < target_width * 0.1:
                break
            if text_width > target_width:
                font_size = int(font_size * 0.85)
            else:
                font_size = int(font_size * 1.15)
        return ImageFont.truetype(resolved_path, max(font_size, 24))
    except OSError:
        logger.warning("Font %s not found, using default", resolved_path)
        return ImageFont.load_default()


# --- Branding overlay ---


def _apply_branding(
    img: Image.Image,
    logo: Image.Image,
    template: ThumbnailTemplate,
) -> Image.Image:
    """Overlay brand logo in the upper-left corner."""
    w, h = img.size
    logo_h = int(h * template.logo_scale)
    aspect = logo.width / logo.height
    logo_w = int(logo_h * aspect)
    logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)

    margin = int(w * _SAFE_MARGIN)
    pos = (margin, margin)

    if logo_resized.mode == "RGBA":
        img.paste(logo_resized, pos, logo_resized)
    else:
        img.paste(logo_resized, pos)

    return img


# --- Platform variants ---


def _render_variants(
    composed_youtube: Image.Image,
    base: Image.Image,
    concept: ThumbnailConcept,
    template: ThumbnailTemplate,
    logo: Image.Image | None,
    output_dir: Path,
) -> dict[str, Path]:
    """Render platform-specific thumbnail variants."""
    variants: dict[str, Path] = {}

    # YouTube (16:9) — already composed
    yt_path = output_dir / "thumbnail_youtube.png"
    composed_youtube.save(yt_path, "PNG")
    variants["youtube"] = yt_path

    # Shorts (9:16) — re-compose vertically
    shorts = _compose_vertical(base, concept, template, logo, SHORTS_SIZE)
    shorts_path = output_dir / "thumbnail_shorts.png"
    shorts.save(shorts_path, "PNG")
    variants["shorts"] = shorts_path

    # LinkedIn (~1.91:1) — crop/resize from YouTube
    li = composed_youtube.resize(LINKEDIN_SIZE, Image.LANCZOS)
    li_path = output_dir / "thumbnail_linkedin.png"
    li.save(li_path, "PNG")
    variants["linkedin"] = li_path

    return variants


def _compose_vertical(
    base: Image.Image,
    concept: ThumbnailConcept,
    template: ThumbnailTemplate,
    logo: Image.Image | None,
    size: tuple[int, int],
) -> Image.Image:
    """Compose a vertical (9:16) thumbnail variant.

    Layout: text in upper third, face/scene in lower two-thirds.
    """
    w, h = size
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # Gradient background
    primary = _hex_to_rgb(template.primary_color)
    dark = tuple(max(0, c - 60) for c in primary)
    for y in range(h):
        ratio = y / h
        r = int(primary[0] * (1 - ratio) + dark[0] * ratio)
        g = int(primary[1] * (1 - ratio) + dark[1] * ratio)
        b = int(primary[2] * (1 - ratio) + dark[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Paste cropped base image in lower portion
    # Center-crop the base to fill width, place in bottom 60%
    base_aspect = base.width / base.height
    fill_w = w
    fill_h = int(fill_w / base_aspect)
    if fill_h < int(h * 0.6):
        fill_h = int(h * 0.6)
        fill_w = int(fill_h * base_aspect)
    resized = base.resize((fill_w, fill_h), Image.LANCZOS)

    # Center-crop to canvas width
    crop_x = (fill_w - w) // 2
    cropped = resized.crop((crop_x, 0, crop_x + w, fill_h))
    paste_y = h - min(fill_h, h)
    img.paste(cropped, (0, paste_y))

    # Render text in upper area (within safe zone)
    font = _load_font(template.font_impact, w, concept.hook_text)
    margin_x = int(w * _SAFE_MARGIN)
    margin_y = int(h * 0.22)  # ~22% from top (below platform UI chrome)

    text = concept.hook_text.upper()
    stroke_width = max(3, int(font.size * 0.06))
    draw = ImageDraw.Draw(img)
    draw.text(
        (margin_x, margin_y),
        text,
        font=font,
        fill=(255, 255, 255),
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0),
    )

    # Logo in upper-left
    if logo:
        img = _apply_branding(img, logo, template)

    return img


# --- Helpers ---


def _find_face_reference_path(brand: str, face_dir: str) -> str | None:
    """Find the file path for a brand's face reference photo."""
    if not brand:
        return None
    resolved_dir = _resolve_asset(face_dir)
    for ext in ("png", "jpg", "jpeg"):
        face_path = resolved_dir / f"{brand}.{ext}"
        if face_path.exists():
            return str(face_path.resolve())
    return None


def _load_face_reference(brand: str, face_dir: str) -> Image.Image | None:
    """Load the reference face photo for a brand."""
    if not brand:
        return None
    resolved_dir = _resolve_asset(face_dir)
    for ext in ("png", "jpg", "jpeg"):
        face_path = resolved_dir / f"{brand}.{ext}"
        if face_path.exists():
            logger.info("Loaded face reference: %s", face_path)
            return Image.open(face_path).convert("RGBA")
    logger.warning("No face reference found for brand '%s' at %s", brand, resolved_dir)
    return None


def _load_logo(branding: Branding | None) -> Image.Image | None:
    """Load the watermark/logo image for branding overlay."""
    if not branding or not branding.watermark:
        return None
    logo_path = _resolve_asset(branding.watermark)
    if logo_path.exists():
        return Image.open(logo_path).convert("RGBA")
    return None


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
