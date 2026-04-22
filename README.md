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

## YouTube Upload (optional)

The app can also upload your compressed video directly to YouTube with
automatic resume if the network drops.

### First-time setup — one-time, about 5 minutes

Because this is an open-source app, it ships **without** Google credentials
baked in. You create your own free Google Cloud project and plug it into
the app. This keeps your upload access under your control and avoids
any shared-credential risk.

Follow the short walkthrough: **[docs/youtube-setup.md](docs/youtube-setup.md)**

The first time you click **Sign in to YouTube** without credentials in
place, the app pops open a dialog with buttons to open the guide and the
`secrets/` folder — no hunting around required.

### Every upload after that

1. Pick the video file (usually the `_compressed.mp4` from the compress step)
2. Edit the title (auto-filled from filename)
3. Pick privacy: **unlisted** (default), **private**, or **public**
4. Click **Upload to YouTube**

If the upload fails mid-way (bad Wi-Fi, laptop sleep, etc.), just click
**Upload to YouTube** again — it resumes from where it stopped using a
`.resume` sidecar file.

> Uploads go to the YouTube channel tied to the Google account you signed
> in with, not some shared account.

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
