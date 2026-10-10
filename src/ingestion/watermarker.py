"""
Nivima Video Watermarker Engine.
Applies an aesthetic, semi-transparent watermark on free-tier video exports using FFmpeg.
Prevents enterprise piracy on free tiers while turning every exported video into organic marketing.
"""

import os
import shutil
import subprocess

import structlog

log = structlog.get_logger()


def apply_watermark(
    input_video_path: str,
    output_video_path: str,
    watermark_text: str = "Made with NIVIMA",
    opacity: float = 0.55
) -> str:
    """
    Overlays a subtle semi-transparent watermark on the bottom-right corner.
    Falls back gracefully to copying input if FFmpeg drawtext filter is unavailable.
    """
    out_dir = os.path.dirname(output_video_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    ff_bin = shutil.which("ffmpeg") or "ffmpeg"

    # Drawtext filter placing watermark in bottom-right with 10px margin
    drawtext_filter = (
        f"drawtext=text='{watermark_text}':x=w-tw-16:y=h-th-16:"
        f"fontsize=h/32:fontcolor=white@{opacity}:shadowcolor=black@0.4:shadowx=1:shadowy=1"
    )

    cmd = [
        ff_bin, "-y",
        "-i", input_video_path,
        "-vf", drawtext_filter,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        output_video_path
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
            log.info("watermark_applied", path=output_video_path, text=watermark_text)
            return output_video_path
    except Exception as e:
        log.warning("watermark_drawtext_failed_using_copy", error=str(e))

    # Safe fallback if drawtext filter lacks font support on platform
    shutil.copyfile(input_video_path, output_video_path)
    return output_video_path
