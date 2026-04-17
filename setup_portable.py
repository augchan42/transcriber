#!/usr/bin/env python3
"""
Create a portable folder that bundles everything needed to run the transcriber.

Usage (run on a Windows machine or WSL with access to Windows):
    python setup_portable.py

Creates: portable/VideoTranscriber/
    run.bat              <- Your friend double-clicks this
    run_cli.bat          <- CLI version
    install_ffmpeg.bat   <- One-time ffmpeg install helper
    gui.py
    transcribe.py
    transcription.py
    downloader.py
    srt_formatter.py
    cantonese.py
    requirements.txt
    README.txt

Your friend:
1. Unzips the folder
2. Double-clicks install_ffmpeg.bat (one time)
3. Double-clicks run.bat
"""

import os
import shutil


PORTABLE_DIR = os.path.join("portable", "VideoTranscriber")

# Python source files to include
SOURCE_FILES = [
    "gui.py",
    "transcribe.py",
    "transcription.py",
    "downloader.py",
    "srt_formatter.py",
    "cantonese.py",
    "compress.py",
    "yt_auth.py",
    "yt_upload.py",
    "requirements.txt",
]


def create_run_bat():
    """Create the main launcher batch file.

    Uses embedded portable Python from the python/ subfolder if present,
    otherwise falls back to system Python.
    """
    return "\r\n".join([
        "@echo off",
        "title Video Transcriber",
        "cd /d %~dp0",
        "echo ============================================",
        "echo   Video Transcriber",
        "echo ============================================",
        "echo.",
        "",
        "REM Use embedded Python if available, otherwise system Python",
        'if exist "python\\python.exe" (',
        '    set "PYTHON=%~dp0python\\python.exe"',
        '    set "PIP=%~dp0python\\python.exe -m pip"',
        "    goto :haspython",
        ")",
        "",
        "REM Fall back to system Python",
        "where python 1>nul 2>&1",
        "if %errorlevel% neq 0 goto :nopython",
        'set "PYTHON=python"',
        'set "PIP=pip"',
        "goto :haspython",
        "",
        ":nopython",
        "echo ERROR: Python not found!",
        "echo.",
        "echo Please ask your tech friend to set up the portable Python.",
        "echo.",
        "pause",
        "exit /b",
        "",
        ":haspython",
        "REM Check if dependencies are installed",
        '%PYTHON% -c "import faster_whisper" 1>nul 2>&1',
        "if %errorlevel% neq 0 goto :installdeps",
        "goto :hasdeps",
        "",
        ":installdeps",
        "echo Installing dependencies (first time only, may take a few minutes)...",
        "echo.",
        "%PIP% install --no-warn-script-location -r requirements.txt",
        "echo.",
        "echo Dependencies installed!",
        "echo.",
        "",
        ":hasdeps",
        "REM Check for ffmpeg",
        "where ffmpeg 1>nul 2>&1",
        "if %errorlevel% neq 0 goto :noffmpeg",
        "goto :hasffmpeg",
        "",
        ":noffmpeg",
        "echo WARNING: ffmpeg not found!",
        "echo.",
        'echo Please double-click "install_ffmpeg.bat" first, then try again.',
        "echo.",
        "pause",
        "exit /b",
        "",
        ":hasffmpeg",
        "echo Starting transcriber...",
        "%PYTHON% gui.py",
        "if %errorlevel% neq 0 (",
        "    echo.",
        "    echo Something went wrong. Press any key to close.",
        "    pause",
        ")",
        "",
    ]) + "\r\n"


def create_run_cli_bat():
    """Create CLI launcher."""
    return "\r\n".join([
        "@echo off",
        "title Video Transcriber (CLI)",
        "cd /d %~dp0",
        "",
        "where python 1>nul 2>&1",
        "if %errorlevel% neq 0 goto :nopython",
        "goto :haspython",
        "",
        ":nopython",
        "echo Python not found! Double-click run.bat first to install Python.",
        "pause",
        "exit /b",
        "",
        ":haspython",
        'python -c "import faster_whisper" 1>nul 2>&1',
        "if %errorlevel% neq 0 goto :installdeps",
        "goto :hasdeps",
        "",
        ":installdeps",
        "echo Installing dependencies...",
        "pip install -r requirements.txt",
        "",
        ":hasdeps",
        "echo.",
        "echo Usage: python transcribe.py video.mp4 [options]",
        "echo.",
        "echo   -l zh          Force Cantonese",
        "echo   -l en          Force English",
        "echo   --domain X     Vocabulary hints (iching, finance, geopolitics...)",
        "echo   -m tiny        Use faster (less accurate) model",
        "echo.",
        "echo Type your command below, or drag a video file onto this window.",
        'echo Type "exit" to quit.',
        "echo.",
        "",
        "cmd /k",
        "",
    ]) + "\r\n"


