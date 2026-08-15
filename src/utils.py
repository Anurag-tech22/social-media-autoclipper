import os
import sys
import shutil
import tempfile
from pathlib import Path

_CACHED_FFMPEG = None
_CACHED_FFPROBE = None

def setup_ffmpeg_path():
    """Ensure ffmpeg & ffprobe executables are available in PATH and os.environ (cached)."""
    global _CACHED_FFMPEG
    if _CACHED_FFMPEG and os.path.exists(_CACHED_FFMPEG):
        return _CACHED_FFMPEG

    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass
        
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = str(Path(ffmpeg_exe).parent)
        
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
            
        target_ffmpeg = Path(ffmpeg_dir) / "ffmpeg.exe"
        if not target_ffmpeg.exists() and Path(ffmpeg_exe).name != "ffmpeg.exe":
            try:
                shutil.copyfile(ffmpeg_exe, target_ffmpeg)
            except Exception:
                pass
    except Exception:
        pass
        
    which_ffmpeg = shutil.which("ffmpeg")
    _CACHED_FFMPEG = which_ffmpeg or "ffmpeg"
    return _CACHED_FFMPEG

def get_ffprobe_path():
    """Get the ffprobe executable path (cached)."""
    global _CACHED_FFPROBE
    if _CACHED_FFPROBE and os.path.exists(_CACHED_FFPROBE):
        return _CACHED_FFPROBE
        
    setup_ffmpeg_path()
    which_ffprobe = shutil.which("ffprobe")
    _CACHED_FFPROBE = which_ffprobe or "ffprobe"
    return _CACHED_FFPROBE

def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS format."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def format_ass_timestamp(seconds: float) -> str:
    """Format seconds into ASS subtitle format: H:MM:SS.cs"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def get_temp_dir(subfolder: str = "autoclipper_tmp") -> Path:
    """Get or create a dedicated temp directory."""
    temp_dir = Path(tempfile.gettempdir()) / subfolder
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

def clean_temp_dir(subfolder: str = "autoclipper_tmp"):
    """Clean the temporary directory."""
    temp_dir = Path(tempfile.gettempdir()) / subfolder
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Could not clean temp dir {temp_dir}: {e}")
