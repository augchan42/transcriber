# Video Transcriber

Transcribe MP4 videos and audio files into .srt subtitles and .txt transcripts. Works offline on CPU. Supports Cantonese and English with auto-detection.

## Prerequisites

- **Python 3.10+**
- **ffmpeg** — required for audio extraction from video

### Install ffmpeg

```bash
# Linux (Ubuntu/Debian)
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

## Setup

```bash
# Clone or copy this folder, then:
cd transcriber
pip install -r requirements.txt
```

The first time you run a transcription, the Whisper model will be downloaded automatically (~150MB for `base`).

## Usage

### Basic — transcribe a local video

```bash
python transcribe.py video.mp4
```

This produces `video.srt` and `video.txt` in the same directory.

### Cantonese content

For Cantonese, force the language to `zh` (NOT `yue` — this produces much better results):

```bash
python transcribe.py cantonese_video.mp4 -l zh
```

With domain-specific vocabulary hints (improves accuracy for specialized topics):

```bash
python transcribe.py iching_lecture.mp4 -l zh --domain iching
python transcribe.py news_clip.mp4 -l zh --domain geopolitics
python transcribe.py finance_talk.mp4 -l zh --domain finance
```

Available domains: `ai`, `crypto`, `finance`, `geopolitics`, `iching`, `iching_philosophy`, `metaphysics`, `philosophy`, `politics`, `technology`

### YouTube and other URLs

```bash
python transcribe.py "https://youtube.com/watch?v=VIDEO_ID"
python transcribe.py "https://twitter.com/user/status/123456" -o subtitles/
```

### Options

```
python transcribe.py INPUT [options]

Options:
  -o, --output DIR         Output directory
  -m, --model SIZE         tiny|base|small|medium|large-v3 (default: base)
  -l, --language LANG      en, zh (Cantonese), etc. Default: auto-detect
  --domain DOMAIN          Cantonese vocabulary hints (iching, finance, etc.)
  --format FORMAT          srt|txt|both (default: both)
  --max-duration SECS      Only transcribe first N seconds (for testing)
  --keep-audio             Keep downloaded audio files
  -v, --verbose            Show detailed logs
```

## Model Size Guide

| Model | Size | Speed on CPU | Accuracy | Recommended for |
|-------|------|-------------|----------|-----------------|
| tiny | ~75MB | ~1x real-time | Fair | Quick test runs |
| **base** | ~150MB | **~2x real-time** | **Good** | **Default — best speed/accuracy balance** |
| small | ~500MB | ~4x real-time | Better | When base isn't accurate enough |
| medium | ~1.5GB | ~8x real-time | Very good | When you need high accuracy and can wait |
| large-v3 | ~3GB | ~15x real-time | Best | Not recommended on CPU (very slow) |

Speed = how many times longer than the audio duration. E.g., "2x real-time" means a 10-minute video takes ~20 minutes to transcribe.

## Cantonese Tips

1. **Always use `-l zh`** — Whisper's `yue` (Cantonese) token causes decoder collapse. Forcing `zh` (Chinese) produces coherent Traditional Chinese output.

2. **Use `--domain`** for specialized content — this provides vocabulary hints that prevent common misrecognitions (e.g., 易經 being heard as 液晶).

3. **`base` model works well** — per testing, `base` + forced `zh` achieves good Cantonese quality without the compute overhead of larger models.

## GUI Mode

Double-click or run the GUI version — no command line needed:

```bash
python gui.py
```

A window opens where you can:
1. **Browse** for a video/audio file
2. **Pick** language (Auto-detect, Cantonese/zh, English, etc.)
3. **Pick** domain for Cantonese vocab hints (optional)
4. **Click Transcribe** and watch progress
5. Get .srt + .txt files in the same folder as your video

## Building a Standalone .exe (for non-technical users)

If your friend doesn't have Python installed, you can build .exe files they can run directly.

### On your machine (one-time build):

```bash
pip install pyinstaller
python build_exe.py
```

This produces:
- `dist/transcriber.exe` — **GUI version** (double-click to open, recommended for non-technical users)
- `dist/transcribe.exe` — CLI version

### What your friend needs:

1. **`transcriber.exe`** — copy it to their computer, double-click to open
2. **ffmpeg** — they need to install this once: open Command Prompt and run `winget install ffmpeg`

The first run downloads the Whisper model (~150MB for base) automatically. After that, it works fully offline.

## Troubleshooting

**"ffmpeg not found"** — Install ffmpeg (see Prerequisites above).

**YouTube download fails** — Update yt-dlp: `pip install -U yt-dlp`

**Transcription is very slow** — Use a smaller model: `-m tiny` or `-m base`

**Wrong language detected** — Force the language: `-l en` for English, `-l zh` for Cantonese

**Garbled output** — The tool auto-detects garbled transcriptions and retries with English. If you still get bad output, try forcing the language explicitly.
# transcriber
