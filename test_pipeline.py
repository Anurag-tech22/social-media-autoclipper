import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import setup_ffmpeg_path, get_temp_dir
from src.downloader import extract_audio
from src.transcriber import transcribe_audio, extract_words_from_transcript, find_top_engaging_segments
from src.video_processor import process_vertical_short, get_video_info

def generate_tts_audio_windows(text: str, output_wav_path: str):
    """
    Generate realistic human speech audio on Windows using System.Speech.Synthesis
    without requiring third-party cloud APIs.
    """
    clean_text = text.replace('"', '""').replace("'", "''")
    ps_cmd = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 0
    $synth.SetOutputToWaveFile('{output_wav_path}')
    $synth.Speak("{clean_text}")
    $synth.Dispose()
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(output_wav_path):
        # Fallback to generating a simple test audio using ffmpeg sine wave
        ffmpeg_exe = setup_ffmpeg_path()
        subprocess.run([
            ffmpeg_exe, "-y", "-f", "lavfi",
            "-i", "sine=frequency=440:duration=15",
            output_wav_path
        ], capture_output=True)

def create_synthetic_test_video(output_video_path: str, duration: float = 30.0) -> str:
    """
    Create a 16:9 test video (1920x1080) with dynamic motion and spoken audio.
    """
    ffmpeg_exe = setup_ffmpeg_path()
    temp_dir = get_temp_dir("test_data")
    wav_path = str(temp_dir / "speech_test.wav")
    
    # 1. Generate speech audio
    spoken_script = (
        "Welcome to the automated shorts creator. "
        "Artificial intelligence is transforming content creation for millions of creators worldwide. "
        "With one click, you can turn any long video into viral vertical clips with instant captions!"
    )
    generate_tts_audio_windows(spoken_script, wav_path)
    
    # 2. Render 16:9 test video with gradient background and animated counter + audio
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size=1920x1080:rate=30",
        "-i", wav_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_video_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_video_path

def test_full_pipeline():
    print("==================================================")
    print("🚀 Running Auto-Clip & Burn Backend Verification")
    print("==================================================")
    
    temp_dir = get_temp_dir("pipeline_test")
    test_video = str(temp_dir / "sample_horizontal.mp4")
    
    print("\n1. Generating synthetic 16:9 sample video...")
    create_synthetic_test_video(test_video, duration=20.0)
    assert os.path.exists(test_video), "Failed to create synthetic test video"
    
    info = get_video_info(test_video)
    print(f"   Video Info: {info['width']}x{info['height']} @ {info['fps']:.1f}fps, duration: {info['duration']:.1f}s")
    
    print("\n2. Extracting audio...")
    audio_wav = extract_audio(test_video)
    assert os.path.exists(audio_wav), "Failed to extract WAV audio"
    print(f"   Extracted audio to: {audio_wav}")
    
    print("\n3. Transcribing with Whisper ('tiny' for speed)...")
    transcription = transcribe_audio(audio_wav, model_name="tiny")
    words = extract_words_from_transcript(transcription)
    print(f"   Transcription complete: {len(words)} words detected.")
    
    print("\n4. Engagement detection & ranking...")
    segments = find_top_engaging_segments(
        transcription_result=transcription,
        total_duration=info["duration"],
        target_length=15.0,
        top_k=2
    )
    print(f"   Found {len(segments)} top engagement segments:")
    for s in segments:
        print(f"   - Rank #{s['rank']}: {s['start']:.1f}s -> {s['end']:.1f}s | Score: {s['score']} | {s['preview_text']}")
    
    print("\n5. Processing 9:16 vertical crop with burned-in animated captions, viral hook, and progress bar...")
    target_seg = segments[0]
    out_short = str(temp_dir / "verified_short.mp4")
    process_vertical_short(
        input_video_path=test_video,
        start_time=target_seg["start"],
        end_time=target_seg["end"],
        words=words,
        output_path=out_short,
        highlight_color="Yellow",
        font_size=58,
        hook_title=target_seg.get("hook_title", "🔥 VIRAL BREAKTHROUGH"),
        enable_progress_bar=True
    )
    
    assert os.path.exists(out_short), "Final short was not created"
    out_info = get_video_info(out_short)
    print(f"   Output Short: {out_info['width']}x{out_info['height']}, duration: {out_info['duration']:.1f}s, size: {os.path.getsize(out_short):,} bytes")
    
    assert out_info["width"] == 1080 and out_info["height"] == 1920, "Output is not 9:16 (1080x1920)"
    assert os.path.getsize(out_short) > 10000, "Output short file is suspiciously small"
    
    print("\n✅ Verification Successful: All pipeline stages executed flawlessly!")

if __name__ == "__main__":
    test_full_pipeline()
