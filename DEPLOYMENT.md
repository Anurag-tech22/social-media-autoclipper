# 🚀 Streamlit Community Cloud Deployment Guide

Deploy **Auto-Clip & Burn AI** for **100% FREE** with **zero credit card required** on [Streamlit Community Cloud](https://share.streamlit.io).

---

## 📋 Prerequisites
- A free [GitHub Account](https://github.com/)
- A free [Streamlit Community Cloud Account](https://share.streamlit.io/) (sign in with your GitHub account)

---

## 🛠️ Step 1: Initialize Git & Push to GitHub

1. Open your terminal in the project directory:
   ```bash
   git init
   git add .
   git commit -m "feat: Initial commit for Auto-Clip & Burn AI"
   ```

2. Create a new public or private repository on GitHub (e.g., `auto-clip-and-burn`).

3. Link your local repository to GitHub and push your code:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git
   git push -u origin main
   ```

---

## ☁️ Step 2: Deploy to Streamlit Community Cloud

1. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
2. Click the **"New app"** button in the top-right corner.
3. Configure the deployment settings:
   - **Repository:** Select `<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** (Optional) Customize your free subdomain: `https://<your-custom-name>.streamlit.app`

---

## ⚙️ Step 3: Configure System & Secret Settings

### System Dependencies (`packages.txt`)
Streamlit Community Cloud uses Debian Linux containers. The repository includes `packages.txt` containing:
```text
ffmpeg
```
Streamlit will automatically run `apt-get install -y ffmpeg` during build time so that video processing and Whisper audio extraction work out-of-the-box.

### Setting Secrets (Optional)
If you want to configure custom secrets or API keys:
1. In the Streamlit Cloud app dashboard, click **Advanced settings** (or go to **Settings > Secrets**).
2. Paste any key-value pairs in TOML format:
   ```toml
   # Example Secrets
   OPENAI_API_KEY = "sk-..."
   DEFAULT_WHISPER_MODEL = "tiny"
   ```
3. Click **Save**.

---

## 🎬 Step 4: Launch & Verify

1. Click **"Deploy!"**
2. Watch the live build logs in the bottom-right console.
3. Once built, your app will be live at `https://<your-app-name>.streamlit.app`!
4. Test by pasting any YouTube video URL or uploading an MP4 clip to generate your first 9:16 vertical Short.

---

## 💡 Cloud Performance Tips
- **Whisper Model**: For free-tier Cloud CPU containers, the **`tiny`** or **`base`** model is recommended for sub-60 second execution times.
- **Upload Limit**: The app supports files up to 200MB within Streamlit default limits.
