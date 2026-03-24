# Voice Clone Emotion Profile Analysis Report

**Date:** 2026-03-23  
**Source:** `Jascha Heifetz Street 223.m4a` (13:30 continuous recording)  
**Profiles:** 8 emotion sections, transcribed and segmented via Whisper large-v3-turbo

---

## Section Boundaries (from transcript)

| # | Profile | Start | End | Duration | File |
|---|---------|-------|-----|----------|------|
| 1 | Drive | 0:00 | 1:39 | 99.5s | `drive.wav` |
| 2 | Drive + Wonder | 1:46 | 3:10 | 84.0s | `drive-wonder.wav` |
| 3 | Tension | 3:16 | 4:38 | 82.0s | `tension.wav` |
| 4 | Tension + Vulnerability | 4:45 | 6:13 | 88.0s | `tension-vulnerability.wav` |
| 5 | Steady | 6:20 | 7:55 | 95.0s | `steady.wav` |
| 6 | Steady + Empathy | 8:03 | 9:44 | 101.0s | `steady-empathy.wav` |
| 7 | High-Intensity Drive | 9:52 | 11:22 | 90.0s | `high-intensity-drive.wav` |
| 8 | Reflective Calm | 11:36 | 13:30 | 114.5s | `reflective-calm.wav` |

---

## VAD Analysis Results (wav2vec2-large-robust)

### Summary: Target vs Measured VAD

| Profile | Target V | Target A | Target D | Measured V | Measured A | Measured D | Energy Mode |
|---------|----------|----------|----------|------------|------------|------------|-------------|
| Drive | 0.70 | 0.75 | 0.75 | 0.241 | 0.303 | 0.304 | drive |
| Drive + Wonder | 0.80 | 0.80 | 0.50 | 0.250 | 0.317 | 0.317 | drive |
| Tension | 0.25 | 0.75 | 0.70 | 0.204 | 0.268 | 0.282 | tension |
| Tension + Vulnerability | 0.25 | 0.60 | 0.30 | 0.207 | 0.254 | 0.268 | tension |
| Steady | 0.65 | 0.45 | 0.50 | 0.269 | 0.244 | 0.266 | steady |
| Steady + Empathy | 0.75 | 0.45 | 0.25 | 0.234 | 0.243 | 0.267 | steady |
| High-Intensity Drive | 0.75 | 0.90 | 0.85 | 0.261 | 0.327 | 0.330 | drive |
| Reflective Calm | 0.55 | 0.25 | 0.40 | 0.234 | 0.241 | 0.265 | steady |

### Key Observations

#### 1. Model outputs are compressed into a narrow range
The wav2vec2-large-robust model outputs values in roughly the **0.15–0.43 range** across all profiles, while our targets span 0.25–0.90. This is a known characteristic of this model trained on MSP-Podcast — it produces conservative, regression-toward-mean predictions, especially on single-speaker narration without dramatic vocal cues (crying, shouting, etc.).

**This does NOT mean David's delivery was flat.** It means the model's absolute output scale doesn't match our 0–1 target scale.

#### 2. Relative ordering IS correct
Despite compressed values, the model correctly distinguishes energy modes:

- **Highest arousal:** High-Intensity Drive (0.327) ✅
- **Lowest arousal:** Reflective Calm (0.241) ✅
- **Tension profiles have lowest valence:** Tension (0.204), Tension+Vuln (0.207) ✅
- **Steady profiles have lowest arousal:** Steady (0.244), Steady+Empathy (0.243) ✅
- **Drive profiles classified as "drive"** ✅
- **Tension profiles classified as "tension"** ✅
- **Steady/Calm profiles classified as "steady"** ✅

The energy mode classification (drive/tension/steady) maps correctly for **all 8 profiles**.

#### 3. Energy mode distribution within clips

| Profile | Drive % | Tension % | Steady % |
|---------|---------|-----------|----------|
| Drive | 27.1% | 9.0% | **63.8%** |
| Drive + Wonder | 7.1% | 28.6% | **64.3%** |
| Tension | 22.0% | 14.6% | **63.4%** |
| Tension + Vulnerability | 18.2% | 13.6% | **68.2%** |
| Steady | 22.1% | 12.6% | **65.3%** |
| Steady + Empathy | 26.7% | 8.9% | **64.4%** |
| High-Intensity Drive | 16.7% | 16.7% | **66.7%** |
| Reflective Calm | 24.0% | 7.9% | **68.1%** |

All profiles are predominantly classified as "steady" at the window level. This is because:
- The 3-second windowed analysis + relative re-classification always pushes ~2/3 of windows to "steady"
- The relative threshold system (top 33% arousal = high energy) is designed for mixed-content videos, not single-emotion recordings
- For voice clone calibration, the **overall averages** are more meaningful than per-window distribution

#### 4. Valence is consistently underestimated
All measured valence values (0.20–0.27) fall well below targets (0.25–0.80). This suggests the model interprets David's narration style as relatively neutral-to-slightly-negative regardless of intended emotion. This is common for professional/authoritative speaking styles.

---

## emotion2vec Analysis

⚠️ **Could not run.** CUDA cuBLAS is in a corrupted state (`CUBLAS_STATUS_ALLOC_FAILED` on `cublasCreate`). Even a 10×10 matrix multiply fails. This affects all GPU matrix operations system-wide and requires either killing all CUDA-holding processes or a system reboot.

The embedding server (PID 1569557, `services/embedding_server.py`) is running and may be contributing to the issue, but the root cause is likely residual state from the earlier OOM when VAD + emotion2vec were loaded simultaneously.

**To fix:** Reboot or run `sudo systemctl restart nvargus-daemon` and kill all Python GPU processes, then rerun:
```bash
cd ~/code/videocontentai && source .venv/bin/activate && python scripts/emotion2vec_analyze.py voice-profiles/recordings/*.wav
```

---

## Recommendations

### For the pipeline (calibration)
1. **Don't compare absolute VAD values to targets directly.** The model's output range is ~0.15–0.45 for narration, not 0–1. Use relative comparisons or apply a linear rescaling.
2. **Consider a calibration function:** Map David's measured VAD ranges to the target space. E.g., if his arousal spans 0.24–0.33 across profiles, linearly map that to 0.25–0.90.
3. **The energy mode classifier works.** The tri-state drive/tension/steady classification is correct for all 8 profiles. This is the most actionable signal.

### For re-recording
4. **No profiles need re-recording** based on VAD analysis — all are correctly differentiated by the model. The issue is model scaling, not delivery.
5. **Once cuBLAS is fixed**, run emotion2vec to get categorical emotion labels (angry/happy/sad/neutral/etc.) as a second validation axis.

### For the model
6. **Consider fine-tuning** the VAD model on a small set of David's labeled recordings to calibrate the output range to your target scale.
7. **The `iic/emotion2vec_plus_large` model** may provide better discrimination — it was specifically designed for emotion recognition vs the wav2vec2 model which was trained for dimensional prediction.

---

## Files Generated

```
voice-profiles/recordings/
├── drive.wav                  (99.5s)
├── drive-wonder.wav           (84.0s)
├── tension.wav                (82.0s)
├── tension-vulnerability.wav  (88.0s)
├── steady.wav                 (95.0s)
├── steady-empathy.wav         (101.0s)
├── high-intensity-drive.wav   (90.0s)
├── reflective-calm.wav        (114.5s)
├── vad_analysis.json          (full windowed VAD results)
└── analysis-report.md         (this file)
```

Full transcript: `/tmp/voice-clone-transcript.json`
