"""
FFmpeg video compression for YouTube upload.

Compresses MP4 videos using H.264 with settings optimized for YouTube's
re-encoding pipeline. Since YouTube re-encodes everything, we can compress
aggressively (CRF 28) for 8-12x file size reduction on typical long-form
content, with negligible quality difference after YouTube processing.

Settings based on YouTube's recommended upload encoding specs:
- H.264 High profile (libx264)
- AAC-LC audio at 128k / 48kHz with loudness normalization (-16 LUFS)
- yuv420p pixel format for compatibility
- faststart flag for streaming/upload optimization

Audio is loudness-normalized to -16 LUFS (YouTube/Spotify/Apple compatible)
so the same output works across platforms if needed later.
"""

import os
import subprocess


# Quality presets: (label, crf, preset, audio_bitrate)
QUALITY_PRESETS = {
    "high_quality": ("High quality (CRF 18)", 18, "slow", "192k"),
    "balanced": ("Balanced (CRF 23)", 23, "slow", "128k"),
    "max_compression": ("Max compression (CRF 28)", 28, "slow", "96k"),
}

DEFAULT_PRESET = "balanced"


def get_video_info(video_path: str) -> dict:
    """Get video file size and duration using ffprobe."""
    info = {"size": os.path.getsize(video_path), "duration": 0}
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            info["duration"] = float(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass
    return info


def compress_for_youtube(
    input_path: str,
    output_path: str | None = None,
    quality: str = DEFAULT_PRESET,
) -> dict:
    """
    Compress a video file for YouTube upload using FFmpeg.

    Args:
        input_path: Path to the source video file.
        output_path: Path for compressed output. Default: input_compressed.mp4
        quality: One of 'high_quality', 'balanced', 'max_compression'.

    Returns:
        Dict with 'output_path', 'input_size', 'output_size', 'ratio'.

    Raises:
        FileNotFoundError: If input file doesn't exist.
        ValueError: If quality preset is invalid.
        RuntimeError: If FFmpeg compression fails.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Video file not found: {input_path}")

    if quality not in QUALITY_PRESETS:
        raise ValueError(f"Unknown quality preset '{quality}'. Use: {', '.join(QUALITY_PRESETS)}")

    _, crf, preset, audio_bitrate = QUALITY_PRESETS[quality]

    # Generate output path if not specified
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_compressed.mp4"

    input_size = os.path.getsize(input_path)
    print(f"Input:   {input_path}")
    print(f"Size:    {_format_size(input_size)}")
    print(f"Quality: CRF {crf}, preset {preset}, audio {audio_bitrate}")
    print(f"Compressing...")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-ar", "48000",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg compression failed:\n{result.stderr[-1000:]}")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("FFmpeg produced empty output file")

    output_size = os.path.getsize(output_path)
    ratio = input_size / output_size if output_size > 0 else 0

    print(f"Output:  {output_path}")
    print(f"Size:    {_format_size(output_size)}")
    print(f"Ratio:   {ratio:.1f}x smaller ({_format_percent(input_size, output_size)} reduction)")

    return {
        "output_path": output_path,
        "input_size": input_size,
        "output_size": output_size,
        "ratio": ratio,
    }


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable units."""
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.2f} GB"
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    return f"{size_bytes / 1024:.0f} KB"


def _format_percent(input_size: int, output_size: int) -> str:
    """Format size reduction as percentage."""
    if input_size == 0:
        return "0%"
    reduction = (1 - output_size / input_size) * 100
    return f"{reduction:.0f}%"
