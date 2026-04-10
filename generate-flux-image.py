#!/usr/bin/env python3
"""Generate an 800x800 image via Flux Schnell on local ComfyUI."""

import io
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path("test_output")
OUTPUT_DIR.mkdir(exist_ok=True)

if len(sys.argv) < 2:
    print('Usage: python3 generate-flux-image.py "your prompt here"')
    sys.exit(1)

prompt_text = " ".join(sys.argv[1:])

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
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["2", 0]}},
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 800, "height": 800, "batch_size": 1},
    },
    "6": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": ["4", 0],
            "negative": ["4", 0],
            "latent_image": ["5", 0],
            "seed": int(time.time()) % 2**32,
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
        "inputs": {"images": ["7", 0], "filename_prefix": "flux_800"},
    },
}

print(f"Prompt: {prompt_text}")
print("Generating 800x800 via Flux Schnell...")

with httpx.Client(timeout=600.0) as client:
    resp = client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
    resp.raise_for_status()
    prompt_id = resp.json()["prompt_id"]

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
                img = Image.open(io.BytesIO(view_resp.content)).convert("RGB")
                out_path = OUTPUT_DIR / "flux_800.jpg"
                img.save(out_path, "JPEG", quality=95)
                print(f"\nDone in {(i+1)*5}s — saved to {out_path}")
                sys.exit(0)

print("\nTimed out waiting for image.")
sys.exit(1)
