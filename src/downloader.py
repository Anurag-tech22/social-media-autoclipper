import os
import subprocess
from pathlib import Path
import yt_dlp
from src.utils import get_temp_dir, setup_ffmpeg_path

def download_youtube_video(url: str, output_dir: str = None) -> tuple[str, dict]:
    """
    Download a YouTube video given its URL using yt-dlp with TLS browser impersonation
    and multi-tiered player client fallbacks to bypass datacenter 403 blocks.
    Returns:
        tuple[str, dict]: (local_video_path, metadata_dict)
    """
    setup_ffmpeg_path()
    
    if output_dir is None:
        output_dir = str(get_temp_dir("downloads"))
    os.makedirs(output_dir, exist_ok=True)
    
    out_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    strategies = [
        # Strategy 1: Genuine Chrome Browser Impersonation with Web Player Client
        {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best[ext=mp4]/best',
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'impersonate': 'chrome',
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'mweb'],
                }
            }
        },
        # Strategy 2: Android VR & Web Client (High compatibility without po-token)
        {
            'format': 'best[height<=720]/best/18',
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'web'],
                }
            }
        },
        # Strategy 3: Mobile Web & Android Creator fallback
        {
            'format': 'best[ext=mp4]/best',
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android_creator'],
                }
            }
        },
        # Strategy 4: Direct best fallback
        {
            'format': 'best/18/worst',
            'outtmpl': out_template,
            'noplaylist': True,
            'no_warnings': True
        }
    ]
    
    info = None
    last_err = None
    
    for strat in strategies:
        try:
            with yt_dlp.YoutubeDL(strat) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    break
        except Exception as e:
            last_err = e
            continue
            
    if not info:
        raise RuntimeError(f"YouTube download failed: {last_err}")
            
    video_id = info.get('id', 'video')
    ext = info.get('ext', 'mp4')
    video_path = os.path.join(output_dir, f"{video_id}.{ext}")
    if not os.path.exists(video_path):
        video_path = os.path.join(output_dir, f"{video_id}.mp4")
        
    metadata = {
        'title': info.get('title', 'YouTube Video'),
        'duration': info.get('duration', 0),
        'uploader': info.get('uploader', 'Unknown Creator'),
        'thumbnail': info.get('thumbnail', ''),
        'id': video_id
    }
        
    return video_path, metadata

def extract_audio(video_path: str, output_audio_path: str = None, max_duration: float = 600.0) -> str:
    """
    Extract clean 16kHz mono WAV audio from a video file for Whisper processing.
    Caps max scan duration (default 10 mins) to ensure blazing fast sub-minute processing.
    """
    ffmpeg_exe = setup_ffmpeg_path()
    
    if output_audio_path is None:
        video_stem = Path(video_path).stem
        temp_dir = get_temp_dir("audio")
        output_audio_path = str(temp_dir / f"{video_stem}_audio.wav")
        
    os.makedirs(Path(output_audio_path).parent, exist_ok=True)
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
    ]
    
    if max_duration and max_duration > 0:
        cmd.extend(["-t", str(max_duration)])
        
    cmd.append(output_audio_path)
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr.decode('utf-8', errors='ignore')}")
        
    return output_audio_path
