# Local Image Generation on Jetson Orin AGX — Research

Compiled 2026-04-07. Tested approaches for running image generation locally without breaking the existing Python environment.

## Hardware

- NVIDIA Jetson Orin AGX 64GB unified memory
- JetPack 6 (L4T R36.4.4), CUDA 12.6
- eMMC: 57GB (99% full, code only)
- SD card: 234GB (~94GB free), mounted at `/mnt/sdcard`

## Decision: Docker containers (zero risk to host)

Docker containers are the only safe approach. Never pip install image gen libraries into the host Python — that's what breaks whisper/TTS/ffmpeg.

Docker data-root relocated to SD card: `/mnt/sdcard/docker` (configured in `/etc/docker/daemon.json`).

---

## Setup: ComfyUI + Flux Schnell

### Container

```bash
docker run --runtime nvidia -it -d --name comfyui --network host \
  -v /mnt/sdcard/comfyui-models/unet:/root/ComfyUI/models/unet \
  -v /mnt/sdcard/comfyui-models/vae:/root/ComfyUI/models/vae \
  -v /mnt/sdcard/comfyui-models/clip:/root/ComfyUI/models/clip \
  -v /mnt/sdcard/comfyui-output:/root/ComfyUI/output \
  dustynv/comfyui:r36.4.0
```

Web UI at `http://localhost:8188`.

### Flux Schnell model files

Download into `/mnt/sdcard/comfyui-models/`:

| File | Size | Destination |
|------|------|-------------|
| `flux1-schnell.safetensors` | ~29 GB | `unet/` |
| `ae.safetensors` (VAE) | ~335 MB | `vae/` |
| `clip_l.safetensors` | ~235 MB | `clip/` |
| `t5xxl_fp8_e4m3fn.safetensors` | ~4.9 GB | `clip/` |

Total: ~34 GB

Sources:
- flux1-schnell: `https://huggingface.co/black-forest-labs/FLUX.1-schnell`
- ae.safetensors: `https://huggingface.co/black-forest-labs/FLUX.1-schnell`
- clip_l: `https://huggingface.co/comfyanonymous/flux_text_encoders`
- t5xxl_fp8: `https://huggingface.co/comfyanonymous/flux_text_encoders`

### Performance

- ~21 seconds per image on AGX Orin (after model loads)
- Memory: ~24 GB (fp16), fits with 40 GB headroom

### Integration with videngine

ComfyUI exposes an API at `:8188`. The thumbnail stage can POST workflow JSON to generate images instead of calling the Flux Kontext cloud API.

---

## Memory Budget (64GB unified)

| Scenario | Memory | Headroom |
|----------|--------|----------|
| Flux Schnell fp16 + Whisper + TTS | ~29 GB | 35 GB |
| Flux Schnell Q8 + Whisper + TTS | ~21 GB | 43 GB |
| SDXL + Whisper + TTS | ~18 GB | 46 GB |

---

## Alternative: stable-diffusion.cpp

Standalone C++ binary, no Python deps:

```bash
git clone https://github.com/leejet/stable-diffusion.cpp
cd stable-diffusion.cpp && git submodule update --init --recursive
CUDACXX=/usr/local/cuda-12.6/bin/nvcc cmake -B build \
  -DGGML_CUDA=ON -DSD_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

Supports GGUF quantized Flux models (Q8 ~14GB, Q4 ~8GB).

---

## Alternative: NVIDIA Sana (0.6B params)

- 20x smaller than Flux, sub-second generation
- Available in ComfyUI
- Best for speed over absolute quality

---

## Sources

- [Flux on Jetson - NVIDIA Forums](https://forums.developer.nvidia.com/t/flux-ai-image-generation-jetson-container/302621)
- [ComfyUI + Flux on Jetson - NVIDIA Forums](https://forums.developer.nvidia.com/t/comfyui-and-flux-on-jetson-orin/346597)
- [Jetson AI Lab - ComfyUI + Flux Tutorial](https://www.jetson-ai-lab.com/tutorial_comfyui_flux.html)
- [dustynv/comfyui Docker Hub](https://hub.docker.com/r/dustynv/comfyui/tags)
- [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp)
- [SD on Jetson Orin via Open-WebUI](https://calje.medium.com/image-generation-with-stable-diffusion-on-jetson-orin-using-open-webui-4acdf5a71183)
