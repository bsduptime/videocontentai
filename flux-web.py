#!/usr/bin/env python3
"""Simple web UI for generating images via Flux Schnell on local ComfyUI."""

import base64
import http.server
import io
import json
import socket
import time

import httpx
from PIL import Image

COMFYUI_URL = "http://localhost:8188"
PORT = 8765

HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flux Image Generator</title>
<style>
  body { background: #111; color: #eee; font-family: system-ui; max-width: 800px; margin: 40px auto; padding: 0 20px; }
  h1 { font-size: 1.4em; }
  textarea { width: 100%; height: 100px; background: #222; color: #eee; border: 1px solid #444; border-radius: 8px; padding: 12px; font-size: 1em; resize: vertical; }
  button { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 12px 32px; font-size: 1em; cursor: pointer; margin-top: 10px; }
  button:hover { background: #1d4ed8; }
  button:disabled { background: #555; cursor: not-allowed; }
  #status { color: #999; margin-top: 10px; }
  #result { margin-top: 20px; }
  #result img { max-width: 100%; border: 1px solid #333; border-radius: 8px; }
</style>
</head><body>
<h1>Flux Image Generator</h1>
<form id="form">
  <textarea id="prompt" placeholder="Enter your prompt..."></textarea>
  <br>
  <button type="submit" id="btn">Generate</button>
</form>
<div id="status"></div>
<div id="result"></div>
<script>
const form = document.getElementById('form');
const btn = document.getElementById('btn');
const status = document.getElementById('status');
const result = document.getElementById('result');
form.onsubmit = async (e) => {
  e.preventDefault();
  const prompt = document.getElementById('prompt').value.trim();
  if (!prompt) return;
  btn.disabled = true;
  status.textContent = 'Generating...';
  result.innerHTML = '';
  try {
    const resp = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt})
    });
    if (!resp.ok) { status.textContent = 'Error: ' + await resp.text(); return; }
    const data = await resp.json();
    status.textContent = data.message;
    result.innerHTML = '<img src="data:image/jpeg;base64,' + data.image + '">';
  } catch (err) {
    status.textContent = 'Error: ' + err.message;
  } finally {
    btn.disabled = false;
  }
};
</script>
</body></html>"""


def generate_image(prompt_text):
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
            "inputs": {"images": ["7", 0], "filename_prefix": "flux_web"},
        },
    }

    with httpx.Client(timeout=600.0) as client:
        resp = client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        resp.raise_for_status()
        prompt_id = resp.json()["prompt_id"]

        for i in range(120):
            time.sleep(3)
            hist = client.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
            if prompt_id not in hist:
                continue
            status = hist[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI error: {status}")
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
                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=95)
                    elapsed = (i + 1) * 3
                    return base64.b64encode(buf.getvalue()).decode(), elapsed

    raise RuntimeError("Timed out waiting for image")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        prompt_text = body.get("prompt", "").strip()
        if not prompt_text:
            self.send_error(400, "No prompt")
            return
        try:
            print(f"Generating: {prompt_text[:80]}...")
            img_b64, elapsed = generate_image(prompt_text)
            resp = json.dumps({"image": img_b64, "message": f"Done in {elapsed}s"})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp.encode())
            print(f"  Done in {elapsed}s")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, *a):
        pass


try:
    lan_ip = socket.gethostbyname(socket.gethostname())
except Exception:
    lan_ip = "0.0.0.0"

server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
print(f"Flux Web UI: http://{lan_ip}:{PORT}/")
print("Ctrl+C to stop")
server.serve_forever()
