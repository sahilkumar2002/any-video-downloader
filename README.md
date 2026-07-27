# 🚀 Any Video Downloader (VidVelocity PRO)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?style=for-the-badge&logo=flask&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Universal_Engine-red?style=for-the-badge&logo=youtube&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-purple?style=for-the-badge)

**VidVelocity PRO** is a state-of-the-art, universal video and audio downloader application powered by **Python, Flask, yt-dlp, and ffmpeg**. It features an ultra-premium glassmorphic web UI that lets you paste links from thousands of platforms and save high-definition videos (or MP3 audio) directly to your system with **100% native Windows Media Player compatibility**.

---

## ✨ Key Features

- **🌐 Universal Website Support**: Easily download from **YouTube, TikTok (No Watermark), Instagram Reels & Stories, Twitter / X, Facebook, Vimeo, Bilibili, Reddit**, and over 1,000+ supported websites.
- **🖥️ 100% Windows Media Player Compatible**: Automatically remuxes video streams to standard **MP4 containers with H.264 (AVC) video and AAC audio** so your files play natively without errors on any Windows PC or media device.
- **🌟 Multi-Format & Resolution Selection**:
  - `Best Quality` — Highest available resolution & bitrate (MP4)
  - `1080p Full HD` — Crisp HD quality for large screens
  - `720p HD` — Fast, mobile-friendly standard HD
  - `480p SD` — Smallest file size for rapid downloading
  - `Audio Only (MP3)` — Extracts 192kbps high-fidelity MP3 audio
- **⚡ Smart Clipboard Paste**: Instant **"📋 Paste"** button that reads your clipboard and auto-fetches video metadata, thumbnails, duration, and channel info.
- **📊 Real-Time Download Telemetry**: Live progress bar showing exact download percentage, speed (`MB/s`), remaining time (`ETA`), and file size.
- **📂 One-Click Explorer Highlight**: When finished, click **"Show in Folder"** to automatically launch Windows File Explorer highlighting the exact downloaded file!
- **📜 Session Download Manager**: Built-in history tracker for all downloads initiated during your active session.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Threaded Asynchronous Workers
- **Extraction Engine**: `yt-dlp` (Universal Video Extractor)
- **Media Processing**: `imageio-ffmpeg` (Standalone ffmpeg binary integration)
- **Frontend**: HTML5, Vanilla JavaScript, Custom HSL Glassmorphic CSS

---

## 🚀 Quick Start Guide (Windows)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/sahilkumar2002/any-video-downloader.git
cd any-video-downloader
```

### 2️⃣ Install Dependencies
Ensure you have Python 3.8+ installed, then run:
```bash
pip install -r requirements.txt
```

### 3️⃣ Launch the Application
Simply double-click the included Windows Batch launcher:
> 📂 **`Start_Downloader.bat`**

Or start the server via terminal:
```bash
python app.py
```

Open your web browser and navigate to:
👉 **http://localhost:5000**

---

## 📁 Project Structure

```text
any-video-downloader/
│
├── app.py                   # Main Flask server & download API controller
├── requirements.txt         # Python package dependencies
├── Start_Downloader.bat     # Windows double-click auto-launcher
├── .gitignore               # Git ignore configuration
│
└── static/
    ├── index.html           # Responsive web UI layout
    ├── style.css            # Glassmorphic design system & animations
    └── script.js            # Client-side interactivity & progress polling
```

---

## 📝 License

This project is open-source and available under the MIT License. Built for seamless high-speed media downloading.
