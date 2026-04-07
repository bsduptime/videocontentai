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
    moods_file: str = "config/cut_specs/moods.json"  # mood definitions
    music_dir: str = "assets/music"  # mood audio files: {music_dir}/{mood_name}.mp3
    music_volume: float = 0.10  # 0.0-1.0, default mix level under speech
    loudnorm_target_lufs: float = -16.0  # EBU R128 target
    loudnorm_true_peak: float = -1.5  # dBTP ceiling
    loudnorm_lra: float = 11.0  # loudness range


@dataclass
class AudioProfileConfig:
    denoise_atten_lim_db: float = 0.0  # 0 = unlimited
    compress_threshold_db: float = -20.0
    compress_ratio: float = 3.0
    compress_attack_ms: float = 5.0
    compress_release_ms: float = 200.0
    compress_knee_db: float = 6.0
    compress_makeup_db: float = 2.0


@dataclass
class AudioConfig:
    denoise: bool = True
    profiles: dict[str, AudioProfileConfig] = field(
        default_factory=lambda: {
            "macbook": AudioProfileConfig(),
            "iphone": AudioProfileConfig(
                compress_threshold_db=-18.0,
                compress_ratio=1.5,
                compress_attack_ms=10.0,
                compress_release_ms=250.0,
                compress_knee_db=8.0,
                compress_makeup_db=1.0,
            ),
        }
    )

    def get_profile(self, name: str) -> AudioProfileConfig:
        """Get a named profile, falling back to macbook defaults."""
        return self.profiles.get(name, self.profiles["macbook"])


@dataclass
class EncodingConfig:
    codec: str = "h264_nvmpi"
    crf: int = 20  # only used by libx264 fallback
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"


@dataclass
class ThumbnailConfig:
    enabled: bool = True
    comfyui_url: str = "http://localhost:8188"  # Local ComfyUI (preferred)
    flux_api_url: str = "https://api.bfl.ai/v1/flux-kontext"  # Cloud fallback
    face_reference_dir: str = "assets/faces"
    fonts_dir: str = "assets/fonts"
    fallback_only: bool = False  # Force Pillow-only mode (no image gen)


@dataclass
class Config:
    paths: PathsConfig = field(default_factory=PathsConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    encoding: EncodingConfig = field(default_factory=EncodingConfig)
    thumbnail: ThumbnailConfig = field(default_factory=ThumbnailConfig)


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
                "thumbnail": cfg.thumbnail,
            }
            for section_name, target in section_map.items():
                if section_name in data:
                    _apply_section(target, data[section_name])

            # Load audio config (has nested profiles)
            if "audio" in data:
                audio_data = data["audio"]
                if "denoise" in audio_data:
                    cfg.audio.denoise = audio_data["denoise"]
                if "profiles" in audio_data:
                    for name, profile_data in audio_data["profiles"].items():
                        profile = AudioProfileConfig()
                        _apply_section(profile, profile_data)
                        cfg.audio.profiles[name] = profile

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
            "thumbnail": cfg.thumbnail,
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
