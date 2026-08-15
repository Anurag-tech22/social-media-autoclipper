import os
import math
import re
from typing import List, Dict, Any, Tuple
from src.utils import setup_ffmpeg_path

# Global model cache to avoid reloading models on every request
_MODEL_CACHE: Dict[str, Any] = {}

def load_whisper_model(model_name: str = "base"):
    """Load and cache Whisper model with lazy import for instant UI responsiveness."""
    global _MODEL_CACHE
    setup_ffmpeg_path()
    if model_name not in _MODEL_CACHE:
        print(f"Loading Whisper model '{model_name}' into memory...")
        import whisper
        _MODEL_CACHE[model_name] = whisper.load_model(model_name)
    return _MODEL_CACHE[model_name]

def transcribe_audio(audio_path: str, model_name: str = "base") -> Dict[str, Any]:
    """
    Transcribe audio with word-level timestamps using OpenAI Whisper.
    Returns:
        dict with segments and word timestamps.
    """
    model = load_whisper_model(model_name)
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        verbose=False,
        fp16=False # ensure CPU and broad hardware compatibility
    )
    return result

def extract_words_from_transcript(transcription_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract a flat list of words with start and end times."""
    words = []
    for segment in transcription_result.get("segments", []):
        if "words" in segment and segment["words"]:
            for w in segment["words"]:
                words.append({
                    "word": w.get("word", "").strip(),
                    "start": float(w.get("start", 0.0)),
                    "end": float(w.get("end", 0.0)),
                    "probability": float(w.get("probability", 1.0))
                })
        else:
            seg_text = segment.get("text", "").strip()
            seg_words = seg_text.split()
            seg_start = float(segment.get("start", 0.0))
            seg_end = float(segment.get("end", 0.0))
            duration = max(seg_end - seg_start, 0.1)
            word_dur = duration / max(len(seg_words), 1)
            for i, w in enumerate(seg_words):
                words.append({
                    "word": w,
                    "start": seg_start + i * word_dur,
                    "end": seg_start + (i + 1) * word_dur,
                    "probability": 1.0
                })
    return words

def generate_viral_hook(text: str, rank: int = 1) -> str:
    """Generate high-retention viral hook headline for the top banner."""
    clean_text = text.lower()
    
    # Contextual keywords matching
    if any(k in clean_text for k in ["money", "dollar", "wealth", "rich", "business", "scale", "sales"]):
        return "💰 THE SECRET TO WEALTH & GROWTH"
    elif any(k in clean_text for k in ["ai", "tech", "code", "future", "algorithm", "intelligence", "transform"]):
        return "⚡ THIS CHANGES EVERYTHING IN AI"
    elif any(k in clean_text for k in ["secret", "truth", "never", "nobody", "mistake", "fail", "stop"]):
        return "🤫 WHAT NOBODY EVER TELLS YOU"
    elif any(k in clean_text for k in ["mindset", "focus", "life", "success", "habit", "discipline"]):
        return "🧠 1% MINDSET REVELATION"
    elif rank == 1:
        return "🔥 THE MOST POWERFUL MOMENT"
    elif rank == 2:
        return "⚡ UNEXPECTED INSIGHT"
    else:
        return "💡 KEY TAKEAWAY FOR CREATORS"

def find_top_engaging_segments(
    transcription_result: Dict[str, Any],
    total_duration: float,
    target_length: float = 30.0,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Identify the top K high-speech/high-engagement segments based on speech density,
    continuous speech activity, and natural boundaries.
    """
    words = extract_words_from_transcript(transcription_result)
    segments = transcription_result.get("segments", [])
    
    # If total duration is shorter than target_length or no speech, return full video
    if total_duration <= target_length:
        preview = " ".join(w["word"] for w in words[:25]) + ("..." if len(words) > 25 else "")
        return [{
            "rank": 1,
            "start": 0.0,
            "end": total_duration,
            "duration": total_duration,
            "word_count": len(words),
            "words_per_sec": round(len(words) / max(total_duration, 1.0), 2),
            "score": 95.0,
            "hook_title": generate_viral_hook(preview, 1),
            "preview_text": preview
        }]

    # Sliding window candidates (step every 2.0 seconds)
    step = 2.0
    candidates = []
    max_start = max(0.0, total_duration - target_length)
    
    current_start = 0.0
    while current_start <= max_start:
        current_end = min(current_start + target_length, total_duration)
        window_duration = current_end - current_start
        
        # Words within this window
        window_words = [w for w in words if w["start"] >= current_start and w["end"] <= current_end]
        word_count = len(window_words)
        
        # Calculate active speech duration
        active_speech_time = sum(w["end"] - w["start"] for w in window_words)
        speech_ratio = active_speech_time / max(window_duration, 0.1)
        wps = word_count / max(window_duration, 0.1)
        
        # Bonus for starting/ending near segment or punctuation boundaries
        boundary_bonus = 0.0
        for seg in segments:
            if abs(seg.get("start", 0.0) - current_start) < 1.0:
                boundary_bonus += 2.0
            if abs(seg.get("end", 0.0) - current_end) < 1.0:
                boundary_bonus += 2.0
                
        # Engagement score: normalized 0-100
        density_score = min(wps / 3.2, 1.3) * 45.0
        continuity_score = min(speech_ratio, 1.0) * 45.0
        score = min(round(density_score + continuity_score + boundary_bonus, 1), 99.0)
        
        preview_text = " ".join(w["word"] for w in window_words[:22])
        if len(window_words) > 22:
            preview_text += "..."
            
        candidates.append({
            "start": current_start,
            "end": current_end,
            "duration": window_duration,
            "word_count": word_count,
            "words_per_sec": round(wps, 2),
            "score": score,
            "preview_text": preview_text or "Ambient / background audio"
        })
        
        current_start += step

    # Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Pick top_k non-overlapping segments (overlap threshold: max 35% of clip duration)
    selected = []
    min_separation = target_length * 0.65
    
    for cand in candidates:
        overlap = False
        for s in selected:
            if abs(cand["start"] - s["start"]) < min_separation:
                overlap = True
                break
        if not overlap:
            cand["rank"] = len(selected) + 1
            cand["hook_title"] = generate_viral_hook(cand["preview_text"], cand["rank"])
            selected.append(cand)
            if len(selected) >= top_k:
                break
                
    # If not enough distinct segments, relax separation
    if len(selected) < top_k:
        for cand in candidates:
            if cand not in selected:
                cand["rank"] = len(selected) + 1
                cand["hook_title"] = generate_viral_hook(cand["preview_text"], cand["rank"])
                selected.append(cand)
                if len(selected) >= top_k:
                    break

    # Sort final selected by timestamp order for logical presentation
    selected.sort(key=lambda x: x["start"])
    for idx, s in enumerate(selected):
        s["rank"] = idx + 1
        s["hook_title"] = generate_viral_hook(s["preview_text"], s["rank"])
        
    return selected
