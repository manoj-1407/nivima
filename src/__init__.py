"""Nivima package initialization with automatic FFmpeg discovery."""
import os
import shutil
import sys


def _ensure_ffmpeg_on_path() -> None:
    if shutil.which("ffmpeg"):
        return

    # Check imageio_ffmpeg if installed
    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        target = os.path.join(ffmpeg_dir, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
        if not os.path.exists(target) and os.path.exists(ffmpeg_exe):
            shutil.copyfile(ffmpeg_exe, target)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass

    # Check user scripts dir on Windows
    if sys.platform == "win32":
        py_scripts = os.path.join(os.path.dirname(sys.executable), "Scripts")
        appdata_scripts = os.path.expandvars(r"%APPDATA%\Python\Python313\Scripts")
        for p in (py_scripts, appdata_scripts):
            if os.path.exists(os.path.join(p, "ffmpeg.exe")) and p not in os.environ.get("PATH", ""):
                os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
                break


_ensure_ffmpeg_on_path()
