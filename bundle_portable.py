#!/usr/bin/env python3
"""
Bundle a fully self-contained VideoTranscriber folder for Windows.

This script:
1. Runs setup_portable.py to create the base folder
2. Downloads embeddable Python 3.12 for Windows
3. Enables pip in the embeddable Python
4. Pre-installs all dependencies into the embedded Python
5. Downloads ffmpeg for Windows
6. Zips everything into VideoTranscriber.zip

After this, your friend just unzips and double-clicks run.bat. Nothing else needed.

Requirements (on YOUR machine):
    - Internet connection
    - Python 3.10+ (any OS)
    - ~2GB free disk space during build

Usage:
    python bundle_portable.py
"""

import io
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile

PORTABLE_DIR = os.path.join("portable", "VideoTranscriber")
PYTHON_DIR = os.path.join(PORTABLE_DIR, "python")
FFMPEG_DIR = os.path.join(PORTABLE_DIR, "ffmpeg")

# Python embeddable package for Windows (amd64)
PYTHON_VERSION = "3.12.8"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"

# get-pip.py
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# ffmpeg release build for Windows
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def download_file(url: str, dest: str, desc: str = ""):
    """Download a file with progress."""
    print(f"  Downloading {desc or url}...")
    urllib.request.urlretrieve(url, dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"  Downloaded: {size_mb:.1f}MB")


def setup_base():
    """Run setup_portable.py to create the base folder structure."""
    print("\n[1/5] Creating base portable folder...")
    result = subprocess.run([sys.executable, "setup_portable.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("setup_portable.py failed")
    print("  Base folder created.")


def setup_python():
    """Download and configure embeddable Python."""
    print(f"\n[2/5] Setting up embeddable Python {PYTHON_VERSION}...")

    if os.path.exists(PYTHON_DIR):
        shutil.rmtree(PYTHON_DIR)
    os.makedirs(PYTHON_DIR)

    # Download embeddable Python
    zip_path = os.path.join(PYTHON_DIR, "python_embed.zip")
    download_file(PYTHON_URL, zip_path, f"Python {PYTHON_VERSION} embeddable")

    # Extract
    print("  Extracting Python...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(PYTHON_DIR)
    os.unlink(zip_path)

    # Enable pip: edit python312._pth to uncomment "import site"
    pth_file = os.path.join(PYTHON_DIR, f"python312._pth")
    if os.path.exists(pth_file):
        with open(pth_file, "r") as f:
            content = f.read()
        # Uncomment "import site" line
        content = content.replace("#import site", "import site")
        with open(pth_file, "w") as f:
            f.write(content)
        print("  Enabled site-packages in Python.")
    else:
        print(f"  WARNING: {pth_file} not found, pip may not work correctly.")

    # Download and run get-pip.py
    getpip_path = os.path.join(PYTHON_DIR, "get-pip.py")
    download_file(GET_PIP_URL, getpip_path, "get-pip.py")

    python_exe = os.path.join(PYTHON_DIR, "python.exe")

    # On Linux/WSL we can't run a Windows .exe directly, so we'll note this
    if platform.system() != "Windows":
        print()
        print("  NOTE: You're on Linux/WSL. Cannot run Windows python.exe here.")
        print("  The portable folder is set up, but dependencies must be installed")
        print("  the first time run.bat is executed on Windows.")
        print("  (run.bat handles this automatically)")
        return

    # On Windows, install pip + dependencies
    print("  Installing pip...")
    subprocess.run([python_exe, getpip_path, "--no-warn-script-location"], check=True)
    os.unlink(getpip_path)

    # Install dependencies
    print("  Installing transcriber dependencies...")
    req_file = os.path.join(PORTABLE_DIR, "requirements.txt")
    subprocess.run(
        [python_exe, "-m", "pip", "install", "--no-warn-script-location", "-r", req_file],
        check=True,
    )
    print("  Dependencies installed.")


def setup_ffmpeg():
    """Download ffmpeg for Windows."""
    print("\n[3/5] Setting up ffmpeg...")

    if os.path.exists(FFMPEG_DIR):
        shutil.rmtree(FFMPEG_DIR)

    zip_path = os.path.join(PORTABLE_DIR, "ffmpeg.zip")
    download_file(FFMPEG_URL, zip_path, "ffmpeg")

    print("  Extracting ffmpeg (this may take a moment)...")
    with zipfile.ZipFile(zip_path, "r") as z:
        # Find the bin directory inside the zip
        bin_files = [f for f in z.namelist() if "/bin/" in f and f.endswith(".exe")]
        os.makedirs(FFMPEG_DIR, exist_ok=True)
        for f in bin_files:
            filename = os.path.basename(f)
            if filename:
                target = os.path.join(FFMPEG_DIR, filename)
                with z.open(f) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                print(f"    Extracted: {filename}")

    os.unlink(zip_path)


def update_run_bat_for_ffmpeg():
    """Update run.bat to add bundled ffmpeg to PATH."""
    print("\n[4/5] Updating run.bat for bundled ffmpeg...")

    run_bat = os.path.join(PORTABLE_DIR, "run.bat")
    with open(run_bat, "r") as f:
        content = f.read()

    # Add ffmpeg to PATH right after cd /d %~dp0
    ffmpeg_path_line = 'set "PATH=%~dp0ffmpeg;%PATH%"'
    if ffmpeg_path_line not in content:
        content = content.replace(
            "cd /d %~dp0",
            "cd /d %~dp0\r\n" + ffmpeg_path_line,
        )
        with open(run_bat, "w") as f:
            f.write(content)

    # Do the same for run_cli.bat
    cli_bat = os.path.join(PORTABLE_DIR, "run_cli.bat")
    with open(cli_bat, "r") as f:
        content = f.read()
    if ffmpeg_path_line not in content:
        content = content.replace(
            "cd /d %~dp0",
            "cd /d %~dp0\r\n" + ffmpeg_path_line,
        )
        with open(cli_bat, "w") as f:
            f.write(content)

    print("  Batch files updated.")


def create_zip():
    """Create the final zip file."""
    print("\n[5/5] Creating VideoTranscriber.zip...")

    zip_path = "VideoTranscriber.zip"
    if os.path.exists(zip_path):
        os.unlink(zip_path)

    # Count files for progress
    file_count = sum(len(files) for _, _, files in os.walk(PORTABLE_DIR))
    print(f"  Zipping {file_count} files...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PORTABLE_DIR):
            for file in files:
                # Never bundle OAuth refresh tokens
                if file == "yt-tokens.json":
                    print(f"  Skipping secret: {file}")
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, "portable")
                zf.write(filepath, arcname)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"  Created: {zip_path} ({size_mb:.1f}MB)")


def main():
    print("=" * 55)
    print("  Building self-contained VideoTranscriber for Windows")
    print("=" * 55)

    setup_base()
    setup_python()
    setup_ffmpeg()
    update_run_bat_for_ffmpeg()
    create_zip()

    print()
    print("=" * 55)
    print("  DONE!")
    print()
    print("  Send VideoTranscriber.zip to your friend.")
    print("  They unzip it and double-click run.bat.")
    print("  That's it — no Python, no ffmpeg install needed.")
    print()
    if platform.system() != "Windows":
        print("  NOTE: Since you built on Linux/WSL, Python dependencies")
        print("  will auto-install on first run (takes a few minutes).")
        print("  If you want them pre-installed, run bundle_portable.py")
        print("  on a Windows machine instead.")
        print()
    print("=" * 55)


if __name__ == "__main__":
    main()
