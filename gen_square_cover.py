#!/usr/bin/env python3
"""Generate Instagram cover from native 9:16 Flux base and serve on LAN."""

import http.server
import io
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
import httpx
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

OUTPUT_DIR = Path("test_output")
OUTPUT_DIR.mkdir(exist_ok=True)
COMFYUI_URL = "http://localhost:8188"

# Step 1: Generate native 1080x1920 (9:16) from Flux
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
        "inputs": {
            "text": "cinematic dark moody tech background, glowing blue PostgreSQL database server racks, neon blue light trails and data streams flowing through circuit board patterns, shallow depth of field, dark navy and electric blue color palette, no text no words no letters no numbers, professional photography, vertical composition",
            "clip": ["2", 0],
        },
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 1080, "height": 1920, "batch_size": 1},
    },
    "6": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": ["4", 0],
            "negative": ["4", 0],
            "latent_image": ["5", 0],
            "seed": 12345,
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
        "inputs": {"images": ["7", 0], "filename_prefix": "igcover_9x16"},
    },
}

print("Generating native 1080x1920 (9:16) via Flux Schnell...")
with httpx.Client(timeout=600.0) as client:
    resp = client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
    resp.raise_for_status()
    prompt_id = resp.json()["prompt_id"]
    print(f"Queued: {prompt_id}")

    base = None
    for i in range(120):
        time.sleep(5)
        hist = client.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
        if prompt_id not in hist:
            print(f"  Waiting... ({(i+1)*5}s)", end="\r", flush=True)
            continue
        status = hist[prompt_id].get("status", {})
        if status.get("status_str") == "error":
            print(f"\nError: {status}")
            sys.exit(1)
        outputs = hist[prompt_id].get("outputs", {})
        if "save" in outputs:
            images = outputs["save"].get("images", [])
            if images:
                img_info = images[0]
                view_resp = client.get(
                    f"{COMFYUI_URL}/view",
                    params={
                        "filename": img_info["filename"],
                        "subfolder": img_info.get("subfolder", ""),
                        "type": img_info.get("type", "output"),
                    },
                )
                view_resp.raise_for_status()
                base = Image.open(io.BytesIO(view_resp.content)).convert("RGB")
                print(f"\nGenerated in {(i+1)*5}s — {base.size}")
            break

if base is None:
    print("Flux failed!")
    sys.exit(1)

base.save(OUTPUT_DIR / "flux_base_9x16.jpg", "JPEG", quality=95)

# Step 2: Compose cover directly on the 9:16 Flux background — no bars, no logo
w, h = 1080, 1920
sq = 1080
band = (h - sq) // 2

# Dim the background slightly for text readability
img = ImageEnhance.Brightness(base).enhance(0.5)
img = ImageEnhance.Color(img).enhance(0.6)

# Text — centered in the center 1080x1080 square (grid-safe)
draw = ImageDraw.Draw(img)
text_lines = ["10X FASTER", "QUERIES"]
text_safe_w = w - 120 - 80  # IG safe zones
font_size = 160
font = ImageFont.truetype("assets/fonts/Montserrat-Bold.ttf", font_size)
target_w = int(text_safe_w * 0.85)
for _ in range(20):
    mw = max(font.getbbox(ln)[2] - font.getbbox(ln)[0] for ln in text_lines)
    if mw <= target_w:
        break
    font_size -= 4
    font = ImageFont.truetype("assets/fonts/Montserrat-Bold.ttf", font_size)

print(f"Font size: {font_size}px")
stroke_w = max(5, int(font_size * 0.06))
lh = [font.getbbox(ln)[3] - font.getbbox(ln)[1] for ln in text_lines]
lg = int(font_size * 0.15)
tth = sum(lh) + lg * (len(text_lines) - 1)
ty = band + (sq - tth) // 2  # center in grid square
for i, line in enumerate(text_lines):
    bbox = font.getbbox(line)
    lw = bbox[2] - bbox[0]
    x = 80 + (text_safe_w - lw) // 2
    draw.text(
        (x, ty), line, font=font, fill=(255, 255, 255), stroke_width=stroke_w, stroke_fill=(0, 0, 0)
    )
    ty += lh[i] + lg

# No logo — branding is in the video content, not on covers

# Save
img.save(OUTPUT_DIR / "thumbnail_instagram.jpg", "JPEG", quality=95)
grid = img.crop((0, band, w, band + sq))
grid.save(OUTPUT_DIR / "thumbnail_instagram_grid.jpg", "JPEG", quality=95)
print("Covers saved")

# HTML
html = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instagram Cover v3</title>
<style>
  body { background: #111; color: #eee; font-family: system-ui; text-align: center; padding: 20px; }
  h1 { font-size: 1.4em; margin-bottom: 5px; }
  .label { color: #999; font-size: 0.9em; margin: 15px 0 5px; }
  img { border: 1px solid #333; border-radius: 8px; }
  .container { display: flex; gap: 40px; justify-content: center; align-items: flex-start; flex-wrap: wrap; }
  .section { margin-bottom: 40px; }
</style>
</head><body>
<h1>Instagram Cover v4 - Native 9:16 Flux, no branding</h1>
<div class="section">
  <p class="label">Flux Schnell base (1080x1920 native 9:16)</p>
  <img src="/flux_base_9x16.jpg" height="400" alt="Flux base 9:16">
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


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(OUTPUT_DIR), **k)

    def log_message(self, *a):
        pass


server = http.server.HTTPServer(("0.0.0.0", 8765), H)
print(f"\nServing at http://{lan_ip}:8765/")
print("Ctrl+C to stop")
server.serve_forever()
