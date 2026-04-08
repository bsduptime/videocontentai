"""Brand configuration loader.

Loads brand config from assets/brands/{name}/brand.json.
Designed to be pluggable — when the content repo integrates,
this module can be swapped to read from its data layer instead of files.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .models import (
    BrandConfig,
    Branding,
    Manifest,
    PlatformThumbnailConfig,
    ThumbnailTemplate,
    WatermarkPosition,
)

logger = logging.getLogger(__name__)

# Default brand asset directories (searched in order)
_BRANDS_DIRS = [
    Path("assets/brands"),
    Path(__file__).resolve().parent.parent.parent / "assets" / "brands",
]

_FONTS_DIRS = [
    Path("assets/fonts"),
    Path(__file__).resolve().parent.parent.parent / "assets" / "fonts",
]


def load_manifest(slug_dir: str | Path) -> Manifest | None:
    """Load manifest.json from a slug input directory.

    Returns None if no manifest exists (legacy flow).
    """
    path = Path(slug_dir) / "manifest.json"
    if not path.exists():
        return None
    return Manifest.model_validate_json(path.read_text())


def load_brand(name: str) -> BrandConfig | None:
    """Load brand config by name from assets/brands/{name}/brand.json.

    Returns None if the brand directory or config doesn't exist.
    """
    if not name:
        return None

    for brands_dir in _BRANDS_DIRS:
        brand_dir = brands_dir / name
        config_path = brand_dir / "brand.json"
        if config_path.exists():
            return _parse_brand_json(config_path, brand_dir)

    logger.warning("Brand not found: %s", name)
    return None


def _parse_brand_json(config_path: Path, brand_dir: Path) -> BrandConfig:
    """Parse brand.json into a BrandConfig, resolving relative paths."""
    raw = json.loads(config_path.read_text())

    colors = raw.get("colors", {})
    fonts = raw.get("fonts", {})
    person = raw.get("person", {})
    watermark = raw.get("watermark", {})
    templates = raw.get("templates", {})
    thumb = raw.get("thumbnail", {})

    # Resolve font paths
    font_heading = _resolve_font(fonts.get("heading", "Montserrat-Bold.ttf"), brand_dir)
    font_body = _resolve_font(fonts.get("body", "BebasNeue-Regular.ttf"), brand_dir)

    # Build thumbnail template with per-platform config
    yt_raw = thumb.get("youtube", {})
    ig_raw = thumb.get("instagram", {})

    thumbnail = ThumbnailTemplate(
        primary_color=colors.get("primary", "#336791"),
        accent_color=colors.get("accent", "#F5A623"),
        font_impact=font_heading,
        font_readable=font_body,
        font_scale=yt_raw.get("font_scale", 1.2),
        logo_scale=0.08,
        person_description=person.get("description", ""),
        text_style=yt_raw.get("text_style", "line1_white_line2_red"),
        youtube=PlatformThumbnailConfig(**yt_raw) if yt_raw else PlatformThumbnailConfig(),
        instagram=PlatformThumbnailConfig(
            text_style=ig_raw.get("text_style", "centered_bold"),
            font_scale=ig_raw.get("font_scale", 1.0),
            use_face=ig_raw.get("use_face", False),
            show_accent_strip=ig_raw.get("show_accent_strip", True),
            background_frame_opacity=ig_raw.get("background_frame_opacity", 0.5),
            background_frame_brightness=ig_raw.get("background_frame_brightness", 0.25),
        )
        if ig_raw
        else PlatformThumbnailConfig(
            text_style="centered_bold",
            use_face=False,
            show_accent_strip=True,
        ),
    )

    # Parse watermark positions
    wm_16x9 = (
        WatermarkPosition(**watermark["position_16x9"])
        if "position_16x9" in watermark
        else WatermarkPosition()
    )
    wm_9x16 = (
        WatermarkPosition(**watermark["position_9x16"])
        if "position_9x16" in watermark
        else WatermarkPosition()
    )

    return BrandConfig(
        name=raw.get("name", ""),
        display_name=raw.get("display_name", ""),
        primary_color=colors.get("primary", "#336791"),
        accent_color=colors.get("accent", "#F5A623"),
        background_dark=colors.get("background_dark", "#1a2332"),
        background_light=colors.get("background_light", "#f5f5f5"),
        text_primary=colors.get("text_primary", "#ffffff"),
        text_secondary=colors.get("text_secondary", "#cccccc"),
        font_heading=font_heading,
        font_body=font_body,
        person_description=person.get("description", ""),
        face_reference=person.get("face_reference", ""),
        expression_default=person.get("expression_default", ""),
        watermark_file=watermark.get("file", ""),
        watermark_16x9=wm_16x9,
        watermark_9x16=wm_9x16,
        intro_16x9=templates.get("intro_16x9", ""),
        intro_9x16=templates.get("intro_9x16", ""),
        outro_16x9=templates.get("outro_16x9", ""),
        outro_9x16=templates.get("outro_9x16", ""),
        thumbnail=thumbnail,
    )


def brand_to_branding(brand: BrandConfig) -> Branding:
    """Convert a BrandConfig to the legacy Branding model.

    Bridge for stages that still read from Branding (watermark, intro_outro).
    Will be removed when those stages read BrandConfig directly.
    """
    return Branding(
        intro_16x9=brand.intro_16x9,
        intro_9x16=brand.intro_9x16,
        outro_16x9=brand.outro_16x9,
        outro_9x16=brand.outro_9x16,
        watermark=brand.watermark_file,
        watermark_16x9=brand.watermark_16x9,
        watermark_9x16=brand.watermark_9x16,
        thumbnail=brand.thumbnail,
    )


def apply_manifest_overrides(brand: BrandConfig, manifest: Manifest) -> BrandConfig:
    """Apply per-job overrides from manifest onto brand config.

    Returns a new BrandConfig with overrides applied (non-empty fields win).
    """
    data = brand.model_dump()
    if manifest.primary_color:
        data["primary_color"] = manifest.primary_color
        data["thumbnail"]["primary_color"] = manifest.primary_color
    if manifest.accent_color:
        data["accent_color"] = manifest.accent_color
        data["thumbnail"]["accent_color"] = manifest.accent_color
    if manifest.person_description:
        data["person_description"] = manifest.person_description
        data["thumbnail"]["person_description"] = manifest.person_description
    return BrandConfig.model_validate(data)


def _resolve_font(filename: str, brand_dir: Path) -> str:
    """Resolve a font filename to a full path.

    Checks brand dir first, then shared fonts dirs.
    """
    # Brand-specific font
    brand_font = brand_dir / "fonts" / filename
    if brand_font.exists():
        return str(brand_font)

    # Shared fonts
    for fonts_dir in _FONTS_DIRS:
        shared = fonts_dir / filename
        if shared.exists():
            return str(shared)

    # Return as-is — let the caller handle missing fonts
    return f"assets/fonts/{filename}"
