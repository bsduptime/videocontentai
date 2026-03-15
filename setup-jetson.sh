#!/bin/bash
set -euo pipefail

echo "=== videngine Jetson setup ==="

# Check we're on the right platform
if ! command -v nvidia-smi &>/dev/null; then
    echo "WARNING: nvidia-smi not found — CUDA may not be available"
fi

# Install uv if not present
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create venv
echo "Creating Python 3.11 venv..."
uv venv --python python3.11
source .venv/bin/activate

# Install videngine + voice cloning
echo "Installing videngine..."
uv pip install -e .

echo "Installing chatterbox-tts..."
uv pip install chatterbox-tts

# Download whisper model
WHISPER_MODEL="$HOME/.videngine/models/ggml-large-v3-turbo.bin"
if [ ! -f "$WHISPER_MODEL" ]; then
    echo "Downloading whisper large-v3-turbo model..."
    mkdir -p "$(dirname "$WHISPER_MODEL")"
    wget -O "$WHISPER_MODEL" \
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin"
else
    echo "Whisper model already present at $WHISPER_MODEL"
fi

# Check whisper-cli
if command -v whisper-cli &>/dev/null; then
    echo "whisper-cli: $(which whisper-cli)"
else
    echo "WARNING: whisper-cli not found. Install whisper.cpp:"
    echo "  git clone https://github.com/ggerganov/whisper.cpp"
    echo "  cd whisper.cpp && cmake -B build -DGGML_CUDA=ON && cmake --build build -j"
    echo "  sudo cp build/bin/whisper-cli /usr/local/bin/"
fi

# Check ffmpeg
if command -v ffmpeg &>/dev/null; then
    echo "ffmpeg: $(ffmpeg -version | head -1)"
else
    echo "WARNING: ffmpeg not found. Install with: sudo apt install ffmpeg"
fi

# Check API key
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo ""
    echo "WARNING: ANTHROPIC_API_KEY not set. Add to your shell profile:"
    echo "  export ANTHROPIC_API_KEY=\"sk-ant-...\""
fi

echo ""
echo "=== Setup complete ==="
echo "Activate with: source .venv/bin/activate"
echo "Run with:      videngine process video.mp4 --project test"
