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
    page_title="Auto-Clip & Burn AI | Viral Shorts Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Ultra-Clean CSS for Enterprise Glassmorphism UI & Smooth Transitions
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');
    
    /* Clean root resets */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #0A0C14 !important;
        color: #F8FAFC !important;
    }
    
    /* Hide Streamlit default Deploy button & menu, keep sidebar toggle accessible */
    #MainMenu {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    .stDeployButton {display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        visibility: visible !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        padding: 6px !important;
        color: #FFFFFF !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="stSidebarCollapseButton"]:hover {
        background: rgba(255, 107, 107, 0.2) !important;
        border-color: #FF6B6B !important;
        box-shadow: 0 0 16px rgba(255, 107, 107, 0.3) !important;
    }
    
    /* Hero Banner Styling */
    .hero-wrapper {
        background: linear-gradient(135deg, rgba(25, 30, 48, 0.6) 0%, rgba(15, 18, 30, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 24px;
        padding: 2.5rem 2.8rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(24px);
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    .hero-wrapper::before {
        content: '';
        position: absolute;
        top: -60px;
        right: -60px;
        width: 240px;
        height: 240px;
        background: radial-gradient(circle, rgba(255, 107, 107, 0.25) 0%, rgba(0, 0, 0, 0) 70%);
        border-radius: 50%;
        filter: blur(40px);
        pointer-events: none;
    }
    
    .hero-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2.9rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FFFFFF 0%, #E2E8F0 40%, #FFD93D 75%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.6rem;
        letter-spacing: -0.03em;
        line-height: 1.15;
    }
    
    .hero-subtitle {
        font-size: 1.12rem;
        color: #94A3B8;
        font-weight: 400;
        line-height: 1.65;
        max-width: 820px;
        margin-bottom: 1.4rem;
    }
    
    .badge-strip {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        align-items: center;
    }
    
    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 0.4rem 0.95rem;
        border-radius: 100px;
        font-size: 0.83rem;
        font-weight: 600;
        color: #E2E8F0;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .pill-badge:hover {
        border-color: rgba(255, 255, 255, 0.25);
        transform: translateY(-1px);
    }
    
    /* Section Headers */
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    
    /* Card Boxes */
    .glass-card {
        background: rgba(18, 22, 36, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 1.6rem;
        margin-bottom: 1.4rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }
    
    /* Output Shorts Cards */
    .short-container {
        background: #111422;
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 1.4rem;
        margin-bottom: 1.5rem;
        transition: all 0.25s ease;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }
    .short-container:hover {
        border-color: rgba(255, 217, 61, 0.45);
        transform: translateY(-3px);
        box-shadow: 0 14px 32px rgba(255, 217, 61, 0.1);
    }
    
    .hook-tag {
        display: inline-block;
        background: linear-gradient(90deg, rgba(255, 107, 107, 0.2) 0%, rgba(255, 142, 83, 0.2) 100%);
        border: 1px solid rgba(255, 107, 107, 0.35);
        color: #FFA07A;
        font-size: 0.8rem;
        font-weight: 800;
        padding: 0.3rem 0.75rem;
        border-radius: 8px;
        letter-spacing: 0.03em;
        margin-bottom: 0.75rem;
    }
    
    .score-badge {
        background: rgba(255, 217, 61, 0.12);
        border: 1px solid rgba(255, 217, 61, 0.35);
        color: #FFD93D;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 0.3rem 0.75rem;
        border-radius: 8px;
    }
    
    .transcript-quote {
        background: rgba(0, 0, 0, 0.35);
        border-left: 3px solid #4D96FF;
        border-radius: 0 8px 8px 0;
        padding: 0.65rem 0.85rem;
        font-size: 0.84rem;
        color: #CBD5E1;
        font-style: italic;
        line-height: 1.5;
        margin: 0.8rem 0;
    }
    
    /* Button enhancements */
    .stButton > button {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        padding: 0.75rem 1.8rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.55) !important;
    }
    
    /* Live Preview Box in Sidebar */
    .preview-box {
        background: #000000;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 1.2rem 0.8rem;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "generated_clips" not in st.session_state:
    st.session_state.generated_clips = []
if "source_video_path" not in st.session_state:
    st.session_state.source_video_path = None
if "demo_active" not in st.session_state:
    st.session_state.demo_active = False

setup_ffmpeg_path()

# Hero Header Component
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-title">⚡ Auto-Clip & Burn AI</div>
    <div class="hero-subtitle">
        Transform 20+ minute long-form YouTube videos and podcasts into high-retention 9:16 vertical Shorts & Reels with AI-driven engagement detection, viral hook banners, and animated burned-in captions.
    </div>
    <div class="badge-strip">
        <span class="pill-badge">⏱️ 120min &rarr; 60s Repurposing</span>
        <span class="pill-badge">🎯 Whisper AI Speech Density</span>
        <span class="pill-badge">🔥 Animated Word Highlights</span>
        <span class="pill-badge">📊 Dynamic Retention Bar</span>
        <span class="pill-badge">📱 1080x1920 HD Crop</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Creator Studio Sidebar
with st.sidebar:
    st.markdown("### 🎛️ **Creator Style Presets**")
    
    style_preset = st.selectbox(
        "Select Viral Preset",
        options=[
            "🔥 Alex Hormozi (Bold Yellow + Hook)",
            "⚡ MrBeast Viral (Electric Cyan + Fast Pacing)",
            "✨ Clean Minimalist (Crisp White + Subtle Outline)",
            "🟣 Neon Cyber (Vibrant Pink + Glowing Bar)"
        ],
        index=0
    )
    
    if "Hormozi" in style_preset:
        preset_color = "Yellow"
        preset_font = 60
        sample_hex = "#FFE600"
    elif "MrBeast" in style_preset:
        preset_color = "Cyan"
        preset_font = 58
        sample_hex = "#00FFFF"
    elif "Minimalist" in style_preset:
        preset_color = "White"
        preset_font = 52
        sample_hex = "#FFFFFF"
    else:
        preset_color = "Pink"
        preset_font = 58
        sample_hex = "#FF33FF"

    # Live Visual Subtitle Preview in Sidebar
    st.markdown(f"""
    <div class="preview-box">
        <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.05em;">Live Caption Preview</div>
        <div style="font-family: 'Arial Black', sans-serif; font-size: 1.15rem; color: #FFFFFF; text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000; line-height: 1.3;">
            TURN ANY VIDEO <br><span style="color: {sample_hex}; font-size: 1.25rem;">INTO VIRAL</span> SHORTS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### ⏱️ Clip Duration")
    clip_length_choice = st.radio(
        "Target Length per Short",
        options=[15, 30, 60],
        index=1,
        format_func=lambda x: f"{x} Seconds {'(TikTok/Story)' if x==15 else '(Standard Short)' if x==30 else '(Deep Dive)'}"
    )
    
    st.markdown("#### 🎨 Caption Customization")
    highlight_color = st.selectbox(
        "Active Word Highlight Accent",
        options=["Yellow", "Cyan", "White", "Green", "Pink"],
        index=["Yellow", "Cyan", "White", "Green", "Pink"].index(preset_color)
    )
    
    font_size = st.slider(
        "Font Size (pt)",
        min_value=42,
        max_value=76,
        value=preset_font,
        step=2
    )
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        enable_hooks = st.checkbox("Top Hook Banner", value=True, help="Renders high-CTR contextual hook title at the top of the short.")
    with col_v2:
        enable_progress = st.checkbox("Retention Bar", value=True, help="Renders dynamic animated progress bar along the bottom.")
    
    st.markdown("#### 🧠 AI Whisper Model")
    model_name = st.selectbox(
        "Speech Recognition Engine",
        options=["base", "tiny"],
        index=0,
        help="'base' offers optimal transcription accuracy, 'tiny' delivers ultra fast processing."
    )
    
    max_clips = st.slider("Top Viral Clips to Extract", min_value=1, max_value=4, value=3, step=1)
    
    st.markdown("---")
    st.caption("⚡ Auto-Clip & Burn AI v2.2 • Powered by Whisper AI & FFmpeg")

# Main Content Area
st.markdown('<div class="section-title">📥 1. Select Input Source</div>', unsafe_allow_html=True)

tab_upload, tab_yt, tab_demo = st.tabs(["📁 Upload MP4 / MOV Video", "🔗 YouTube Video URL", "🎬 1-Click Demo Podcast"])

video_source_type = None
uploaded_file = None
youtube_url = None

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload horizontal 16:9 recording",
        type=["mp4", "mov", "mkv"],
        help="Upload standard horizontal widescreen video (up to 200MB)"
    )
    if uploaded_file is not None:
        video_source_type = "upload"
        st.session_state.demo_active = False

with tab_yt:
    youtube_url_input = st.text_input(
        "Enter YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste any public YouTube video or podcast URL"
    )
    if youtube_url_input.strip():
        youtube_url = youtube_url_input.strip()
        video_source_type = "youtube"
        st.session_state.demo_active = False

with tab_demo:
    st.info("💡 Want to test instantly without uploading? Click below to load a synthetic sample AI podcast recording and run the complete pipeline in seconds!")
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1:
        if st.button("🧪 Select Demo Podcast", use_container_width=True):
            st.session_state.demo_active = True
            st.toast("✅ Demo Podcast Loaded!", icon="🎬")
    with col_d2:
        if st.session_state.demo_active:
            st.success("🎬 Active Source: **Synthetic AI Content Mastery Podcast (35s)**")

# Action Trigger
st.markdown("---")
generate_btn = st.button("⚡ Generate Viral Vertical Shorts", type="primary", use_container_width=True)

if generate_btn:
    # Resolve Active Source
    if uploaded_file is not None:
        video_source_type = "upload"
    elif youtube_url_input.strip():
        video_source_type = "youtube"
        youtube_url = youtube_url_input.strip()
    elif st.session_state.demo_active:
        video_source_type = "demo"
    else:
        video_source_type = None

    if not video_source_type:
        st.error("⚠️ Please provide a video source (upload an MP4 file, enter a YouTube URL, or click 'Select Demo Podcast' under the 1-Click Demo tab) before generating.")
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
                    
                elif video_source_type == "demo" or st.session_state.demo_active:
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
    st.markdown('<div class="section-title">🎬 2. Generated 9:16 Vertical Shorts</div>', unsafe_allow_html=True)
    st.caption("Preview your vertical shorts with burned-in animated captions, viral hook banners, and dynamic progress bars. Ready for TikTok, YouTube Shorts, and Reels!")
    
    cols = st.columns(len(st.session_state.generated_clips))
    
    for idx, clip in enumerate(st.session_state.generated_clips):
        col = cols[idx] if len(cols) > idx else cols[0]
        with col:
            st.markdown(f"""
            <div class="short-container">
                <div class="hook-tag">{clip['hook_title']}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.15rem; color: #FFFFFF;">Short #{clip['rank']}</span>
                    <span class="score-badge">Viral Score: {clip['score']}</span>
                </div>
                <div style="font-size: 0.84rem; color: #94A3B8; margin-bottom: 0.6rem;">
                    ⏱️ <b>{format_timestamp(clip['start'])} &rarr; {format_timestamp(clip['end'])}</b> ({clip['duration']:.1f}s)
                    &nbsp;|&nbsp; 🗣️ <b>{clip['words_per_sec']} wps</b> ({clip['word_count']} words)
                </div>
                <div class="transcript-quote">
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
