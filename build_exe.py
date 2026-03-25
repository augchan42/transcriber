#!/usr/bin/env python3
"""
Build standalone Windows .exe files for the transcriber.

Requirements:
    pip install pyinstaller

Usage:
    python build_exe.py          # Build both GUI and CLI
    python build_exe.py --gui    # GUI only (recommended for non-technical users)
    python build_exe.py --cli    # CLI only

This creates:
    dist/transcriber.exe    — GUI app (double-click to open)
    dist/transcribe.exe     — CLI app (command line)

Your friend only needs transcriber.exe + ffmpeg installed on their system.
The Whisper model will be downloaded automatically on first run.
"""

import argparse
import subprocess
import sys


def build(name: str, entry: str, windowed: bool) -> bool:
    """Build a single .exe target."""
    print(f"Building {name}...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", name,
        "--windowed" if windowed else "--console",
        # Include our modules
        "--hidden-import", "faster_whisper",
        "--hidden-import", "ctranslate2",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "requests",
        # Collect data files needed by faster-whisper and ctranslate2
        "--collect-data", "faster_whisper",
        "--collect-data", "ctranslate2",
        # Entry point
        entry,
    ]

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Build transcriber .exe files")
    parser.add_argument("--gui", action="store_true", help="Build GUI version only")
    parser.add_argument("--cli", action="store_true", help="Build CLI version only")
    args = parser.parse_args()

    # Default: build both
    build_gui = not args.cli or args.gui
    build_cli = not args.gui or args.cli
    if not args.gui and not args.cli:
        build_gui = True
        build_cli = True

    print("This may take a few minutes.\n")

    results = []

    if build_gui:
        ok = build("transcriber", "gui.py", windowed=True)
        results.append(("dist/transcriber.exe (GUI)", ok))

    if build_cli:
        ok = build("transcribe", "transcribe.py", windowed=False)
        results.append(("dist/transcribe.exe (CLI)", ok))

    print("\n" + "=" * 60)
    for name, ok in results:
        status = "OK" if ok else "FAILED"
        print(f"  [{status}] {name}")

    if all(ok for _, ok in results):
        print()
        print("  For your friend, give them transcriber.exe (GUI version).")
        print("  They double-click it, pick a video, and hit Transcribe.")
        print()
        print("  They also need ffmpeg installed once:")
        print("    Open Command Prompt -> winget install ffmpeg")
    else:
        print()
        print("  Some builds failed. Make sure PyInstaller is installed:")
        print("    pip install pyinstaller")

    print("=" * 60)

    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
