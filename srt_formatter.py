"""
SRT and TXT subtitle file generation.

Converts transcription segments (with start/end timestamps) into
standard .srt subtitle files and plain .txt transcripts.
"""

import os
import re
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format: HH:MM:SS,mmm

    >>> format_timestamp(3723.456)
    '01:02:03,456'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    # Clamp millis to 999 in case of floating point rounding
    millis = min(millis, 999)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments: list[dict], output_path: str) -> str:
    """
    Write segments to an SRT subtitle file.

    Args:
        segments: List of dicts with 'start' (float), 'end' (float), 'text' (str).
        output_path: Path for the output .srt file.

    Returns:
        The output path written to.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # UTF-8 with BOM for maximum compatibility with media players
    with open(output_path, "w", encoding="utf-8-sig") as f:
        index = 1
        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue

            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])

            f.write(f"{index}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n")
            f.write("\n")
            index += 1

    return output_path


def write_txt(segments: list[dict], output_path: str) -> str:
    """
    Write segments as plain text transcript.

    Args:
        segments: List of dicts with 'text' (str).
        output_path: Path for the output .txt file.

    Returns:
        The output path written to.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    text = " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text", "").strip())

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text + "\n")

    return output_path


def sanitize_filename(name: str) -> str:
    """
    Make a string safe for use as a filename.

    Removes/replaces characters that are unsafe on Windows/Linux filesystems.
    """
    # Replace common unsafe characters with underscore
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # Collapse multiple underscores/spaces
    name = re.sub(r"[_\s]+", "_", name)
    # Strip leading/trailing underscores and dots
    name = name.strip("_. ")
    # Truncate to reasonable length
    if len(name) > 200:
        name = name[:200]
    return name or "transcription"


def generate_output_path(input_name: str, output_dir: str | None, extension: str) -> str:
    """
    Generate output file path from input name.

    For local files: same basename with new extension, in output_dir or same directory.
    For URL-derived titles: sanitized title with extension, in output_dir or ./output.

    Args:
        input_name: Original filename or video title.
        output_dir: Output directory (None = auto).
        extension: File extension including dot (e.g., '.srt').

    Returns:
        Full output file path.
    """
    # Determine the base name
    input_path = Path(input_name)
    if input_path.exists():
        # Local file — use same directory unless output_dir specified
        base = input_path.stem
        default_dir = str(input_path.parent)
    else:
        # URL-derived title
        base = sanitize_filename(input_name)
        default_dir = "output"

    out_dir = output_dir or default_dir
    os.makedirs(out_dir, exist_ok=True)

    return os.path.join(out_dir, base + extension)
