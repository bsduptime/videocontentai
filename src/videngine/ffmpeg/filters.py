"""Filter graph builders for FFmpeg."""

from __future__ import annotations


def watermark_overlay(
    position: str = "bottom_right",
    opacity: float = 0.3,
    scale: float = 0.08,
) -> str:
    """Build a filter graph string for watermark overlay.

    Args:
        position: One of "bottom_right", "bottom_left", "top_right", "top_left", "center"
        opacity: 0.0-1.0
        scale: Fraction of video width for watermark width
    """
    # Scale watermark relative to main video width
    scale_filter = f"[1:v]scale=iw*{scale}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm]"

    position_map = {
        "bottom_right": "W-w-20:H-h-20",
        "bottom_left": "20:H-h-20",
        "top_right": "W-w-20:20",
        "top_left": "20:20",
        "center": "(W-w)/2:(H-h)/2",
    }
    pos = position_map.get(position, position_map["bottom_right"])

    return f"{scale_filter};[0:v][wm]overlay={pos}"


def crop_for_aspect(
    target_width: int,
    target_height: int,
    focus: str = "center",
) -> str:
    """Build crop + scale filter for target aspect ratio.

    Args:
        target_width: Output width
        target_height: Output height
        focus: "center", "left_third", or "right_third"
    """
    # Calculate crop dimensions to match target aspect ratio
    crop_w = f"ih*{target_width}/{target_height}"
    crop_h = "ih"

    if focus == "left_third":
        x_offset = "0"
    elif focus == "right_third":
        x_offset = f"iw-{crop_w}"
    else:  # center
        x_offset = f"(iw-{crop_w})/2"

    return f"crop={crop_w}:{crop_h}:{x_offset}:0,scale={target_width}:{target_height}"
