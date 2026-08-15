import os
import subprocess
from pathlib import Path
import yt_dlp
from src.utils import get_temp_dir, setup_ffmpeg_path

def download_youtube_video(url: str, output_dir: str = None) -> tuple[str, dict]:
    """
    Download a YouTube video given its URL using yt-dlp with anti-403 client fallback.
    Returns:
        tuple[str, dict]: (local_video_path, metadata_dict)
    """
    setup_ffmpeg_path()
    
    if output_dir is None:
        output_dir = str(get_temp_dir("downloads"))
    os.makedirs(output_dir, exist_ok=True)
    
    out_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    # Primary anti-403 options using Android/iOS player clients
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best/18/22',
        'outtmpl': out_template,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 5,
        'fragment_retries': 5,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web_creator', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        # Fallback without specific player_skip if first attempt failed
        fallback_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android'],
                }
            }
        }
        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
    video_id = info.get('id', 'video')
    ext = info.get('ext', 'mp4')
    video_path = os.path.join(output_dir, f"{video_id}.{ext}")
    if not os.path.exists(video_path):
        video_path = os.path.join(output_dir, f"{video_id}.mp4")
        
    metadata = {
        'title': info.get('title', 'Unknown Title'),
        'duration': info.get('duration', 0),
        'uploader': info.get('uploader', 'Unknown Creator'),
        'thumbnail': info.get('thumbnail', ''),
        'id': video_id
    }
        
    return video_path, metadata

def extract_audio(video_path: str, output_audio_path: str = None) -> str:
    """
    Extract clean 16kHz mono WAV audio from a video file for Whisper processing.
    """
    ffmpeg_exe = setup_ffmpeg_path()
    
    if output_audio_path is None:
        video_stem = Path(video_path).stem
        temp_dir = get_temp_dir("audio")
        output_audio_path = str(temp_dir / f"{video_stem}_audio.wav")
        
    os.makedirs(Path(output_audio_path).parent, exist_ok=True)
    
    # Run ffmpeg to convert audio to 16kHz mono 16-bit PCM WAV
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_audio_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr.decode('utf-8', errors='ignore')}")
        
    return output_audio_path
