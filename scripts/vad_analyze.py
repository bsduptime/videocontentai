#!/usr/bin/env python3
"""Run VAD (Valence-Arousal-Dominance) analysis on video clips using wav2vec2-large-robust.

Outputs continuous V/A/D scores per window, overall averages, and energy mode
classification mapped to the content pipeline's drive/tension/steady system.

Model: audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torch.nn as nn
import transformers

WINDOW_SEC = 3  # analyze in 3-second windows (matches emotion2vec)
SAMPLE_RATE = 16000
MODEL_NAME = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"

# Energy mode classification uses percentile-based thresholds.
# The model outputs values typically in the 0.05–0.80 range, clustered
# differently per speaker. We classify relative to per-recording stats
# after analysis, but for individual windows we use absolute thresholds
# calibrated from MSP-Podcast norms.
#
# Drive:   high arousal, positive valence
# Tension: high arousal, negative/low valence
# Steady:  low arousal (regardless of valence)
AROUSAL_HIGH_THRESHOLD = 0.25  # above this = high energy (drive or tension)
VALENCE_POSITIVE_THRESHOLD = 0.22  # above this = positive (drive vs tension)


class Wav2Vec2ForSpeechClassification(nn.Module):
    """Custom classification head matching audeering's architecture.

    Architecture (from state dict inspection):
    - wav2vec2 base encoder (12 layers, hidden_size=1024)
    - Mean pooling over time
    - classifier.dense: Linear(1024, 1024) + ReLU + Dropout
    - classifier.out_proj: Linear(1024, 3) → [arousal, dominance, valence]
    """

    def __init__(self, config):
        super().__init__()
        self.wav2vec2 = transformers.Wav2Vec2Model(config)
        self.classifier = nn.ModuleDict(
            {
                "dense": nn.Linear(config.hidden_size, config.hidden_size),
                "out_proj": nn.Linear(config.hidden_size, 3),
            }
        )

    def forward(self, input_values, attention_mask=None):
        outputs = self.wav2vec2(input_values, attention_mask=attention_mask)
        hidden = outputs.last_hidden_state  # [B, T, 1024]

        # Mean pooling
        pooled = hidden.mean(dim=1)  # [B, 1024]

        # Classification head
        x = self.classifier["dense"](pooled)
        x = torch.relu(x)
        logits = self.classifier["out_proj"](x)

        return logits


def classify_energy_mode(arousal: float, valence: float) -> str:
    """Map VAD scores to pipeline energy modes (drive/tension/steady)."""
    if arousal >= AROUSAL_HIGH_THRESHOLD:
        if valence >= VALENCE_POSITIVE_THRESHOLD:
            return "drive"
        return "tension"
    return "steady"


def classify_energy_modes_relative(windows: list[dict]) -> list[dict]:
    """Re-classify energy modes using per-recording percentiles.

    Uses the top 33% arousal windows as high-energy, then splits
    by valence median into drive vs tension.
    """
    if not windows:
        return windows

    arousals = sorted(w["arousal"] for w in windows)
    valences = sorted(w["valence"] for w in windows)

    # Top third by arousal = high energy
    a_threshold = arousals[len(arousals) * 2 // 3]
    v_median = valences[len(valences) // 2]

    for w in windows:
        if w["arousal"] >= a_threshold:
            w["energy_mode"] = "drive" if w["valence"] >= v_median else "tension"
        else:
            w["energy_mode"] = "steady"

    return windows


def extract_audio(video_path: Path, out_wav: Path) -> None:
    """Extract 16kHz mono WAV from video."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-f",
            "wav",
            str(out_wav),
        ],
        capture_output=True,
        check=True,
    )


def load_model(device: str = "cuda:0"):
    """Load wav2vec2-large-robust emotion model with custom classification head."""
    config = transformers.AutoConfig.from_pretrained(MODEL_NAME)
    model = Wav2Vec2ForSpeechClassification(config)

    # Load weights from pretrained
    state_dict = torch.hub.load_state_dict_from_url(
        f"https://huggingface.co/{MODEL_NAME}/resolve/main/pytorch_model.bin",
        map_location="cpu",
    )
    model.load_state_dict(state_dict, strict=False)
    model.eval()

    if torch.cuda.is_available():
        model = model.to(device)

    processor = transformers.Wav2Vec2Processor.from_pretrained(MODEL_NAME)

    return model, processor


def predict_vad(model, processor, audio: np.ndarray, device: str) -> dict:
    """Run VAD prediction on audio array. Returns {arousal, dominance, valence}."""
    inputs = processor(
        audio,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs)

    scores = logits.squeeze().cpu().numpy()
    return {
        "arousal": float(scores[0]),
        "dominance": float(scores[1]),
        "valence": float(scores[2]),
    }


