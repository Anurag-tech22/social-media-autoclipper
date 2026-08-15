import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils import setup_ffmpeg_path, get_ffprobe_path, get_temp_dir, format_ass_timestamp

def get_video_info(video_path: str) -> Dict[str, Any]:
    """Get video dimensions, fps, and duration using ffprobe."""
    ffprobe_exe = get_ffprobe_path()

    cmd = [
        ffprobe_exe,
        "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration",
        "-of", "json",
        video_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return {"width": 1080, "height": 1920, "fps": 30.0, "duration": 30.0}
            
        data = json.loads(res.stdout)
        width = 1920
        height = 1080
        duration = 0.0
        fps = 30.0
        
        for stream in data.get("streams", []):
            if "width" in stream and "height" in stream:
                width = int(stream["width"])
                height = int(stream["height"])
                r_fps = stream.get("r_frame_rate", "30/1")
                if "/" in r_fps:
                    num, den = map(float, r_fps.split("/"))
                    fps = num / max(den, 1.0)
                else:
                    fps = float(r_fps)
                break
        
        if "format" in data and "duration" in data["format"]:
            duration = float(data["format"]["duration"])
            
        return {"width": width, "height": height, "fps": fps, "duration": duration}
    except Exception as e:
        return {"width": 1080, "height": 1920, "fps": 30.0, "duration": 30.0}

def create_ass_subtitles(
    words: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float,
    output_ass_path: str,
    highlight_color: str = "Yellow",
    font_size: int = 58,
    hook_title: Optional[str] = None
):
    """
    Generate Advanced SubStation Alpha (ASS) subtitles with:
    1. Word-level animated highlight captions in the lower 35% safe zone.
    2. Optional top viral hook title banner.
    """
    # Color mapping for ASS (Format: &HAABBGGRR in hex)
    color_map = {
        "Yellow": "&H0000E5FF&",   # Bright Golden Yellow (BGR: 00 E5 FF)
        "Cyan": "&H00FFFF00&",     # Vibrant Electric Cyan (BGR: FF FF 00)
        "White": "&H00FFFFFF&",    # Crisp Pure White
        "Green": "&H0000FF66&",    # Neon Lime Green
        "Pink": "&H00FF33FF&"      # Neon Magenta / Pink
    }
    
    primary_color = "&H00FFFFFF&"
    active_color = color_map.get(highlight_color, "&H0000E5FF&")
    outline_color = "&H00000000&" # Pure Black outline
    shadow_color = "&H90000000&"  # Drop shadow

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: AutoClip,Arial Black,Arial,{font_size},{primary_color},&H000000FF,{outline_color},{shadow_color},-1,0,0,0,100,100,0,0,1,5.5,3.0,2,60,60,360,1
Style: HookBanner,Arial Black,Arial,48,&H0000E5FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,4.5,2.5,8,40,40,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    events = []
    
    # 1. Add Viral Hook Top Banner if provided
    if hook_title:
        clip_dur = clip_end - clip_start
        banner_end = format_ass_timestamp(clip_dur)
        clean_hook = hook_title.upper()
        events.append(f"Dialogue: 1,0:00:00.00,{banner_end},HookBanner,,0,0,0,,{{\\an8\\bord4\\fscx102\\fscy102}}{clean_hook}")

    # 2. Filter words relevant to this clip interval
    clip_words = [
        w for w in words
        if w["end"] > clip_start and w["start"] < clip_end
    ]
    
    if clip_words:
        # Group words into short punchy phrases (3 to 5 words)
        grouped_phrases: List[List[Dict[str, Any]]] = []
        current_group: List[Dict[str, Any]] = []
        
        for w in clip_words:
            rel_w = {
                "word": w["word"].strip(),
                "start": max(0.0, w["start"] - clip_start),
                "end": max(0.0, w["end"] - clip_start),
            }
            current_group.append(rel_w)
            
            has_break = any(p in rel_w["word"] for p in [".", "?", "!", ",", ";"])
            if len(current_group) >= 4 or (len(current_group) >= 2 and has_break):
                grouped_phrases.append(current_group)
                current_group = []
                
        if current_group:
            grouped_phrases.append(current_group)

        for group in grouped_phrases:
            if not group:
                continue
            
            for current_idx, current_word in enumerate(group):
                w_start = current_word["start"]
                w_end = current_word["end"]
                if w_end <= w_start:
                    w_end = w_start + 0.3
                    
                line_parts = []
                for idx, w in enumerate(group):
                    clean_word = w["word"].upper()
                    if idx == current_idx:
                        line_parts.append(f"{{\\c{active_color}\\b1\\fscx110\\fscy110}}{clean_word}{{\\rAutoClip}}")
                    else:
                        line_parts.append(f"{{\\c{primary_color}}}{clean_word}")
                        
                caption_text = " ".join(line_parts)
                start_str = format_ass_timestamp(w_start)
                end_str = format_ass_timestamp(w_end)
                events.append(f"Dialogue: 0,{start_str},{end_str},AutoClip,,0,0,0,,{caption_text}")

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events) + "\n")

