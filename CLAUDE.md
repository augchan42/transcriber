# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Windows-targeted Python app that transcribes video/audio to `.srt`/`.txt` using
faster-whisper, plus a secondary YouTube compress+upload pipeline. Shipped two
ways: the source tree (`python gui.py`) and a portable zip containing a
PyInstaller-built `transcriber.exe` + bundled `ffmpeg.exe`/`ffprobe.exe`. The
portable zip is submitted to winget as `Augchan42.Transcriber`.

## Common commands

### Running from source

```bash
pip install -r requirements.txt          # faster-whisper, yt-dlp, requests
python gui.py                            # Tkinter GUI
python transcribe.py video.mp4           # CLI
python transcribe.py video.mp4 -l zh --domain iching
python transcribe.py "https://youtube.com/watch?v=..."
python transcribe.py video.mp4 --compress --compress-quality balanced
```

`ffmpeg` + `ffprobe` must be on PATH at runtime (the code shells out; there is
no Python-level fallback).

### Building the .exe / portable zip

**Do not run `build.bat` or `release.bat` through the Bash tool** — the system
Python at `C:\Python312` requires admin for `pip install` into
`Scripts\`/`share\`, and Bash-tool subshells hit `WinError 5` more reliably
than the user's own `cmd.exe`. Ask the user to run them in `cmd.exe` and paste
output. See `docs/RELEASING.md` for the full 5-step release flow (build →
bump winget YAMLs → `gh release create` → `winget validate` → submit
winget-pkgs PR).

```bat
:: cmd.exe, in repo root
build.bat                 :: -> dist\transcriber.exe
release.bat               :: -> TranscriberPortable.zip (build + bundle ffmpeg)
```

### Release PowerShell scripts

All scripts under `scripts\*.ps1` must stay **ASCII-only** (see ADR-002):
Windows PowerShell 5.1 reads BOM-less `.ps1` as CP1252, so any em-dash, smart
quote, ellipsis, arrow, or accented letter breaks the parser with misleading
errors tens of lines away from the real character. Also avoid here-strings
(`@"..."@`) and `2>&1` on native executables in these scripts — build
multi-line strings from `-join "\`r\`n"` arrays and branch on `$LASTEXITCODE`
instead.

There is no test suite and no linter configured.

## Architecture

### Two entry points, one engine

`transcribe.py` (CLI) and `gui.py` (Tkinter) both call into
`transcription.transcribe_with_timestamps()`. The GUI additionally wraps
compress/upload/auth flows and redirects `sys.stdout`/`sys.stderr` into a Text
widget via `PrintRedirector`, which is why the core modules use plain `print()`
for progress — it's the GUI's transport as well as the CLI's.

### Model loading is a module-global cache

`transcription._model_cache` is a dict keyed by `f"{model_size}_{device}_{compute_type}"`.
Subsequent calls with the same triple are instant. If you refactor model
loading, preserve this — the GUI relies on it to avoid re-loading Whisper
between clicks.

Device/compute-type auto-selection: `cuda` → `float16`, `cpu` → `int8` when
supported (falls back via `ctranslate2.get_supported_compute_types`). Users
can override with `--device` / `--compute-type`.

### Cantonese pipeline (cantonese.py)

Two mechanisms, both optional and controlled by `--domain`:

1. **initial_prompt** — a tightly packed, ~224-token prompt in
   `DOMAIN_PROMPTS` biases Whisper toward domain vocabulary *during*
   decoding. Each prompt starts with "純粵語轉錄，不要翻譯" to fight
   Whisper's tendency to translate to English. Don't blow past the 224-token
   budget — Whisper silently truncates.
2. **Post-correction regexes** — `DOMAIN_CORRECTIONS` applied after
   transcription when detected language is in `(yue, zh, zh-TW, zh-HK, cmn)`,
   plus `UNIVERSAL_CORRECTIONS` (Cantonese sentence particles romanized as
   `la` → `喇`, `ga` → `嘅`, etc.). Added regexes should be domain-specific
   so they don't fire on unrelated zh content.

### Garbled-transcription retry

`transcription.py` hardcodes a list of known-garbled output strings
(`"Fuck replacement"`, `"Mae aa"`, etc. — Whisper's failure modes on
particular audio). If detected-language ≠ en, no `--language` was forced,
and the transcript contains any indicator, it retries with `language="en"`.
If you see similar garbage in new failures, add the marker string here
rather than trying to detect it statistically.

### YouTube upload (yt_upload.py) — resumable by design

Uses `requests` directly, not the googleapis client, to keep the PyInstaller
bundle small. The resumable-session URL is persisted to a `{video}.resume`
sidecar so a failed upload can be re-tried by clicking "Upload to YouTube"
again — it re-queries the server's byte offset via `PUT Content-Range:
bytes */{size}` and continues from there. The `.resume` sidecar is gitignored.

Token format in `secrets/yt-tokens.json` (expiry stored as `expiry_date` in
ms since epoch) matches the hongkongaipodcast-site TypeScript version so
both projects can share a tokens file.

### BYO credentials (open-source release)

The repo and portable zip deliberately do **not** ship
`secrets/client_secret_*.json`. First click on "Sign in to YouTube" with no
credentials present opens a dialog with buttons for the setup guide
(`docs/youtube-setup.md`) and the `secrets/` folder. When editing the upload
UI, preserve this flow — it's the only way a first-time user discovers they
need their own Google Cloud project.

`yt_auth.get_secrets_dir()` returns `dirname(sys.executable)/secrets` when
frozen, else `dirname(__file__)/secrets`. Keep that branch in sync if you
add other resource-resolution helpers.

### Video compression (compress.py)

Settings are decided in ADR-001 (see `docs/adr/`). Default preset is
`balanced` (CRF 23); `max_compression` (CRF 28) was the original default and
is still valid for long-form talk content. Loudness is normalized to -16 LUFS
(YouTube/Apple) rather than Spotify's -14 so the same output is cross-platform.
Don't switch to H.265/AV1 without re-reading the ADR — the rationale is
encoder speed on CPU, not compression ratio.
