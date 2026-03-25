"""
URL downloading for video/audio content.

Uses yt-dlp as the universal downloader (supports YouTube + hundreds of other sites).
Falls back to direct HTTP download for simple file URLs.

Extracted from qdayanon-content-engine's audio_transcription.py.
"""

import logging
import os
import tempfile
from urllib.parse import urlparse

import requests
import yt_dlp

logger = logging.getLogger(__name__)


def is_url(input_str: str) -> bool:
    """Check if input looks like a URL."""
    return input_str.startswith("http://") or input_str.startswith("https://")


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL (robust to subdomains)."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower().strip()
    return netloc.endswith("youtube.com") or netloc.endswith("youtu.be")


def _get_yt_dlp_opts(output_template: str, progress_hooks: list | None = None) -> dict:
    """Build yt-dlp options for audio extraction."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": False,
        "no_warnings": False,
        "noprogress": False,
    }

    if progress_hooks:
        opts["progress_hooks"] = progress_hooks

    return opts


def _extract_title_from_url(url: str) -> str | None:
    """Try to extract video title from URL metadata without downloading."""
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                return info.get("title")
    except Exception:
        pass
    return None


def download_url(url: str, output_dir: str = "downloads") -> tuple[str, str]:
    """
    Download audio from any URL using yt-dlp.

    Tries yt-dlp first (handles YouTube, Twitter, and hundreds of other sites).
    Falls back to direct HTTP download for simple file URLs.

    Args:
        url: Video/audio URL.
        output_dir: Directory to save downloaded file.

    Returns:
        Tuple of (audio_file_path, title).

    Raises:
        RuntimeError: If download fails.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Try to get title first
    print(f"Fetching info from URL...")
    title = _extract_title_from_url(url)

    if title:
        print(f"Title: {title}")

    # Try yt-dlp first (handles most video/audio sites)
    try:
        return _download_with_ytdlp(url, output_dir, title)
    except Exception as ytdlp_error:
        logger.debug(f"yt-dlp failed: {ytdlp_error}")

        # Fall back to direct HTTP download for simple file URLs
        try:
            return _download_direct(url, output_dir)
        except Exception as http_error:
            raise RuntimeError(
                f"Could not download from URL.\n"
                f"  yt-dlp error: {ytdlp_error}\n"
                f"  HTTP error: {http_error}"
            )


def _download_with_ytdlp(url: str, output_dir: str, title: str | None = None) -> tuple[str, str]:
    """Download audio using yt-dlp."""
    # Use a temp name, then find the actual output file
    temp_base = os.path.join(output_dir, "download_temp")
    opts = _get_yt_dlp_opts(temp_base)

    print("Downloading audio...")

    # Try with default settings first
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not title and info:
                title = info.get("title", "Unknown")
    except Exception as e:
        # If cookie-related error on YouTube, retry without cookies
        error_str = str(e).lower()
        if is_youtube_url(url) and ("cookie" in error_str or "login" in error_str):
            logger.warning("Retrying YouTube download without cookies...")
            opts["sleep_interval"] = 2
            opts["max_sleep_interval"] = 5
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not title and info:
                    title = info.get("title", "Unknown")
        else:
            raise

    # Find the downloaded file (yt-dlp adds extension)
    audio_path = temp_base + ".mp3"
    if not os.path.exists(audio_path):
        # Search for any file matching the temp base
        for ext in [".mp3", ".m4a", ".wav", ".webm", ".opus", ".ogg"]:
            candidate = temp_base + ext
            if os.path.exists(candidate):
                audio_path = candidate
                break
        else:
            raise FileNotFoundError(f"Downloaded file not found at {temp_base}.*")

    print(f"Downloaded: {os.path.basename(audio_path)}")
    return audio_path, title or "Unknown"


def _download_direct(url: str, output_dir: str) -> tuple[str, str]:
    """Download a direct file URL via HTTP."""
    print("Downloading file directly...")

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    # Determine filename from URL or content-disposition
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "download"

    # Ensure it has an extension
    if "." not in filename:
        content_type = response.headers.get("content-type", "")
        if "mp4" in content_type:
            filename += ".mp4"
        elif "mp3" in content_type or "mpeg" in content_type:
            filename += ".mp3"
        elif "wav" in content_type:
            filename += ".wav"
        else:
            filename += ".mp4"  # Default assumption

    filepath = os.path.join(output_dir, filename)

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                print(f"\rDownloading: {pct}%", end="", flush=True)

    if total:
        print()  # Newline after progress

    # Title from filename
    title = os.path.splitext(filename)[0]
    print(f"Downloaded: {filename}")
    return filepath, title