def process_vertical_short(
    input_video_path: str,
    start_time: float,
    end_time: float,
    words: List[Dict[str, Any]],
    output_path: str,
    highlight_color: str = "Yellow",
    font_size: int = 58,
    hook_title: Optional[str] = None,
    enable_progress_bar: bool = True,
    target_width: int = 1080,
    target_height: int = 1920
) -> str:
    """
    Cuts video segment, transforms 16:9 into 9:16 centered vertical short,
    burns in animated high-contrast captions, top viral hook title, and bottom progress bar.
    """
    ffmpeg_exe = setup_ffmpeg_path()
    temp_dir = get_temp_dir("process")
    os.makedirs(temp_dir, exist_ok=True)
    
    clip_duration = end_time - start_time
    ass_path = str(temp_dir / f"subs_{Path(output_path).stem}.ass")
    
    # Generate ASS subtitles with hook banner
    create_ass_subtitles(
        words=words,
        clip_start=start_time,
        clip_end=end_time,
        output_ass_path=ass_path,
        highlight_color=highlight_color,
        font_size=font_size,
        hook_title=hook_title
    )

    escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
    
    # 9:16 Centered Crop Filter + Lanczos scaling + Subtitles + Animated Progress Bar
    filters = [
        "crop=ih*9/16:ih:(iw-ih*9/16)/2:0",
        f"scale={target_width}:{target_height}:flags=lanczos",
        f"subtitles='{escaped_ass_path}'"
    ]
    
    # Animated progress bar at bottom of frame (height 14px, glowing gold/cyan)
    if enable_progress_bar:
        bar_color = "0xFFD700" if highlight_color == "Yellow" else "0x00E5FF" if highlight_color == "Cyan" else "0xFF3366"
        # Progress bar width grows proportionally with t: w = (t / duration) * 1080
        progress_filter = (
            f"drawbox=y=ih-18:x=0:w='(t/{clip_duration})*1080':h=12:color={bar_color}@0.9:t=fill"
        )
        filters.append(progress_filter)
        
    vf_filter = ",".join(filters)
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", str(start_time),
        "-t", str(clip_duration),
        "-i", input_video_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"Rendering Viral 9:16 Short: {output_path} ({start_time:.1f}s - {end_time:.1f}s)...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if res.returncode != 0:
        print(f"Warning: Primary render failed, falling back. Stderr: {res.stderr[:250]}")
        fallback_filter = (
            f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
            f"scale={target_width}:{target_height}:flags=lanczos"
        )
        cmd_fallback = [
            ffmpeg_exe,
            "-y",
            "-ss", str(start_time),
            "-t", str(clip_duration),
            "-i", input_video_path,
            "-vf", fallback_filter,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        res_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_fb.returncode != 0:
            raise RuntimeError(f"FFmpeg processing failed: {res_fb.stderr}")
            
    return output_path