def create_install_ffmpeg_bat():
    """Create ffmpeg installer helper."""
    return "\r\n".join([
        "@echo off",
        "title Install ffmpeg",
        "echo ============================================",
        "echo   Installing ffmpeg...",
        "echo ============================================",
        "echo.",
        "",
        "where ffmpeg 1>nul 2>&1",
        "if %errorlevel% equ 0 goto :already",
        "goto :install",
        "",
        ":already",
        "echo ffmpeg is already installed!",
        "echo.",
        "pause",
        "exit /b",
        "",
        ":install",
        "echo Trying winget...",
        "winget install ffmpeg",
        "if %errorlevel% equ 0 goto :winget_ok",
        "goto :try_choco",
        "",
        ":winget_ok",
        "echo.",
        "echo ffmpeg installed successfully!",
        "echo Please CLOSE and REOPEN any command windows for it to take effect.",
        "echo.",
        "pause",
        "exit /b",
        "",
        ":try_choco",
        "echo.",
        "echo winget didn't work. Trying chocolatey...",
        "where choco 1>nul 2>&1",
        "if %errorlevel% neq 0 goto :manual",
        "choco install ffmpeg -y",
        "echo.",
        "echo ffmpeg installed successfully!",
        "pause",
        "exit /b",
        "",
        ":manual",
        "echo.",
        "echo ============================================",
        "echo   Could not install ffmpeg automatically.",
        "echo.",
        "echo   Please install it manually:",
        "echo   1. Go to https://www.gyan.dev/ffmpeg/builds/",
        'echo   2. Download "ffmpeg-release-essentials.zip"',
        "echo   3. Extract it",
        'echo   4. Add the "bin" folder to your system PATH',
        "echo.",
        "echo   Or ask your tech friend for help :)",
        "echo ============================================",
        "pause",
        "",
    ]) + "\r\n"


def create_readme_txt():
    """Create a simple readme for the portable folder."""
    return "\r\n".join([
        "VIDEO TRANSCRIBER",
        "=================",
        "",
        "Turn any video into subtitles. Works offline after first setup.",
        "",
        "FIRST TIME SETUP (do these once):",
        "----------------------------------",
        '1. Double-click "install_ffmpeg.bat"',
        "   - This installs ffmpeg (needed to read video files)",
        "   - Close and reopen any windows after it finishes",
        "",
        '2. Double-click "run.bat"',
        "   - First time it will install some things (takes a few minutes)",
        "   - Then the app opens automatically",
        "",
        "AFTER SETUP (every time):",
        "-------------------------",
        '1. Double-click "run.bat"',
        '2. Click "Browse" and pick your video',
        '3. For Cantonese: set Language to "Cantonese / Chinese (zh)"',
        '4. Click "Transcribe"',
        "5. Subtitle files (.srt and .txt) appear next to your video",
        "",
        "YOUTUBE UPLOAD (optional):",
        "--------------------------",
        '1. Pick a video, then click "Sign in to YouTube" (first time only)',
        "   A browser window opens — sign in with the shared podcast account",
        '2. Enter a title, pick Privacy (unlisted/private/public)',
        '3. Click "Upload to YouTube"',
        "   Upload auto-resumes if the network drops mid-upload",
        "",
        "TROUBLESHOOTING:",
        "----------------",
        '- "ffmpeg not found" -> Run install_ffmpeg.bat again',
        '- Very slow -> Change Model to "tiny"',
        "- Wrong language -> Pick the language manually",
        "- Still not working -> Send the error message to your tech friend",
        "",
    ]) + "\r\n"


def main():
    print("Creating portable VideoTranscriber folder...\n")

    # Clean and create directory
    if os.path.exists(PORTABLE_DIR):
        shutil.rmtree(PORTABLE_DIR)
    os.makedirs(PORTABLE_DIR)

    # Copy Python source files
    for filename in SOURCE_FILES:
        src = filename
        dst = os.path.join(PORTABLE_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Copied: {filename}")
        else:
            print(f"  WARNING: {filename} not found, skipping")

    # Copy OAuth client_secret (safe to bundle) but not yt-tokens.json (has refresh token)
    secrets_src = "secrets"
    secrets_dst = os.path.join(PORTABLE_DIR, "secrets")
    if os.path.isdir(secrets_src):
        os.makedirs(secrets_dst, exist_ok=True)
        for name in os.listdir(secrets_src):
            if name.startswith("client_secret_") and name.endswith(".json"):
                shutil.copy2(os.path.join(secrets_src, name), os.path.join(secrets_dst, name))
                print(f"  Copied: secrets/{name}")
        if not any(f.startswith("client_secret_") for f in os.listdir(secrets_dst)):
            print("  WARNING: no client_secret_*.json found in secrets/ — YouTube upload won't work")

    # Create batch files
    batch_files = {
        "run.bat": create_run_bat(),
        "run_cli.bat": create_run_cli_bat(),
        "install_ffmpeg.bat": create_install_ffmpeg_bat(),
        "README.txt": create_readme_txt(),
    }

    for filename, content in batch_files.items():
        filepath = os.path.join(PORTABLE_DIR, filename)
        with open(filepath, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(content)
        print(f"  Created: {filename}")

    print(f"\n{'='*50}")
    print(f"  Done! Portable folder: {PORTABLE_DIR}/")
    print()
    print("  Contents:")
    for f in sorted(os.listdir(PORTABLE_DIR)):
        size = os.path.getsize(os.path.join(PORTABLE_DIR, f))
        print(f"    {f:30s} {size:>8,} bytes")
    print()
    print("  Next steps:")
    print(f"  1. Zip the folder:  zip -r VideoTranscriber.zip {PORTABLE_DIR}")
    print("  2. Send VideoTranscriber.zip to your friend")
    print("  3. They unzip, double-click install_ffmpeg.bat, then run.bat")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
