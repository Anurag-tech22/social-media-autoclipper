# 🎤 3-Minute Hackathon Winning Pitch & Demo Script
**Project**: Auto-Clip & Burn AI  
**Target Duration**: 3:00 Minutes  
**Format**: Screen Recording + Voiceover / Webcam  

---

## ⏱️ [0:00 - 0:35] Part 1: The Problem & The Inspiration

**[WHAT TO SHOW ON SCREEN]**:
Open a long 40-minute horizontal podcast or YouTube video in one browser tab, and then switch to the **Auto-Clip & Burn AI** studio at `http://localhost:8501`.

**[WHAT TO SAY]**:
> *"Hello judges and fellow creators! If you've ever tried building an audience on YouTube Shorts, TikTok, or Instagram Reels, you know that short-form video is the single most powerful growth engine in 2026.*
>
> *But here is the painful truth: **repurposing long-form content is broken.** For every 30-minute podcast or tutorial, editors spend **over 2 hours** scrubbing through timelines, manually calculating 9:16 aspect ratios, typing subtitles word-by-word, and keyframing color animations.*
>
> *Commercial tools charge upwards of $50 to $80 every single month for basic clipping.*
>
> *That’s why we built **Auto-Clip & Burn AI**—a 100% free, open-source, full-stack AI media engine that turns 20-minute videos into viral vertical Shorts with animated captions in under 60 seconds."*

---

## ⏱️ [0:35 - 1:15] Part 2: What We Built & Architecture

**[WHAT TO SHOW ON SCREEN]**:
Point your mouse at the creator sidebar with the presets, and briefly flash the GitHub repository architecture diagram.

**[WHAT TO SAY]**:
> *"Under the hood, Auto-Clip & Burn is NOT just a simple ChatGPT wrapper. It is a full multi-modal media pipeline:*
>
> 1. **Ingestion Layer**: Using `yt-dlp` and FFmpeg, it extracts high-fidelity 16kHz mono audio from any YouTube URL or MP4 upload.
> 2. **AI Speech Intelligence**: We run **OpenAI Whisper AI** locally with word-level microsecond alignment and greedy fast-path decoding.
> 3. **Engagement Algorithm**: Instead of random cuts, our custom speech-density heuristic scans the pacing, words-per-second, and sentence boundaries to mathematically identify the top 3 highest-energy moments.
> 4. **Transformation & Rendering**: Our video engine renders 1080x1920 HD vertical frames, generates Advanced SubStation Alpha (`.ass`) karaoke keyframes, burns luminous neon captions into the lower 35% safe zone, and adds a dynamic retention progress bar."*

---

## ⏱️ [1:15 - 2:20] Part 3: Live Interactive Demo (Capturing Maximum Bonus Points!)

**[WHAT TO SHOW ON SCREEN]**:
1. In the sidebar, select **`🔥 Alex Hormozi (Bold Yellow + Hook)`** and point out how the **Live Caption Preview** updates in real time.
2. Under **Aspect Ratio Mode**, show that **`Fit (Full 100% View + Dynamic Blurred Canvas)`** is selected.
3. Click the **`🎬 1-Click Demo Podcast`** tab and click **`🧪 Select Demo Podcast`** (or paste a YouTube URL).
4. Click the big glowing button: **`⚡ Generate Viral Vertical Shorts`**.
5. Watch the live 4-stage progress indicators (`Ingesting → Transcribing → Engagement → Cropping & Caption Burning`).
6. Scroll down to the **Generated 9:16 Vertical Shorts** gallery and hit **Play** on Short #1.
7. Click **`⬇️ Download Short #1 (MP4)`** to show the real video file downloading.

**[WHAT TO SAY]**:
> *"Let’s see it run live!*
>
> *First, in the sidebar, I can choose our viral creator presets—like the **Alex Hormozi** bold yellow theme or **MrBeast** electric cyan. Notice how our live caption preview updates instantly.*
>
> *Next, we have our breakthrough **Fit Canvas Mode**. Unlike naive tools that zoom in and cut off 50% of your screen, our engine keeps 100% of your widescreen video visible in the center, framed with a dynamic, matching blurred background.*
>
> *Now, I click **'Generate Viral Vertical Shorts'**.*
>
> *In real-time, the app executes all 4 stages: audio extraction, Whisper transcription, viral hook generation, and GPU/CPU compositing.*
>
> *And in just 25 seconds—look at the result!*
>
> *We have three complete, publication-ready vertical Shorts. Look at how the active words light up with a luminous neon glow as the speaker speaks. Look at the high-CTR viral hook banner at the top (`'THE MOST POWERFUL MOMENT'`), and the smooth retention progress bar filling up at the bottom.*
>
> *With one single click on 'Download MP4', the high-definition vertical video is saved directly to my computer, ready for TikTok and Reels!"*

---

## ⏱️ [2:20 - 3:00] Part 4: Real-World Usefulness, DevOps & Conclusion

**[WHAT TO SHOW ON SCREEN]**:
Show the GitHub repo with `packages.txt` and `requirements.txt` ready for Streamlit Community Cloud.

**[WHAT TO SAY]**:
> *"To summarize why Auto-Clip & Burn AI is a game-changer:*
>
> - **Real-World Impact**: It saves creators **10+ hours every week** by cutting video editing time from 2 hours to 60 seconds.
> - **Zero Infrastructure Cost**: It requires zero paid third-party cloud APIs and can be deployed for **100% free** on Streamlit Community Cloud using our bundled `packages.txt` and `requirements.txt`.
> - **Production Quality**: It delivers crisp 1080x1920 resolution, frame-accurate word sync, and zero cut-off framing.
>
> *Auto-Clip & Burn AI bridges the gap between long-form content and viral short-form growth.*
>
> *Thank you for watching, and we can’t wait to see what you create with it!"*
