# Video Transcriber

Turn any video into subtitles. Works offline, no internet needed after setup.

---

## Quick Start (for non-technical users)

You need two things:

### 1. Install ffmpeg (one time)

Open **Command Prompt** and paste:

```
winget install ffmpeg
```

Restart Command Prompt after installing.

### 2. Run the transcriber

Double-click **transcriber.exe**. A window opens:

1. Click **Browse** and pick your video file
2. Choose your language (use **Cantonese/Chinese (zh)** for Cantonese)
3. Click **Transcribe**
4. Wait for it to finish — subtitle files appear next to your video

That's it! You get a `.srt` file (subtitles) and a `.txt` file (plain text) in the same folder as your video.

> First run takes a bit longer because it downloads the speech model (~150MB). After that it works fully offline.

---

## For Cantonese Videos

- Set language to **Cantonese / Chinese (zh)**
- If the video is about a specific topic, pick a **Domain** for better accuracy:

| Domain | Good for |
|--------|----------|
| I-Ching / Metaphysics | 易經, 風水, 八字 lectures |
| Philosophy | 儒釋道, 新儒家 discussions |
| Geopolitics | 時事分析, international affairs |
| Finance | 財經, stocks, markets |
| Crypto | Bitcoin, blockchain |
| Technology / AI | Tech and AI topics |

---

## Troubleshooting

**"ffmpeg not found"** — Make sure you installed ffmpeg (step 1 above) and restarted Command Prompt.

**It's very slow** — Change the Model to **tiny** for faster (but less accurate) results. The default **base** model is a good balance.

**Wrong language** — Pick the correct language manually instead of leaving it on Auto-detect.

**Subtitles look garbled** — The tool retries automatically, but if it still looks wrong, try setting the language explicitly.

---

## Developer Setup

If you want to run from source instead of the .exe:

```bash
# Install Python 3.10+ and ffmpeg, then:
pip install -r requirements.txt

# GUI
python gui.py

# Command line
python transcribe.py video.mp4
python transcribe.py video.mp4 -l zh --domain iching
python transcribe.py "https://youtube.com/watch?v=..."
```

### Command Line Options

```
python transcribe.py INPUT [options]

  -o DIR              Output directory
  -m MODEL            tiny|base|small|medium|large-v3 (default: base)
  -l LANG             en, zh (Cantonese), ja, ko, fr, es, de...
  --domain DOMAIN     iching, geopolitics, finance, philosophy, etc.
  --format FORMAT     srt|txt|both (default: both)
  -v                  Verbose output
```

### Building the .exe

```bash
pip install pyinstaller
python build_exe.py
```

Produces `dist/transcriber.exe` (GUI) and `dist/transcribe.exe` (CLI).
