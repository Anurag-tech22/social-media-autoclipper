import os
import sys
import time
import tempfile
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import setup_ffmpeg_path, get_temp_dir, format_timestamp
from src.downloader import download_youtube_video, extract_audio
from src.transcriber import transcribe_audio, extract_words_from_transcript, find_top_engaging_segments
from src.video_processor import process_vertical_short, get_video_info

# Configure page metadata
st.set_page_config(
    page_title="Auto-Clip & Burn AI | Viral Shorts Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics, dark glassmorphism, and removing default Streamlit badges
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    /* Completely hide Streamlit Deploy button, header bar, hamburger menu, and footer */
    #MainMenu {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    [data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main {
        background: radial-gradient(circle at 10% 20%, rgba(20, 24, 38, 1) 0%, rgba(10, 12, 18, 1) 90.2%);
    }
    
    .hero-container {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF6B6B 0%, #FFD93D 50%, #4D96FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1.15rem;
        color: #94A3B8;
        font-weight: 400;
        line-height: 1.6;
        max-width: 850px;
        margin-bottom: 1.2rem;
    }
    
    .badge-container {
        display: flex;
        gap: 0.8rem;
        flex-wrap: wrap;
    }
    
    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 0.35rem 0.85rem;
        border-radius: 50px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #E2E8F0;
    }
    
    .card-box {
        background: rgba(18, 22, 34, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    
    .clip-card {
        background: #131722;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .clip-card:hover {
        border-color: rgba(255, 217, 61, 0.5);
        transform: translateY(-2px);
    }
    
    .metric-pill {
        background: rgba(255, 217, 61, 0.15);
        color: #FFD93D;
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        border: 1px solid rgba(255, 217, 61, 0.3);
    }
    
    .hook-pill {
        background: linear-gradient(90deg, rgba(255, 107, 107, 0.2) 0%, rgba(255, 142, 83, 0.2) 100%);
        color: #FF8E53;
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        margin-bottom: 0.5rem;
        display: inline-block;
        border: 1px solid rgba(255, 107, 107, 0.3);
    }
    
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.05rem;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "generated_clips" not in st.session_state:
    st.session_state.generated_clips = []
if "source_video_path" not in st.session_state:
    st.session_state.source_video_path = None
if "video_meta" not in st.session_state:
    st.session_state.video_meta = {}

setup_ffmpeg_path()

# Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">⚡ Auto-Clip & Burn AI</div>
    <div class="hero-subtitle">
        Turn 20+ minute long-form videos & podcasts into high-retention 9:16 vertical Shorts & Reels with AI-driven engagement detection, viral hook banners, and animated burned-in captions in seconds.
    </div>
    <div class="badge-container">
        <span class="feature-badge">⏱️ 120min &rarr; 60s Repurposing</span>
        <span class="feature-badge">🎯 AI Speech Density Ranking</span>
        <span class="feature-badge">🔥 Word-by-Word Highlight Captions</span>
        <span class="feature-badge">📊 Animated Progress Bar</span>
        <span class="feature-badge">📱 9:16 Smart Cropping</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Customization
with st.sidebar:
    st.markdown("### 🎛️ **Shorts Studio Presets**")
    
    style_preset = st.selectbox(
        "Creator Viral Preset",
        options=["🔥 Hormozi Punch (Bold Yellow)", "⚡ MrBeast Viral (Electric Cyan)", "✨ Clean Minimalist (Crisp White)", "🟣 Neon Cyber (Magenta Pink)"],
        index=0
    )
    
    # Auto preset config
    if "Hormozi" in style_preset:
        preset_color = "Yellow"
        preset_font = 60
    elif "MrBeast" in style_preset:
        preset_color = "Cyan"
        preset_font = 58
    elif "Minimalist" in style_preset:
        preset_color = "White"
        preset_font = 52
    else:
        preset_color = "Pink"
        preset_font = 58

    st.markdown("#### ⏱️ Clip Duration")
    clip_length_choice = st.radio(
        "Target Length per Short",
        options=[15, 30, 60],
        index=1,
        format_func=lambda x: f"{x} Seconds {'(TikTok/Story)' if x==15 else '(Standard Short)' if x==30 else '(Deep Dive)'}"
    )
    
    st.markdown("#### 🎨 Custom Visual Enhancements")
    highlight_color = st.selectbox(
        "Word Highlight Color",
        options=["Yellow", "Cyan", "White", "Green", "Pink"],
        index=["Yellow", "Cyan", "White", "Green", "Pink"].index(preset_color)
    )
    
    font_size = st.slider(
        "Caption Font Size",
        min_value=42,
        max_value=76,
        value=preset_font,
        step=2
    )
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        enable_hooks = st.checkbox("Top Hook Banner", value=True, help="Renders high-CTR hook title at the top of the short.")
    with col_t2:
        enable_progress = st.checkbox("Bottom Progress Bar", value=True, help="Renders animated progress bar along the bottom.")
    
    st.markdown("#### 🧠 AI Engine")
    model_name = st.selectbox(
        "Whisper Speech Model",
        options=["base", "tiny"],
        index=0,
        help="'base' offers high transcription accuracy, 'tiny' delivers ultra fast processing."
    )
    
    max_clips = st.slider("Max Clips to Extract", min_value=1, max_value=4, value=3, step=1)
    
    st.markdown("---")
    st.caption("Auto-Clip & Burn AI v2.0 • Powered by Whisper AI & FFmpeg")

# Main Input Section
st.markdown("### 📥 1. Select Video Source")
tab_upload, tab_yt, tab_demo = st.tabs(["📁 Upload MP4 File", "🔗 YouTube Video URL", "🎬 Synthetic Test Demo"])

video_source_type = None
uploaded_file = None
youtube_url = None
use_demo = False

with tab_upload:
    uploaded_file = st.file_uploader("Drop horizontal 16:9 video (MP4, MOV, MKV)", type=["mp4", "mov", "mkv"])
    if uploaded_file is not None:
        video_source_type = "upload"

with tab_yt:
    youtube_url_input = st.text_input("Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    if youtube_url_input.strip():
        youtube_url = youtube_url_input.strip()
        video_source_type = "youtube"

with tab_demo:
    st.info("💡 Want to test instantly? Click below to generate a synthetic sample audio-video clip and run the full pipeline in seconds!")
    if st.button("🧪 Load Synthetic Demo Clip"):
        use_demo = True
        video_source_type = "demo"

# Action Button
st.markdown("---")
generate_btn = st.button("⚡ Generate Viral Vertical Shorts", type="primary", use_container_width=True)

if generate_btn:
    if not video_source_type:
        st.error("⚠️ Please provide a video source (upload an MP4 file, enter a YouTube URL, or click the Demo tab) before generating.")
    else:
        progress_box = st.container()
        with progress_box:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                temp_dir = get_temp_dir("session")
                source_video_path = None
                video_title = "Uploaded Video"
                
                # STEP 1: Ingestion
                status_text.markdown("🔄 **Step 1/4: Ingesting video & extracting 16kHz mono audio stream...**")
                progress_bar.progress(15)
                
                if video_source_type == "upload" and uploaded_file is not None:
                    source_video_path = str(temp_dir / f"upload_{uploaded_file.name}")
                    with open(source_video_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    video_title = uploaded_file.name
                    
                elif video_source_type == "youtube" and youtube_url:
                    status_text.markdown(f"📥 **Downloading YouTube video:** `{youtube_url}`...")
                    source_video_path, meta = download_youtube_video(youtube_url, str(temp_dir / "yt"))
                    video_title = meta.get("title", "YouTube Video")
                    st.session_state.video_meta = meta
                    
                elif video_source_type == "demo" or use_demo:
                    from test_pipeline import create_synthetic_test_video
                    source_video_path = str(temp_dir / "demo_podcast.mp4")
                    create_synthetic_test_video(source_video_path, duration=35.0)
                    video_title = "AI Content Mastery Demo"
                
                v_info = get_video_info(source_video_path)
                total_duration = v_info.get("duration", 30.0)
                
                # Extract WAV audio for Whisper
                audio_path = extract_audio(source_video_path)
                
                # STEP 2: Transcription
                status_text.markdown(f"🎙️ **Step 2/4: Transcribing speech with Whisper AI (`{model_name}`)...**")
                progress_bar.progress(40)
                start_t = time.time()
                transcription = transcribe_audio(audio_path, model_name=model_name)
                words = extract_words_from_transcript(transcription)
                
                # STEP 3: Engagement Detection & Hook Generation
                status_text.markdown("📊 **Step 3/4: Calculating speech density & generating viral hook headlines...**")
                progress_bar.progress(65)
                top_segments = find_top_engaging_segments(
                    transcription_result=transcription,
                    total_duration=total_duration,
                    target_length=float(clip_length_choice),
                    top_k=max_clips
                )
                
                if not top_segments:
                    st.warning("No clear speech detected. Using default opening interval.")
                    top_segments = [{
                        "rank": 1,
                        "start": 0.0,
                        "end": min(float(clip_length_choice), total_duration),
                        "duration": min(float(clip_length_choice), total_duration),
                        "word_count": len(words),
                        "words_per_sec": 2.5,
                        "score": 88.0,
                        "hook_title": "🔥 KEY HIGHLIGHT MOMENT",
                        "preview_text": "Full video segment"
                    }]

                # STEP 4: Video Processing (Cropping, Hooks & Caption Burning)
                status_text.markdown("✂️ **Step 4/4: Cropping to 9:16 vertical, burning captions & animated progress bars...**")
                out_clips_dir = get_temp_dir("rendered_shorts")
                rendered_clips = []
                
                step_progress = 65
                progress_increment = 30 / max(len(top_segments), 1)
                
                for seg in top_segments:
                    status_text.markdown(f"🔥 **Rendering Short #{seg['rank']}** ({format_timestamp(seg['start'])} &rarr; {format_timestamp(seg['end'])})...")
                    out_clip_file = str(out_clips_dir / f"short_rank_{seg['rank']}_{int(time.time())}.mp4")
                    
                    hook_to_burn = seg.get("hook_title") if enable_hooks else None
                    
                    process_vertical_short(
                        input_video_path=source_video_path,
                        start_time=seg["start"],
                        end_time=seg["end"],
                        words=words,
                        output_path=out_clip_file,
                        highlight_color=highlight_color,
                        font_size=font_size,
                        hook_title=hook_to_burn,
                        enable_progress_bar=enable_progress
                    )
                    
                    rendered_clips.append({
                        "rank": seg["rank"],
                        "file_path": out_clip_file,
                        "start": seg["start"],
                        "end": seg["end"],
                        "duration": seg["duration"],
                        "score": seg["score"],
                        "words_per_sec": seg["words_per_sec"],
                        "word_count": seg["word_count"],
                        "hook_title": seg.get("hook_title", "🔥 VIRAL MOMENT"),
                        "preview_text": seg["preview_text"]
                    })
                    
                    step_progress += progress_increment
                    progress_bar.progress(min(int(step_progress), 98))
                
                progress_bar.progress(100)
                status_text.success(f"🎉 Generated {len(rendered_clips)} viral Shorts in {time.time()-start_t:.1f}s!")
                st.session_state.generated_clips = rendered_clips
                st.session_state.source_video_path = source_video_path
                
            except Exception as e:
                st.error(f"❌ Error generating clips: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# STEP 5: Render Generated Clips Gallery
if st.session_state.generated_clips:
    st.markdown("---")
    st.markdown("## 🎬 Generated 9:16 Vertical Shorts")
    st.markdown("Preview your vertical shorts with burned-in animated captions, viral hook banners, and dynamic progress bars. Ready for TikTok, YouTube Shorts, and Reels!")
    
    cols = st.columns(len(st.session_state.generated_clips))
    
    for idx, clip in enumerate(st.session_state.generated_clips):
        col = cols[idx] if len(cols) > idx else cols[0]
        with col:
            st.markdown(f"""
            <div class="clip-card">
                <div class="hook-pill">{clip['hook_title']}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 800; font-size: 1.1rem; color: #FFF;">🔥 Short #{clip['rank']}</span>
                    <span class="metric-pill">Viral Score: {clip['score']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem;">
                    ⏱️ <b>{format_timestamp(clip['start'])} &rarr; {format_timestamp(clip['end'])}</b> ({clip['duration']:.1f}s)
                    <br>🗣️ <b>{clip['words_per_sec']} words/sec</b> ({clip['word_count']} words)
                </div>
                <div style="font-size: 0.82rem; color: #CBD5E1; font-style: italic; margin-bottom: 0.8rem; background: rgba(0,0,0,0.35); padding: 0.6rem; border-radius: 8px;">
                    "{clip['preview_text']}"
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # HTML5 Video Player
            if os.path.exists(clip["file_path"]):
                with open(clip["file_path"], "rb") as f:
                    video_bytes = f.read()
                st.video(video_bytes, format="video/mp4")
                
                # Single-click download button
                st.download_button(
                    label=f"⬇️ Download Short #{clip['rank']} (MP4)",
                    data=video_bytes,
                    file_name=f"viral_short_{clip['rank']}.mp4",
                    mime="video/mp4",
                    key=f"dl_btn_{clip['rank']}_{idx}",
                    use_container_width=True
                )
