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
import textwrap


PORTABLE_DIR = os.path.join("portable", "VideoTranscriber")

# Python source files to include
SOURCE_FILES = [
    "gui.py",
    "transcribe.py",
    "transcription.py",
    "downloader.py",
    "srt_formatter.py",
    "cantonese.py",
    "requirements.txt",
]


def create_run_bat():
    """Create the main launcher batch file."""
    return textwrap.dedent(r"""
        @echo off
        title Video Transcriber
        echo ============================================
        echo   Video Transcriber - Starting...
        echo ============================================
        echo.

        REM Check if Python is available
        where python >nul 2>nul
        if %errorlevel% neq 0 (
            echo Python not found! Installing...
            echo.
            echo Downloading Python installer...
            curl -o python_installer.exe https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
            echo.
            echo Installing Python (this may take a minute)...
            python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
            del python_installer.exe
            echo.
            echo Python installed! Please CLOSE this window and double-click run.bat again.
            pause
            exit /b
        )

        REM Check if dependencies are installed (check for faster-whisper)
        python -c "import faster_whisper" >nul 2>nul
        if %errorlevel% neq 0 (
            echo Installing dependencies (first time only, may take a few minutes)...
            echo.
            pip install -r requirements.txt
            echo.
            echo Dependencies installed!
            echo.
        )

        REM Check for ffmpeg
        where ffmpeg >nul 2>nul
        if %errorlevel% neq 0 (
            echo WARNING: ffmpeg not found!
            echo.
            echo Please double-click "install_ffmpeg.bat" first, then try again.
            echo.
            pause
            exit /b
        )

        REM Launch the GUI
        echo Starting transcriber...
        python gui.py

        if %errorlevel% neq 0 (
            echo.
            echo Something went wrong. Press any key to close.
            pause
        )
    """).strip() + "\n"


def create_run_cli_bat():
    """Create CLI launcher."""
    return textwrap.dedent(r"""
        @echo off
        title Video Transcriber (CLI)

        where python >nul 2>nul
        if %errorlevel% neq 0 (
            echo Python not found! Double-click run.bat first to install Python.
            pause
            exit /b
        )

        python -c "import faster_whisper" >nul 2>nul
        if %errorlevel% neq 0 (
            echo Installing dependencies...
            pip install -r requirements.txt
        )

        echo.
        echo Usage: python transcribe.py video.mp4 [options]
        echo.
        echo   -l zh          Force Cantonese
        echo   -l en          Force English
        echo   --domain X     Vocabulary hints (iching, finance, geopolitics...)
        echo   -m tiny        Use faster (less accurate) model
        echo.
        echo Type your command below, or drag a video file onto this window.
        echo Type "exit" to quit.
        echo.

        cmd /k "cd /d %~dp0"
    """).strip() + "\n"


def create_install_ffmpeg_bat():
    """Create ffmpeg installer helper."""
    return textwrap.dedent(r"""
        @echo off
        title Install ffmpeg
        echo ============================================
        echo   Installing ffmpeg...
        echo ============================================
        echo.

        where ffmpeg >nul 2>nul
        if %errorlevel% equ 0 (
            echo ffmpeg is already installed!
            echo.
            pause
            exit /b
        )

        echo Trying winget...
        winget install ffmpeg
        if %errorlevel% equ 0 (
            echo.
            echo ffmpeg installed successfully!
            echo Please CLOSE and REOPEN any command windows for it to take effect.
            echo.
            pause
            exit /b
        )

        echo.
        echo winget didn't work. Trying chocolatey...
        where choco >nul 2>nul
        if %errorlevel% equ 0 (
            choco install ffmpeg -y
            echo.
            echo ffmpeg installed successfully!
            pause
            exit /b
        )

        echo.
        echo ============================================
        echo   Could not install ffmpeg automatically.
        echo.
        echo   Please install it manually:
        echo   1. Go to https://www.gyan.dev/ffmpeg/builds/
        echo   2. Download "ffmpeg-release-essentials.zip"
        echo   3. Extract it
        echo   4. Add the "bin" folder to your system PATH
        echo.
        echo   Or ask your tech friend for help :)
        echo ============================================
        pause
    """).strip() + "\n"


def create_readme_txt():
    """Create a simple readme for the portable folder."""
    return textwrap.dedent("""
        VIDEO TRANSCRIBER
        =================

        Turn any video into subtitles. Works offline after first setup.

        FIRST TIME SETUP (do these once):
        ----------------------------------
        1. Double-click "install_ffmpeg.bat"
           - This installs ffmpeg (needed to read video files)
           - Close and reopen any windows after it finishes

        2. Double-click "run.bat"
           - First time it will install Python and dependencies
           - This takes a few minutes, then the app opens

        AFTER SETUP (every time):
        -------------------------
        1. Double-click "run.bat"
        2. Click "Browse" and pick your video
        3. For Cantonese: set Language to "Cantonese / Chinese (zh)"
        4. Click "Transcribe"
        5. Subtitle files (.srt and .txt) appear next to your video

        TROUBLESHOOTING:
        ----------------
        - "ffmpeg not found" -> Run install_ffmpeg.bat again
        - Very slow -> Change Model to "tiny"
        - Wrong language -> Pick the language manually
        - Still not working -> Send the error message to your tech friend
    """).strip() + "\n"


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