def analyze_video(video_path: Path, model, processor, device: str) -> dict:
    """Run VAD analysis on a single video with windowed analysis."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)

    extract_audio(video_path, wav_path)

    try:
        audio_data, sr = sf.read(str(wav_path))
        assert sr == SAMPLE_RATE, f"Expected {SAMPLE_RATE}Hz, got {sr}Hz"
        total_samples = len(audio_data)
        total_duration = total_samples / sr
        window_samples = WINDOW_SEC * sr

        # Windowed analysis
        windows = []
        for start_sample in range(0, total_samples, window_samples):
            end_sample = min(start_sample + window_samples, total_samples)
            chunk = audio_data[start_sample:end_sample]

            # Skip very short chunks (< 0.5s)
            if len(chunk) < sr * 0.5:
                continue

            vad = predict_vad(model, processor, chunk.astype(np.float32), device)
            mode = classify_energy_mode(vad["arousal"], vad["valence"])

            windows.append(
                {
                    "start_sec": round(start_sample / sr, 2),
                    "end_sec": round(end_sample / sr, 2),
                    "arousal": round(vad["arousal"], 4),
                    "dominance": round(vad["dominance"], 4),
                    "valence": round(vad["valence"], 4),
                    "energy_mode": mode,
                }
            )

        # Re-classify using per-recording relative thresholds
        classify_energy_modes_relative(windows)

        # Overall averages
        if windows:
            avg_a = sum(w["arousal"] for w in windows) / len(windows)
            avg_d = sum(w["dominance"] for w in windows) / len(windows)
            avg_v = sum(w["valence"] for w in windows) / len(windows)
        else:
            avg_a = avg_d = avg_v = 0.0

        overall_mode = classify_energy_mode(avg_a, avg_v)

        overall = {
            "arousal": round(avg_a, 4),
            "dominance": round(avg_d, 4),
            "valence": round(avg_v, 4),
            "energy_mode": overall_mode,
        }

        # Build energy mode segments (consecutive windows with same mode)
        segments = []
        if windows:
            seg_start = windows[0]["start_sec"]
            seg_mode = windows[0]["energy_mode"]
            seg_arousals = [windows[0]["arousal"]]
            seg_valences = [windows[0]["valence"]]
            seg_dominances = [windows[0]["dominance"]]

            for w in windows[1:]:
                if w["energy_mode"] != seg_mode:
                    segments.append(
                        {
                            "energy_mode": seg_mode,
                            "start_sec": seg_start,
                            "end_sec": w["start_sec"],
                            "duration_sec": round(w["start_sec"] - seg_start, 2),
                            "avg_arousal": round(sum(seg_arousals) / len(seg_arousals), 4),
                            "avg_valence": round(sum(seg_valences) / len(seg_valences), 4),
                            "avg_dominance": round(sum(seg_dominances) / len(seg_dominances), 4),
                        }
                    )
                    seg_start = w["start_sec"]
                    seg_mode = w["energy_mode"]
                    seg_arousals = [w["arousal"]]
                    seg_valences = [w["valence"]]
                    seg_dominances = [w["dominance"]]
                else:
                    seg_arousals.append(w["arousal"])
                    seg_valences.append(w["valence"])
                    seg_dominances.append(w["dominance"])

            segments.append(
                {
                    "energy_mode": seg_mode,
                    "start_sec": seg_start,
                    "end_sec": windows[-1]["end_sec"],
                    "duration_sec": round(windows[-1]["end_sec"] - seg_start, 2),
                    "avg_arousal": round(sum(seg_arousals) / len(seg_arousals), 4),
                    "avg_valence": round(sum(seg_valences) / len(seg_valences), 4),
                    "avg_dominance": round(sum(seg_dominances) / len(seg_dominances), 4),
                }
            )

        # Energy mode distribution
        mode_time = {}
        for seg in segments:
            mode_time[seg["energy_mode"]] = (
                mode_time.get(seg["energy_mode"], 0) + seg["duration_sec"]
            )
        distribution = {
            m: round(t / total_duration * 100, 1)
            for m, t in sorted(mode_time.items(), key=lambda x: x[1], reverse=True)
        }

        # Arousal arc (for visualizing energy curve across the video)
        arousal_arc = [{"time_sec": w["start_sec"], "arousal": w["arousal"]} for w in windows]

        return {
            "file": str(video_path),
            "duration_sec": round(total_duration, 2),
            "overall": overall,
            "windows": windows,
            "segments": segments,
            "energy_mode_distribution_pct": distribution,
            "arousal_arc": arousal_arc,
        }

    finally:
        wav_path.unlink(missing_ok=True)


def main():
    video_paths = sys.argv[1:]
    if not video_paths:
        print("Usage: vad_analyze.py <video1.mp4> [video2.mp4 ...]")
        sys.exit(1)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Loading wav2vec2-large-robust VAD model on {device}...", flush=True)
    model, processor = load_model(device)
    print("Model loaded.\n", flush=True)

    all_results = []
    for vp in video_paths:
        path = Path(vp)
        print(f"Analyzing: {path.name}...", flush=True)
        result = analyze_video(path, model, processor, device)
        all_results.append(result)

        # Print summary
        o = result["overall"]
        print(f"  Duration: {result['duration_sec']:.1f}s")
        print(
            f"  Overall: {o['energy_mode']}  "
            f"(A={o['arousal']:.3f}  V={o['valence']:.3f}  "
            f"D={o['dominance']:.3f})"
        )
        print(f"  Segments: {len(result['segments'])}")
        for seg in result["segments"]:
            print(
                f"    {seg['start_sec']:6.1f}s - {seg['end_sec']:6.1f}s  "
                f"{seg['energy_mode']:>8s}  "
                f"(A={seg['avg_arousal']:.3f}  "
                f"V={seg['avg_valence']:.3f}  "
                f"D={seg['avg_dominance']:.3f})"
            )
        dist = result["energy_mode_distribution_pct"]
        print(f"  Energy distribution: " f"{', '.join(f'{m} {p}%' for m, p in dist.items())}")
        print()

    # Write full results
    out_path = Path(video_paths[0]).parent / "vad_analysis.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Full results saved to: {out_path}")


if __name__ == "__main__":
    main()
