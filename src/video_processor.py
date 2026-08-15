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
    font_size: int = 54,
    hook_title: Optional[str] = None
):
    """
    Generate Advanced SubStation Alpha (ASS) subtitles with:
    1. Word-level animated luminous glowing highlight captions.
    2. Vibrant top viral hook badge banner with neon accent.
    """
    # Color mapping for ASS (Format: &HAABBGGRR in hex)
    color_map = {
        "Yellow": {
            "text": "&H0000FFFF&",    # Bright Neon Yellow
            "glow": "&H0000E5FF&",    # Warm Golden Glow
        },
        "Cyan": {
            "text": "&H00FFFF00&",    # Electric Cyan
            "glow": "&H00E5E500&",    # Deep Cyan Glow
        },
        "White": {
            "text": "&H00FFFFFF&",    # Pure Crisp White
            "glow": "&H00CCCCCC&",    # Silver Glow
        },
        "Green": {
            "text": "&H0033FF33&",    # Neon Lime Green
            "glow": "&H0000CC33&",    # Emerald Glow
        },
        "Pink": {
            "text": "&H00FF33FF&",    # Neon Magenta
            "glow": "&H00CC00CC&",    # Violet Glow
        }
    }
    
    cfg = color_map.get(highlight_color, color_map["Yellow"])
    active_color = cfg["text"]
    glow_color = cfg["glow"]
    primary_color = "&H00FFFFFF&"
    dark_outline = "&H000A0C14&"
    
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: AutoClip,Arial Black,Arial,{font_size},{primary_color},&H00000000,{dark_outline},&H00000000,-1,0,0,0,100,100,0,0,1,2.8,0,2,50,50,260,1
Style: HookBanner,Arial Black,Arial,42,&H00FFFFFF,&H00000000,{dark_outline},&H00000000,-1,0,0,0,100,100,1,0,1,3.2,0,8,40,40,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    events = []
    
    # 1. Add Glowing Viral Hook Top Banner if provided
    if hook_title:
        clip_dur = clip_end - clip_start
        banner_end = format_ass_timestamp(clip_dur)
        clean_hook = hook_title.upper()
        events.append(f"Dialogue: 1,0:00:00.00,{banner_end},HookBanner,,0,0,0,,{{\\an8\\bord3.2\\3c{glow_color}\\c{primary_color}\\blur1.5\\fscx102\\fscy102}}{clean_hook}")

    # 2. Filter words relevant to this clip interval
    clip_words = [
        w for w in words
        if w["end"] > clip_start and w["start"] < clip_end
    ]
    
    if clip_words:
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
                        # Active word: Luminous Neon Glow effect with slight scale up
                        line_parts.append(f"{{\\c{active_color}\\b1\\bord3.5\\3c{glow_color}\\blur2\\fscx112\\fscy112}}{clean_word}{{\\rAutoClip}}")
                    else:
                        # Base word: Crisp clean white with subtle dark border
                        line_parts.append(f"{{\\c{primary_color}\\bord2.5\\3c{dark_outline}\\blur0.8}}{clean_word}")
                        
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
    font_size: int = 54,
    hook_title: Optional[str] = None,
    enable_progress_bar: bool = True,
    video_layout_mode: str = "Fit (Full View + Blurred Background)",
    target_width: int = 1080,
    target_height: int = 1920
) -> str:
    """
    Cuts video segment, transforms into 9:16 vertical short (Fit with blurred bg or Center Crop),
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
    
    # Check layout mode: Fit with Blurred BG (Default - 100% full content visible) vs Center Crop
    is_fit_mode = "Fit" in video_layout_mode or "Full" in video_layout_mode
    
    bar_color = "0xFFD700" if highlight_color == "Yellow" else "0x00E5FF" if highlight_color == "Cyan" else "0xFF3366"
    progress_cmd = f",drawbox=y=ih-18:x=0:w='(t/{clip_duration})*1080':h=12:color={bar_color}@0.95:t=fill" if enable_progress_bar else ""

    if is_fit_mode:
        # Fit mode: 10x accelerated downscaled boxblur + full uncropped foreground
        filter_complex = (
            f"[0:v]split[bg][fg];"
            f"[bg]scale=180:320:force_original_aspect_ratio=increase,crop=180:320,boxblur=4:1,scale={target_width}:{target_height}[bgblur];"
            f"[fg]scale={target_width}:-2:flags=lanczos[fgsharp];"
            f"[bgblur][fgsharp]overlay=0:(H-h)/2[base];"
            f"[base]subtitles='{escaped_ass_path}'{progress_cmd}[out]"
        )
        cmd = [
            ffmpeg_exe,
            "-y",
            "-ss", str(start_time),
            "-t", str(clip_duration),
            "-i", input_video_path,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-threads", "0",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
    else:
        # Crop mode: Center 9:16 slice
        vf_filter = (
            f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
            f"scale={target_width}:{target_height}:flags=lanczos,"
            f"subtitles='{escaped_ass_path}'{progress_cmd}"
        )
        cmd = [
            ffmpeg_exe,
            "-y",
            "-ss", str(start_time),
            "-t", str(clip_duration),
            "-i", input_video_path,
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-threads", "0",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]

    print(f"Rendering Vertical Short ({video_layout_mode}): {output_path}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if res.returncode != 0:
        print(f"Warning: Primary render failed, attempting fallback. Stderr: {res.stderr[:300]}")
        # Robust fallback filter
        fallback_filter = f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale={target_width}:{target_height}"
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
