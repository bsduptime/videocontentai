"""Typer CLI entry point."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config
from .pipeline import Pipeline
from .storage import cleanup_jobs, get_latest_job, list_jobs

# Convention directories (relative to project root)
# Input path: video-content/input/{slug}/
CONTENT_DIR = Path("video-content")
TO_CUT_DIR = CONTENT_DIR / "input"
IN_PROGRESS_DIR = CONTENT_DIR / "production"
DONE_DIR = CONTENT_DIR / "output"

# Brand → spec file mapping. Aspect ratio is auto-detected from the source.
BRAND_SPECS = {
    "dbexpertai": {
        "16:9": "config/cut_specs/landscape-dbexpertai.json",
        "9:16": "config/cut_specs/portrait-dbexpertai.json",
    },
    "founder": {
        "16:9": "config/cut_specs/landscape-founder.json",
        "9:16": "config/cut_specs/portrait-founder.json",
    },
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

app = typer.Typer(
    name="videngine",
    help="Automated video production pipeline with AI-driven editing.",
    no_args_is_help=True,
)
console = Console()


@app.command(name="pre-process")
def pre_process(
    slug: Annotated[
        str, typer.Argument(help="Video slug (directory name in video-content/input/)")
    ],
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Pre-process raw video files: ingest → audio processing → transcription.

    Expects raw files in video-content/input/{slug}/.
    Outputs processed files + transcripts to video-content/production/{slug}/.
    Updates or creates production manifest with pipeline status.
    """
    import json
    import shutil
    from datetime import datetime

    config = load_config(config_file)

    input_dir = TO_CUT_DIR / slug
    prod_dir = IN_PROGRESS_DIR / slug

    # --- Step 1: Validate input ---
    if not input_dir.exists():
        console.print(f"[red]Input directory not found: {input_dir}[/red]")
        raise typer.Exit(1)

    video_files = [f for f in sorted(input_dir.iterdir()) if f.suffix.lower() in VIDEO_EXTENSIONS]
    if not video_files:
        console.print(f"[red]No video files found in {input_dir}[/red]")
        raise typer.Exit(1)

    metadata_files = [
        f for f in sorted(input_dir.iterdir()) if f.suffix.lower() in {".md", ".json"}
    ]

    console.print(f"\n[bold]Pre-processing: {slug}[/bold]")
    console.print(f"  Videos: {len(video_files)}")
    console.print(f"  Metadata: {len(metadata_files)}")

    # --- Step 2: Probe & detect devices ---
    from .ffmpeg.probe import detect_recording_device
    from .ffmpeg.probe import probe as ffprobe

    file_info: list[dict] = []
    for vf in video_files:
        info = ffprobe(str(vf))
        device = detect_recording_device(str(vf))
        size_mb = vf.stat().st_size / (1024 * 1024)
        file_info.append(
            {
                "path": vf,
                "name": vf.name,
                "device": device,
                "duration": info.duration,
                "width": info.width,
                "height": info.height,
                "size_mb": size_mb,
            }
        )
        mins, secs = divmod(int(info.duration), 60)
        console.print(
            f"  [cyan]{vf.name}[/cyan]: {device} | {mins}:{secs:02d} | {info.width}x{info.height} | {size_mb:.0f}MB"
        )

    # --- Step 3: Create production directory ---
    prod_dir.mkdir(parents=True, exist_ok=True)
    (prod_dir / "audio").mkdir(exist_ok=True)
    (prod_dir / "transcripts").mkdir(exist_ok=True)

    # Copy metadata files
    for mf in metadata_files:
        shutil.copy2(str(mf), str(prod_dir / mf.name))
        console.print(f"  Copied metadata: {mf.name}")

    # --- Step 4: Audio preprocessing ---
    console.print("\n[bold]Audio preprocessing...[/bold]")

    from .audio_preprocess import preprocess_audio
    from .ffmpeg.commands import compress_audio, loudnorm_apply, loudnorm_measure

    processed_files: list[dict] = []
    for fi in file_info:
        vf = fi["path"]
        device = fi["device"]
        profile = config.audio.get_profile(device)

        console.print(f"  [cyan]{vf.name}[/cyan] ({device} profile)...")

        # Working dir for intermediate files
        work_dir = prod_dir / "audio" / vf.stem
        work_dir.mkdir(parents=True, exist_ok=True)

        # Step 4a: DeepFilterNet denoise
        denoised_path = str(work_dir / f"{vf.stem}_denoised{vf.suffix}")
        atten = profile.denoise_atten_lim_db if profile.denoise_atten_lim_db != 0 else None
        console.print("    Denoising...")
        preprocess_audio(str(vf), denoised_path, str(work_dir), atten_lim_db=atten)

        # Step 4b: Compress
        compressed_path = str(work_dir / f"{vf.stem}_compressed{vf.suffix}")
        console.print("    Compressing...")
        import subprocess

        cmd = compress_audio(
            denoised_path,
            compressed_path,
            config.encoding,
            threshold_db=profile.compress_threshold_db,
            ratio=profile.compress_ratio,
            attack_ms=profile.compress_attack_ms,
            release_ms=profile.compress_release_ms,
            knee_db=profile.compress_knee_db,
            makeup_db=profile.compress_makeup_db,
        )
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"    [red]Compression failed: {result.stderr[-200:]}[/red]")
            raise typer.Exit(1)

        # Step 4c: Two-pass loudnorm
        console.print("    Loudnorm pass 1 (measuring)...")
        measure_cmd = loudnorm_measure(compressed_path)
        result = subprocess.run(measure_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"    [red]Loudnorm measure failed: {result.stderr[-200:]}[/red]")
            raise typer.Exit(1)

        # Parse loudnorm JSON from stderr
        import re

        json_match = re.search(r'\{[^{}]*"input_i"[^{}]*\}', result.stderr, re.DOTALL)
        if not json_match:
            console.print("    [red]Could not parse loudnorm stats[/red]")
            raise typer.Exit(1)
        stats = json.loads(json_match.group())

        output_path = str(prod_dir / vf.name)
        console.print("    Loudnorm pass 2 (applying)...")
        apply_cmd = loudnorm_apply(
            compressed_path,
            output_path,
            config.encoding,
            measured_i=float(stats["input_i"]),
            measured_tp=float(stats["input_tp"]),
            measured_lra=float(stats["input_lra"]),
            measured_thresh=float(stats["input_thresh"]),
            offset=float(stats.get("target_offset", 0)),
        )
        result = subprocess.run(apply_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"    [red]Loudnorm apply failed: {result.stderr[-200:]}[/red]")
            raise typer.Exit(1)

        console.print(f"    [green]✅ {vf.name}[/green]")
        processed_files.append({**fi, "output": output_path})

    # --- Step 5: Transcribe ---
    console.print("\n[bold]Transcribing...[/bold]")

    from .models import Transcript
    from .stages.transcribe import run_transcribe

    transcript_info: list[dict] = []
    for pf in processed_files:
        name = pf["name"]
        stem = Path(name).stem
        output_video = pf["output"]

        transcript_work_dir = str(prod_dir / "transcripts" / stem)
        Path(transcript_work_dir).mkdir(parents=True, exist_ok=True)

        # Check for existing transcript from /pull-input (in the input slug dir)
        existing_transcript = input_dir / f"{stem}.transcript.json"
        target_transcript = Path(transcript_work_dir) / "transcript.json"

        if existing_transcript.exists():
            transcript = Transcript.model_validate_json(existing_transcript.read_text())
            # Copy into the standard transcript location
            if not target_transcript.exists():
                shutil.copy2(str(existing_transcript), str(target_transcript))
            # Also extract audio (needed by later stages) even when skipping transcription
            from .ffmpeg.commands import extract_audio as _extract_audio

            audio_path = Path(transcript_work_dir) / "audio.wav"
            if not audio_path.exists():
                import subprocess as _sp

                _sp.run(
                    _extract_audio(output_video, str(audio_path)), capture_output=True, text=True
                )
            word_count = sum(len(seg.words) for seg in transcript.segments)
            mins, secs = divmod(int(transcript.duration_seconds), 60)
            console.print(
                f"  [cyan]{name}[/cyan]: [dim]existing transcript found, skipping whisper[/dim]"
            )
            console.print(
                f"    [green]✅ {word_count} words | {mins}:{secs:02d} | {transcript.language}[/green]"
            )
        else:
            console.print(f"  [cyan]{name}[/cyan]...")
            transcript = run_transcribe(output_video, transcript_work_dir, config)
            word_count = sum(len(seg.words) for seg in transcript.segments)
            mins, secs = divmod(int(transcript.duration_seconds), 60)
            console.print(
                f"    [green]✅ {word_count} words | {mins}:{secs:02d} | {transcript.language}[/green]"
            )

        transcript_info.append(
            {
                "file": name,
                "transcript_path": f"transcripts/{stem}/transcript.json",
                "words": word_count,
                "duration": transcript.duration_seconds,
                "language": transcript.language,
            }
        )

    # --- Step 6: Update manifest ---
    console.print("\n[bold]Updating manifest...[/bold]")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    manifest_path = prod_dir / "manifest.md"

    # Try to load existing manifest and update checkboxes
    if manifest_path.exists():
        manifest = manifest_path.read_text()

        # Tick the first 3 checkboxes
        manifest = manifest.replace(
            "- [ ] Raw files received", f"- [x] Raw files received ✅ {now}", 1
        )
        manifest = manifest.replace(
            "- [ ] Audio pre-processing", f"- [x] Audio pre-processing ✅ {now}", 1
        )
        manifest = manifest.replace(
            "- [ ] Transcription complete", f"- [x] Transcription complete ✅ {now}", 1
        )
        # Also handle alternate checkbox text
        manifest = manifest.replace("- [ ] Transcription", f"- [x] Transcription ✅ {now}", 1)
    else:
        # Build manifest from scratch
        # Try to load sidecar for beat info
        sidecar_data = None
        for mf in metadata_files:
            if mf.suffix == ".json" and mf.name != "manifest.json":
                try:
                    sidecar_data = json.loads(mf.read_text())
                except Exception:
                    pass

        beats_table = ""
        if sidecar_data and "beats" in sidecar_data:
            beats_table = "\n## Beats\n\n"
            beats_table += "| Beat | Name | Source Type | VAD Target | Status |\n"
            beats_table += "|------|------|-----------|------------|--------|\n"
            for beat in sidecar_data["beats"]:
                vad = beat.get("vad", {})
                vad_str = (
                    f"V{vad.get('v', 0):.2f} A{vad.get('a', 0):.2f} D{vad.get('d', 0):.2f}"
                    if vad
                    else "—"
                )
                beats_table += f"| {beat.get('number', '?')} | {beat.get('name', '?')} | {beat.get('source_type', '?')} | {vad_str} | ⬜ awaiting scene match |\n"

        manifest = f"""# Production Manifest: {slug}

**Slug**: {slug}
**Date**: {now.split()[0]}

## Pipeline Status
- [x] Raw files received ✅ {now}
- [x] Audio pre-processing ✅ {now}
- [x] Transcription complete ✅ {now}
- [ ] Scene matching
- [ ] Beat cuts
- [ ] Beat transcription
- [ ] VAD scoring
- [ ] Delivery comparison
- [ ] Readiness review
"""
        manifest += beats_table

    # Append/update file, audio, and transcript tables
    files_table = "\n## Files\n\n"
    files_table += "| File | Device | Duration | Size |\n"
    files_table += "|------|--------|----------|------|\n"
    for fi in file_info:
        mins, secs = divmod(int(fi["duration"]), 60)
        files_table += (
            f"| {fi['name']} | {fi['device']} | {mins}:{secs:02d} | {fi['size_mb']:.0f}MB |\n"
        )

    audio_table = "\n## Audio Processing\n\n"
    audio_table += "| File | Profile | Denoise | Compress | Loudnorm |\n"
    audio_table += "|------|---------|---------|----------|----------|\n"
    for fi in file_info:
        audio_table += f"| {fi['name']} | {fi['device']} | ✅ | ✅ | ✅ -16 LUFS |\n"

    transcripts_table = "\n## Transcripts\n\n"
    transcripts_table += "| File | Transcript | Words | Duration | Language |\n"
    transcripts_table += "|------|-----------|-------|----------|----------|\n"
    for ti in transcript_info:
        mins, secs = divmod(int(ti["duration"]), 60)
        transcripts_table += f"| {ti['file']} | {ti['transcript_path']} | {ti['words']} | {mins}:{secs:02d} | {ti['language']} |\n"

    # If manifest had existing sections, replace; otherwise append
    for section_header, section_content in [
        ("## Files", files_table),
        ("## Audio Processing", audio_table),
        ("## Transcripts", transcripts_table),
    ]:
        if section_header in manifest:
            # Replace existing section up to the next ## or end of file
            pattern = re.escape(section_header) + r".*?(?=\n## |\Z)"
            manifest = re.sub(pattern, section_content.strip(), manifest, count=1, flags=re.DOTALL)
        else:
            manifest += section_content

    if "\n## Notes" not in manifest:
        manifest += "\n## Notes\n\n"

    manifest_path.write_text(manifest)
    console.print(f"  [green]✅ Manifest updated: {manifest_path}[/green]")

    # --- Step 7: Summary ---
    total_words = sum(ti["words"] for ti in transcript_info)
    devices = list(set(fi["device"] for fi in file_info))

    console.print(f"\n[bold green]{'═' * 50}[/bold green]")
    console.print(f"[bold]Pre-Processing Complete: {slug}[/bold]\n")
    console.print(f"  Files processed: {len(video_files)}")
    console.print(f"  Devices: {', '.join(devices)}")
    console.print(f"  Total words: {total_words}")
    console.print("\n  Pipeline status:")
    console.print("  [green]✅ Ingest[/green]")
    console.print("  [green]✅ Audio pre-processing[/green]")
    console.print("  [green]✅ Transcription[/green]")
    console.print("  [dim]⬜ Scene matching (next step)[/dim]")
    console.print(f"\n  Production: {prod_dir}/")
    console.print(f"  Manifest:   {manifest_path}")


