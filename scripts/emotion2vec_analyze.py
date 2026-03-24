#!/usr/bin/env python3
"""Run emotion2vec analysis on video clips with temporal windowing."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import soundfile as sf

EMOTION_LABELS = [
    "angry", "disgusted", "fearful", "happy",
    "neutral", "other", "sad", "surprised", "unknown",
]

WINDOW_SEC = 3  # analyze in 3-second windows for temporal tracking


def extract_audio(video_path: Path, out_wav: Path) -> None:
    """Extract 16kHz mono WAV from video."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video_path),
            "-ar", "16000", "-ac", "1", "-f", "wav",
            str(out_wav),
        ],
        capture_output=True,
        check=True,
    )


def parse_scores(raw_scores):
    """Normalize raw scores to a list of 9 floats."""
    scores = raw_scores
    if hasattr(scores, "tolist"):
        scores = scores.tolist()
    if isinstance(scores[0], list):
        scores = scores[0]
    return [float(s) for s in scores]


def analyze_video(video_path: Path, model) -> dict:
    """Run emotion2vec on a single video with windowed analysis."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)

    extract_audio(video_path, wav_path)

    try:
        # Overall utterance-level analysis
        utt_res = model.generate(
            str(wav_path),
            granularity="utterance",
            extract_embedding=False,
        )
        scores = parse_scores(utt_res[0]["scores"])
        labeled = {EMOTION_LABELS[i]: round(s, 4) for i, s in enumerate(scores)}
        top = max(labeled, key=labeled.get)
        overall = {
            "top_emotion": top,
            "confidence": labeled[top],
            "all_scores": labeled,
        }

        # Windowed analysis: split audio into WINDOW_SEC chunks
        audio_data, sr = sf.read(str(wav_path))
        total_samples = len(audio_data)
        total_duration = total_samples / sr
        window_samples = WINDOW_SEC * sr

        windows = []
        for start_sample in range(0, total_samples, window_samples):
            end_sample = min(start_sample + window_samples, total_samples)
            chunk = audio_data[start_sample:end_sample]

            # Skip very short chunks (< 0.5s)
            if len(chunk) < sr * 0.5:
                continue

            # Write chunk to temp file
            chunk_path = wav_path.with_suffix(".chunk.wav")
            sf.write(str(chunk_path), chunk, sr)

            try:
                res = model.generate(
                    str(chunk_path),
                    granularity="utterance",
                    extract_embedding=False,
                )
                w_scores = parse_scores(res[0]["scores"])
                w_labeled = {EMOTION_LABELS[i]: round(s, 4)
                             for i, s in enumerate(w_scores)}
                w_top = max(w_labeled, key=w_labeled.get)
                windows.append({
                    "start_sec": round(start_sample / sr, 2),
                    "end_sec": round(end_sample / sr, 2),
                    "top_emotion": w_top,
                    "confidence": w_labeled[w_top],
                    "all_scores": w_labeled,
                })
            finally:
                chunk_path.unlink(missing_ok=True)

        # Build emotion segments (consecutive windows with same emotion)
        segments = []
        if windows:
            seg_start = windows[0]["start_sec"]
            seg_emotion = windows[0]["top_emotion"]
            seg_confidences = [windows[0]["confidence"]]

            for w in windows[1:]:
                if w["top_emotion"] != seg_emotion:
                    segments.append({
                        "emotion": seg_emotion,
                        "start_sec": seg_start,
                        "end_sec": w["start_sec"],
                        "duration_sec": round(w["start_sec"] - seg_start, 2),
                        "avg_confidence": round(
                            sum(seg_confidences) / len(seg_confidences), 4),
                    })
                    seg_start = w["start_sec"]
                    seg_emotion = w["top_emotion"]
                    seg_confidences = [w["confidence"]]
                else:
                    seg_confidences.append(w["confidence"])

            segments.append({
                "emotion": seg_emotion,
                "start_sec": seg_start,
                "end_sec": windows[-1]["end_sec"],
                "duration_sec": round(
                    windows[-1]["end_sec"] - seg_start, 2),
                "avg_confidence": round(
                    sum(seg_confidences) / len(seg_confidences), 4),
            })

        # Emotion distribution
        emotion_time = {}
        for seg in segments:
            emotion_time[seg["emotion"]] = (
                emotion_time.get(seg["emotion"], 0) + seg["duration_sec"]
            )
        distribution = {
            e: round(t / total_duration * 100, 1)
            for e, t in sorted(emotion_time.items(),
                                key=lambda x: x[1], reverse=True)
        }

        return {
            "file": str(video_path),
            "duration_sec": round(total_duration, 2),
            "overall": overall,
            "windows": windows,
            "segments": segments,
            "emotion_distribution_pct": distribution,
        }

    finally:
        wav_path.unlink(missing_ok=True)


def main():
    video_paths = sys.argv[1:]
    if not video_paths:
        print("Usage: emotion2vec_analyze.py <video1.mp4> [video2.mp4 ...]")
        sys.exit(1)

    print("Loading emotion2vec+large model on GPU...", flush=True)
    from funasr import AutoModel

    model = AutoModel(
        model="iic/emotion2vec_plus_large",
        device="cuda:0",
        hub="hf",
        disable_update=True,
    )
    print("Model loaded.\n", flush=True)

    all_results = []
    for vp in video_paths:
        path = Path(vp)
        print(f"Analyzing: {path.name}...", flush=True)
        result = analyze_video(path, model)
        all_results.append(result)

        # Print summary
        o = result["overall"]
        print(f"  Duration: {result['duration_sec']:.1f}s")
        print(f"  Overall: {o['top_emotion']} ({o['confidence']:.1%})")
        print(f"  Segments: {len(result['segments'])}")
        for seg in result["segments"]:
            print(f"    {seg['start_sec']:6.1f}s - {seg['end_sec']:6.1f}s  "
                  f"{seg['emotion']:>10s}  ({seg['avg_confidence']:.1%})")
        dist = result["emotion_distribution_pct"]
        print(f"  Distribution: "
              f"{', '.join(f'{e} {p}%' for e, p in dist.items())}")
        print()

    # Write full results
    out_path = Path(video_paths[0]).parent / "emotion2vec_analysis.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Full results saved to: {out_path}")


if __name__ == "__main__":
    main()
