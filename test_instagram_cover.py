#!/usr/bin/env python3
"""Generate a test Instagram cover with Flux background and serve on LAN."""

import http.server
import io
import socket
import sys
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

sys.path.insert(0, str(Path(__file__).parent / "src"))

from videngine.models import PlatformThumbnailConfig, ThumbnailConcept, ThumbnailTemplate
from videngine.stages.thumbnail import _crop_center_square, _crop_to_square, _hex_to_rgb

PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)

COMFYUI_URL = "http://localhost:8188"
INSTAGRAM_SIZE = (1080, 1920)
INSTAGRAM_GRID = (1080, 1080)


def generate_flux_background(prompt: str, seed: int = 42) -> Image.Image | None:
    """Generate a 1280x720 background image via local ComfyUI + Flux Schnell."""
    workflow = {
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
            "inputs": {"text": prompt, "clip": ["2", 0]},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1280, "height": 720, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": seed,
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
            "inputs": {"images": ["7", 0], "filename_prefix": "igcover_test"},
        },
    }

    print("  Submitting to ComfyUI...")
    with httpx.Client(timeout=600.0) as http:
        resp = http.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        resp.raise_for_status()
        prompt_id = resp.json()["prompt_id"]
        print(f"  Queued: {prompt_id}")

        for i in range(120):
            time.sleep(5)
            hist = http.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
            if prompt_id not in hist:
                print(f"  Waiting... ({(i+1)*5}s)", end="\r")
                continue

            status = hist[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                print(f"\n  ComfyUI error: {status.get('messages', '')}")
                return None

            outputs = hist[prompt_id].get("outputs", {})
            if "save" in outputs:
                images = outputs["save"].get("images", [])
                if not images:
                    return None
                img_info = images[0]
                view_resp = http.get(
                    f"{COMFYUI_URL}/view",
                    params={
                        "filename": img_info["filename"],
                        "subfolder": img_info.get("subfolder", ""),
                        "type": img_info.get("type", "output"),
                    },
                )
                view_resp.raise_for_status()
                print(f"\n  Generated in {(i+1)*5}s")
                return Image.open(io.BytesIO(view_resp.content)).convert("RGB")

    print("\n  Timed out")
    return None


def compose_instagram_cover_v2(
    base: Image.Image,
    concept: ThumbnailConcept,
    template: ThumbnailTemplate,
    logo: Image.Image | None,
) -> Image.Image:
    """Improved Instagram cover — larger text, no accent strip, research-backed sizing."""
    w, h = INSTAGRAM_SIZE  # 1080x1920
    sq = INSTAGRAM_GRID[0]  # 1080
    band = (h - sq) // 2  # 420px top/bottom

    primary = _hex_to_rgb(template.primary_color)
    dark = tuple(max(0, c - 80) for c in primary)

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # Step 1: Brand gradient background (full canvas)
    for y in range(h):
        ratio = y / h
        r = int(dark[0] + (primary[0] - dark[0]) * ratio)
        g = int(dark[1] + (primary[1] - dark[1]) * ratio)
        b = int(dark[2] + (primary[2] - dark[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Step 2: Dimmed video frame as background texture in center square
    ig_config = template.instagram
    base_sq = _crop_to_square(base).resize((sq, sq), Image.LANCZOS)
    base_dimmed = ImageEnhance.Brightness(base_sq).enhance(ig_config.background_frame_brightness)
    base_dimmed = ImageEnhance.Color(base_dimmed).enhance(0.3)
    bg_region = img.crop((0, band, w, band + sq))
    blended = Image.blend(bg_region, base_dimmed, ig_config.background_frame_opacity)
    img.paste(blended, (0, band))

    # NO accent strip — research says it just competes with text

    # Step 3: Hook text — BIG (research: 80-120px for headlines on 9:16)
    draw = ImageDraw.Draw(img)
    text = concept.hook_text.upper()
    lines = text.split("\n")

    # Target font size: fill ~70% of safe width (research says bold, large, max 2 lines)
    text_safe_w = w - 120 - 80  # 880px safe area
    font_path = str(PROJECT_ROOT / template.font_impact)

    # Start large and shrink until it fits — target ~70% of safe width for longest line
    target_w = int(text_safe_w * 0.85)
    font_size = 160  # start big
    font = ImageFont.truetype(font_path, font_size)
    for _ in range(20):
        max_line_w = max(font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines)
        if max_line_w <= target_w:
            break
        font_size -= 4
        font = ImageFont.truetype(font_path, font_size)

    print(f"  Font size: {font_size}px (research recommends 80-120px for 1080w)")

    stroke_w = max(5, int(font_size * 0.06))

    # Measure total text block height
    line_heights = []
    for line in lines:
        bbox = font.getbbox(line)
        line_heights.append(bbox[3] - bbox[1])
    line_gap = int(font_size * 0.15)
    total_text_h = sum(line_heights) + line_gap * (len(lines) - 1)

    # Center text vertically in the center square
    text_start_y = band + (sq - total_text_h) // 2
    margin_x = 80

    line_y = text_start_y
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = margin_x + (text_safe_w - line_w) // 2

        # Draw text with strong stroke for readability
        draw.text(
            (x, line_y),
            line,
            font=font,
            fill=(255, 255, 255),
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0),
        )
        line_y += line_heights[i] + line_gap

    # Step 4: Logo at bottom of center square
    if logo:
        logo_h = int(sq * 0.08)
        aspect = logo.width / logo.height
        logo_w = int(logo_h * aspect)
        logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)
        logo_x = (w - logo_w) // 2
        logo_y = band + sq - logo_h - int(sq * 0.06)
        if logo_resized.mode == "RGBA":
            img.paste(logo_resized, (logo_x, logo_y), logo_resized)
        else:
            img.paste(logo_resized, (logo_x, logo_y))

    return img


def main():
    template = ThumbnailTemplate(
        primary_color="#336791",
        accent_color="#F5A623",
        font_impact="assets/fonts/Montserrat-Bold.ttf",
        font_readable="assets/fonts/BebasNeue-Regular.ttf",
        font_scale=1.2,
        instagram=PlatformThumbnailConfig(
            text_style="centered_bold",
            font_scale=1.0,
            use_face=False,
            show_accent_strip=False,  # removed
            background_frame_opacity=0.5,
            background_frame_brightness=0.25,
        ),
    )

    concept = ThumbnailConcept(
        hook_text="10x FASTER\nQUERIES",
        archetype="performance",
        accent_color="#F5A623",
        visual_elements=["database", "lightning bolt", "speed gauge"],
    )

    # Generate real background via Flux Schnell
    flux_prompt = (
        "cinematic dark moody tech background, glowing blue PostgreSQL database server racks, "
        "neon blue light trails and data streams flowing through circuit board patterns, "
        "shallow depth of field, dark navy and electric blue color palette, "
        "no text no words no letters no numbers, professional photography"
    )

    print("Generating Flux Schnell background (1280x720)...")
    base = generate_flux_background(flux_prompt, seed=12345)
    if base is None:
        print("  Flux failed, falling back to gradient")
        base = Image.new("RGB", (1280, 720), (30, 50, 80))

    base_path = OUTPUT_DIR / "flux_base.jpg"
    base.save(base_path, "JPEG", quality=95)
    print(f"  Base image saved: {base_path}")

    # Load logo
    logo_path = PROJECT_ROOT / "assets" / "watermarks" / "dbexpertai-watermark.png"
    logo = Image.open(logo_path).convert("RGBA") if logo_path.exists() else None

    # Generate v2 cover
    print("Composing Instagram cover v2 (larger text, no accent strip)...")
    ig_cover = compose_instagram_cover_v2(base, concept, template, logo)
    cover_path = OUTPUT_DIR / "thumbnail_instagram.jpg"
    ig_cover.save(cover_path, "JPEG", quality=95)
    print(f"  Saved: {cover_path}")

    print("Generating grid preview (1080x1080)...")
    grid = _crop_center_square(ig_cover)
    grid_path = OUTPUT_DIR / "thumbnail_instagram_grid.jpg"
    grid.save(grid_path, "JPEG", quality=95)
    print(f"  Saved: {grid_path}")

    # HTML preview
    html = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instagram Cover Preview v2</title>
<style>
  body { background: #111; color: #eee; font-family: system-ui; text-align: center; padding: 20px; }
  h1 { font-size: 1.4em; margin-bottom: 5px; }
  .label { color: #999; font-size: 0.9em; margin: 15px 0 5px; }
  img { border: 1px solid #333; border-radius: 8px; }
  .container { display: flex; gap: 40px; justify-content: center; align-items: flex-start; flex-wrap: wrap; }
  .section { margin-bottom: 40px; }
</style>
</head><body>
<h1>Instagram Cover v2 — Flux background, larger text, no accent strip</h1>
<div class="section">
  <p class="label">Flux Schnell generated base image (1280x720)</p>
  <img src="/flux_base.jpg" width="640" alt="Flux base">
</div>
<div class="container">
  <div>
    <img src="/thumbnail_instagram.jpg" height="600" alt="Reel cover">
    <p class="label">9:16 Reel Cover (1080x1920)</p>
  </div>
  <div>
    <img src="/thumbnail_instagram_grid.jpg" height="400" alt="Grid preview">
    <p class="label">1:1 Grid Preview (1080x1080)</p>
  </div>
</div>
</body></html>"""
    (OUTPUT_DIR / "index.html").write_text(html)

    # Serve
    hostname = socket.gethostname()
    try:
        lan_ip = socket.gethostbyname(hostname)
    except Exception:
        lan_ip = "0.0.0.0"

    port = 8765

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(OUTPUT_DIR), **kwargs)

        def log_message(self, fmt, *args):
            print(f"  [{args[0]}] {args[1]}")

    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print("\n  Preview ready at:")
    print(f"    http://{lan_ip}:{port}/")
    print(f"    http://{hostname}:{port}/")
    print("\n  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