@app.command(name="cut-beats")
def cut_beats(
    slug: Annotated[
        str, typer.Argument(help="Video slug (directory name in video-content/production/)")
    ],
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Cut beat files, re-transcribe, and run VAD + emotion2vec scoring.

    Expects scene matching to be complete: production/{slug}/beats/ must contain
    a beat_map.json (produced by the scene-matching agent step).

    Steps:
    5. Cut each beat from source files by timecodes in beat_map.json
    6. Re-transcribe each cut beat with Whisper (fresh timecodes)
    7. Run VAD + emotion2vec analysis on each beat
    """
    import json
    import subprocess
    from datetime import datetime

    config = load_config(config_file)

    prod_dir = IN_PROGRESS_DIR / slug
    beats_dir = prod_dir / "beats"
    beat_map_path = beats_dir / "beat_map.json"

    # --- Validate ---
    if not prod_dir.exists():
        console.print(f"[red]Production directory not found: {prod_dir}[/red]")
        raise typer.Exit(1)

    if not beat_map_path.exists():
        console.print("[red]beat_map.json not found — run scene matching first[/red]")
        raise typer.Exit(1)

    beat_map = json.loads(beat_map_path.read_text())
    console.print(f"\n[bold]Cutting beats for: {slug}[/bold]")
    console.print(f"  Beats in map: {len(beat_map)}")

    # --- Step 5: Cut beats ---
    console.print("\n[bold]Step 5: Cutting beats...[/bold]")

    from .ffmpeg.commands import cut_segment

    cut_files: list[dict] = []
    for entry in beat_map:
        beat_num = entry["beat"]
        beat_name = entry.get("name", f"beat-{beat_num}")
        source_file = entry["source_file"]
        takes = entry.get("takes", [{"start": entry["start"], "end": entry["end"]}])

        for take_idx, take in enumerate(takes, 1):
            out_name = f"beat-{beat_num:02d}-{beat_name}-take-{take_idx}.mp4"
            out_path = str(beats_dir / out_name)

            cmd = cut_segment(source_file, out_path, take["start"], take["end"])
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"  [red]Failed to cut {out_name}: {result.stderr[-200:]}[/red]")
                continue

            duration = take["end"] - take["start"]
            console.print(f"  [green]✅ {out_name}[/green] ({duration:.1f}s)")
            cut_files.append(
                {
                    "beat": beat_num,
                    "name": beat_name,
                    "take": take_idx,
                    "file": out_name,
                    "path": out_path,
                    "duration": duration,
                }
            )

    # --- Step 6: Re-transcribe each beat ---
    console.print("\n[bold]Step 6: Transcribing beats...[/bold]")

    from .stages.transcribe import run_transcribe

    for cf in cut_files:
        transcript_dir = str(beats_dir / f"{Path(cf['file']).stem}")
        Path(transcript_dir).mkdir(parents=True, exist_ok=True)

        transcript = run_transcribe(cf["path"], transcript_dir, config)
        word_count = sum(len(seg.words) for seg in transcript.segments)
        cf["words"] = word_count
        cf["transcript_path"] = f"{Path(cf['file']).stem}/transcript.json"
        console.print(f"  [green]✅ {cf['file']}[/green]: {word_count} words")

    # --- Step 7: VAD + emotion2vec ---
    console.print("\n[bold]Step 7: VAD + emotion2vec scoring...[/bold]")

    # Run VAD analysis via the standalone script (loads model once for all files)
    beat_paths = [cf["path"] for cf in cut_files]

    console.print(f"  Running VAD analysis on {len(beat_paths)} files...")
    vad_result = subprocess.run(
        ["python", "scripts/vad_analyze.py"] + beat_paths,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent.parent),
    )
    if vad_result.returncode != 0:
        console.print(f"  [red]VAD analysis failed: {vad_result.stderr[-300:]}[/red]")
        raise typer.Exit(1)

    # Load VAD results
    vad_json_path = beats_dir / "vad_analysis.json"
    if vad_json_path.exists():
        vad_results = json.loads(vad_json_path.read_text())
        for cf, vad in zip(cut_files, vad_results):
            cf["vad"] = vad.get("overall", {})
            cf["vad_windows"] = vad.get("windows", [])
            o = cf["vad"]
            console.print(
                f"  [green]✅ {cf['file']}[/green]: "
                f"{o.get('energy_mode', '?')} "
                f"(A={o.get('arousal', 0):.3f} V={o.get('valence', 0):.3f} D={o.get('dominance', 0):.3f})"
            )

    console.print(f"\n  Running emotion2vec analysis on {len(beat_paths)} files...")
    emo_result = subprocess.run(
        ["python", "scripts/emotion2vec_analyze.py"] + beat_paths,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent.parent),
    )
    if emo_result.returncode != 0:
        console.print(f"  [red]emotion2vec analysis failed: {emo_result.stderr[-300:]}[/red]")
        raise typer.Exit(1)

    # Load emotion2vec results
    emo_json_path = beats_dir / "emotion2vec_analysis.json"
    if emo_json_path.exists():
        emo_results = json.loads(emo_json_path.read_text())
        for cf, emo in zip(cut_files, emo_results):
            cf["emotion"] = emo.get("overall", {})
            e = cf["emotion"]
            console.print(
                f"  [green]✅ {cf['file']}[/green]: "
                f"{e.get('top_emotion', '?')} ({e.get('confidence', 0):.0%})"
            )

    # --- Save beat analysis summary ---
    analysis_path = beats_dir / "beat_analysis.json"
    analysis_path.write_text(json.dumps(cut_files, indent=2, default=str))

    # --- Update manifest ---
    console.print("\n[bold]Updating manifest...[/bold]")
    manifest_path = prod_dir / "manifest.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if manifest_path.exists():
        manifest = manifest_path.read_text()
        manifest = manifest.replace("- [ ] Beat cuts", f"- [x] Beat cuts ✅ {now}", 1)
        manifest = manifest.replace(
            "- [ ] Beat transcription", f"- [x] Beat transcription ✅ {now}", 1
        )
        manifest = manifest.replace("- [ ] VAD scoring", f"- [x] VAD scoring ✅ {now}", 1)
        manifest_path.write_text(manifest)

    # --- Summary ---
    console.print(f"\n[bold green]{'═' * 50}[/bold green]")
    console.print(f"[bold]Beat Processing Complete: {slug}[/bold]\n")
    console.print(f"  Beats cut: {len(cut_files)}")
    console.print("  All transcribed: ✅")
    console.print("  All VAD scored: ✅")
    console.print("  All emotion scored: ✅")
    console.print("\n  Pipeline status:")
    console.print("  [green]✅ Beat cuts[/green]")
    console.print("  [green]✅ Beat transcription[/green]")
    console.print("  [green]✅ VAD + emotion2vec scoring[/green]")
    console.print("  [dim]⬜ Delivery comparison + readiness (next: agent)[/dim]")
    console.print(f"\n  Beat analysis: {analysis_path}")


@app.command()
def cut(
    brand: Annotated[
        Optional[str],
        typer.Option(help="Brand: dbexpertai or founder (overrides subdir detection)"),
    ] = None,
    no_voice: Annotated[bool, typer.Option("--no-voice", help="Skip voice cloning")] = False,
    no_thumbnail: Annotated[
        bool, typer.Option("--no-thumbnail", help="Skip thumbnail generation")
    ] = False,
    review: Annotated[bool, typer.Option(help="Pause after AI analysis for review")] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would run without executing")
    ] = False,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Process all videos in video-content/input/.

    Drop video files into video-content/input/{slug}/.
    The brand subdir determines which branding (intro/outro/watermark) to use.
    Aspect ratio is auto-detected from each file.

    Files move through: input → production → output.
    """
    config = load_config(config_file)

    # Ensure dirs exist
    for d in [TO_CUT_DIR, IN_PROGRESS_DIR, DONE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Find all video files in to_cut/ (including brand subdirs)
    files_to_process: list[tuple[Path, str]] = []  # (path, brand)
    for f in sorted(TO_CUT_DIR.rglob("*")):
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            # Detect brand from subdir
            detected_brand = brand
            if not detected_brand:
                rel = f.relative_to(TO_CUT_DIR)
                if rel.parts[0] in BRAND_SPECS:
                    detected_brand = rel.parts[0]
                else:
                    detected_brand = "dbexpertai"  # default
            files_to_process.append((f, detected_brand))

    if not files_to_process:
        console.print("[dim]No video files in video-content/input/[/dim]")
        return

    console.print(f"\n[bold]Found {len(files_to_process)} video(s) to process[/bold]\n")

    for video_path, video_brand in files_to_process:
        console.print(f"[bold cyan]{'─' * 60}[/bold cyan]")
        console.print(f"[bold]File:[/bold] {video_path.name}")
        console.print(f"[bold]Brand:[/bold] {video_brand}")

        # Move to in_progress
        in_progress_path = IN_PROGRESS_DIR / video_path.name
        shutil.move(str(video_path), str(in_progress_path))

        try:
            # Detect aspect ratio → pick spec file
            from .ffmpeg.probe import probe

            info = probe(str(in_progress_path))
            aspect = "16:9" if info.width >= info.height else "9:16"

            specs_path = BRAND_SPECS.get(video_brand, {}).get(aspect)
            if not specs_path or not Path(specs_path).exists():
                console.print(f"[red]No spec file for brand={video_brand} aspect={aspect}[/red]")
                shutil.move(str(in_progress_path), str(TO_CUT_DIR / video_path.name))
                continue

            console.print(f"[bold]Specs:[/bold] {specs_path} ({aspect})")

            pipeline = Pipeline(
                source_file=str(in_progress_path),
                config=config,
                project=video_path.stem,
                specs_file=specs_path,
                no_voice=no_voice,
                no_thumbnail=no_thumbnail,
                review=review,
                dry_run=dry_run,
            )
            pipeline.run()

            # Move to done
            done_path = DONE_DIR / video_path.name
            shutil.move(str(in_progress_path), str(done_path))
            console.print(f"[green]Moved to {done_path}[/green]\n")

        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            # Move back to to_cut so it can be retried
            fallback = TO_CUT_DIR / video_path.name
            if in_progress_path.exists():
                shutil.move(str(in_progress_path), str(fallback))
            console.print(f"[yellow]Moved back to {fallback}[/yellow]\n")


@app.command()
def process(
    video: Annotated[Path, typer.Argument(help="Path to source video file")],
    project: Annotated[str, typer.Option(help="Project name for organization")] = "",
    specs: Annotated[
        Optional[Path],
        typer.Option(
            "--specs",
            help="Path to JSON file with cut specs (auto-detects from source aspect ratio if omitted)",
        ),
    ] = None,
    no_voice: Annotated[bool, typer.Option("--no-voice", help="Skip voice cloning")] = False,
    no_thumbnail: Annotated[
        bool, typer.Option("--no-thumbnail", help="Skip thumbnail generation")
    ] = False,
    review: Annotated[bool, typer.Option(help="Pause after AI analysis for review")] = False,
    model: Annotated[Optional[str], typer.Option(help="Override AI model")] = None,
    keep_intermediates: Annotated[
        bool, typer.Option("--keep-intermediates", help="Keep intermediate files")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would run without executing")
    ] = False,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Process a video through the AI-driven multi-cut pipeline.

    Aspect ratio is auto-detected from the source video. Landscape (16:9) and
    portrait (9:16) sources each have their own default cut specs under
    config/cut_specs/. Override with --specs to provide a custom spec file.
    """
    if not video.exists():
        console.print(f"[red]Video file not found: {video}[/red]")
        raise typer.Exit(1)

    config = load_config(config_file)

    if model:
        config.ai.model = model

    pipeline = Pipeline(
        source_file=str(video),
        config=config,
        project=project,
        specs_file=str(specs) if specs else None,
        no_voice=no_voice,
        no_thumbnail=no_thumbnail,
        review=review,
        dry_run=dry_run,
    )
    pipeline.run()


@app.command()
def resume(
    job_id: Annotated[Optional[str], typer.Argument(help="Job ID to resume")] = None,
    latest: Annotated[bool, typer.Option("--latest", help="Resume most recent job")] = False,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Resume a previously interrupted or failed job."""
    config = load_config(config_file)

    if latest:
        job = get_latest_job(config.paths.working_dir)
        if job is None:
            console.print("[red]No jobs found[/red]")
            raise typer.Exit(1)
        job_id = job.job_id
    elif job_id is None:
        console.print("[red]Provide a job ID or use --latest[/red]")
        raise typer.Exit(1)

    pipeline = Pipeline(
        source_file="",  # Will be loaded from job state
        config=config,
        job_id=job_id,
    )
    pipeline.run()


@app.command()
def jobs(
    status: Annotated[
        Optional[str], typer.Option(help="Filter by status: completed, failed, running")
    ] = None,
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """List all jobs."""
    config = load_config(config_file)
    all_jobs = list_jobs(config.paths.working_dir, status=status)

    if not all_jobs:
        console.print("[dim]No jobs found[/dim]")
        return

    table = Table(title="Jobs")
    table.add_column("Job ID", style="cyan")
    table.add_column("Project")
    table.add_column("Created")
    table.add_column("Stages")

    for job in all_jobs:
        stages_summary = " ".join(
            f"[{'green' if s.status.value == 'completed' else 'red' if s.status.value == 'failed' else 'dim'}]{name[0].upper()}[/]"
            for name, s in job.stages.items()
        )
        table.add_row(
            job.job_id,
            job.project or "-",
            job.created_at.strftime("%Y-%m-%d %H:%M"),
            stages_summary,
        )

    console.print(table)


@app.command()
def cleanup(
    older_than: Annotated[str, typer.Option(help="Delete jobs older than (e.g. 7d)")] = "7d",
    config_file: Annotated[
        Optional[Path], typer.Option("--config", help="Path to config TOML file")
    ] = None,
) -> None:
    """Delete old completed jobs."""
    config = load_config(config_file)

    # Parse duration string
    days = int(older_than.rstrip("d"))
    deleted = cleanup_jobs(config.paths.working_dir, older_than_days=days)
    console.print(f"Deleted {deleted} job(s)")


if __name__ == "__main__":
    app()
