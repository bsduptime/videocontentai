"""TOML + environment variable config loading."""

from __future__ import annotations

import os
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]
from dataclasses import dataclass, field
from pathlib import Path


def _resolve(path_str: str) -> str:
    return str(Path(path_str).expanduser())


@dataclass
class PathsConfig:
    working_dir: str = "~/.videngine/jobs"


@dataclass
class WhisperConfig:
    model_path: str = "~/.videngine/models/ggml-large-v3-turbo.bin"
    language: str = "en"
    threads: int = 4


@dataclass
class AIConfig:
    model: str = "claude-opus-4-20250115"
    max_tokens: int = 8192
    temperature: float = 0.3
    target_total_duration: int = 300


@dataclass
class VoiceConfig:
    engine: str = "chatterbox"
    reference_audio: str = "assets/voice_refs/founder.wav"


@dataclass
class VideoConfig:
    intro_template: str = "assets/intros/default.mp4"
    outro_template: str = "assets/outros/default.mp4"
    watermark: str = "assets/watermarks/logo.png"
    watermark_position: str = "bottom_right"
    watermark_opacity: float = 0.3
    watermark_scale: float = 0.08


@dataclass
class EncodingConfig:
    codec: str = "libx264"
    crf: int = 20
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"


@dataclass
class Config:
    paths: PathsConfig = field(default_factory=PathsConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    encoding: EncodingConfig = field(default_factory=EncodingConfig)


def _apply_section(target: object, data: dict) -> None:
    for key, value in data.items():
        if hasattr(target, key):
            setattr(target, key, value)


def load_config(config_path: str | Path | None = None) -> Config:
    """Load config from TOML file, with env var overrides."""
    cfg = Config()

    # Find config file
    if config_path is None:
        candidates = [
            Path("videngine.toml"),
            Path("config/default.toml"),
            Path.home() / ".videngine" / "config.toml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break

    if config_path is not None:
        path = Path(config_path)
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
            section_map = {
                "paths": cfg.paths,
                "whisper": cfg.whisper,
                "ai": cfg.ai,
                "voice": cfg.voice,
                "video": cfg.video,
                "encoding": cfg.encoding,
            }
            for section_name, target in section_map.items():
                if section_name in data:
                    _apply_section(target, data[section_name])

    # Env var overrides (VIDENGINE_AI_MODEL, VIDENGINE_WHISPER_LANGUAGE, etc.)
    prefix = "VIDENGINE_"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("_", 1)
        if len(parts) != 2:
            continue
        section_name, field_name = parts
        section_map = {
            "paths": cfg.paths,
            "whisper": cfg.whisper,
            "ai": cfg.ai,
            "voice": cfg.voice,
            "video": cfg.video,
            "encoding": cfg.encoding,
        }
        target = section_map.get(section_name)
        if target and hasattr(target, field_name):
            current = getattr(target, field_name)
            if isinstance(current, int):
                setattr(target, field_name, int(value))
            elif isinstance(current, float):
                setattr(target, field_name, float(value))
            else:
                setattr(target, field_name, value)

    # Resolve paths after all overrides are applied
    cfg.paths.working_dir = _resolve(cfg.paths.working_dir)
    cfg.whisper.model_path = _resolve(cfg.whisper.model_path)

    return cfg
