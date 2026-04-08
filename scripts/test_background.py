#!/usr/bin/env python3
"""Quick standalone test of background replacement on an existing clip."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from videngine.config import BackgroundConfig, Config, EncodingConfig

TEST_CLIP = "/mnt/sdcard/videngine-jobs/IMG_1971-20260318_191317/clips/hook_loudnorm.mp4"
OUTPUT_DIR = "/mnt/sdcard/videngine-jobs/_bg_test"


def main():
    clip = TEST_CLIP
    if len(sys.argv) > 1:
        clip = sys.argv[1]

    if not Path(clip).exists():
        print(f"Test clip not found: {clip}")
        print("Usage: python scripts/test_background.py [path_to_clip.mp4]")
        sys.exit(1)

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy test clip to output dir so the stage can write alongside it
    import shutil

    test_path = out_dir / "input.mp4"
    if not test_path.exists():
        print(f"Copying test clip to {test_path}...")
        shutil.copy2(clip, test_path)

    # Configure
    config = Config()
    config.background = BackgroundConfig(
        enabled=True,
        background_type="blur",
        blur_strength=21,
        downsample_ratio=0.25,
    )
    # Use libx264 for test (avoid nvmpi issues)
    config.encoding = EncodingConfig(codec="libx264", crf=20)

    from videngine.stages.background import run_background

    clip_paths = {"test": str(test_path)}

    print(f"\nInput: {test_path}")
    print(f"Background type: {config.background.background_type}")
    print(f"Downsample ratio: {config.background.downsample_ratio}")
    print()

    start = time.time()
    result = run_background(clip_paths, str(out_dir), config)
    elapsed = time.time() - start

    print(f"\nDone in {elapsed:.1f}s")
    for name, path in result.items():
        size_mb = Path(path).stat().st_size / 1024 / 1024
        print(f"  {name}: {path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
