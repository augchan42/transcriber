"""
Core transcription engine using faster-whisper (CTranslate2 backend).

Handles model loading, audio extraction from video, and transcription
with timestamp segments. CPU-only with int8 quantization.

Extracted from qdayanon-content-engine's audio_transcription.py.
"""

import logging
import os
import subprocess
import tempfile

from faster_whisper import WhisperModel

from cantonese import apply_cantonese_corrections, get_domain_prompt

logger = logging.getLogger(__name__)

# Model cache to avoid reloading
_model_cache: dict[str, WhisperModel] = {}


def load_model(model_size: str, compute_type: str | None = None) -> WhisperModel:
    """
    Load a faster-whisper model for CPU inference.

    Auto-selects int8 quantization if AVX2 is available, otherwise float32.
    Models are cached globally so subsequent calls with the same size are instant.

    Args:
        model_size: 'tiny', 'base', 'small', 'medium', or 'large-v3'.
        compute_type: Override quantization type. None = auto-detect.

    Returns:
        WhisperModel instance.
    """
    if not model_size or not isinstance(model_size, str) or not model_size.strip():
        logger.warning(f"Invalid model_size '{model_size}', defaulting to 'base'")
        model_size = "base"

    if compute_type is None:
        try:
            import ctranslate2
            supported = ctranslate2.get_supported_compute_types("cpu")
            compute_type = "int8" if "int8" in supported else "float32"
        except Exception:
            compute_type = "float32"

    cache_key = f"{model_size}_cpu_{compute_type}"
    if cache_key not in _model_cache:
        logger.info(f"Loading Whisper model: {model_size} (CPU, {compute_type})")
        print(f"Loading model: {model_size} ({compute_type} quantization)...")
        _model_cache[cache_key] = WhisperModel(model_size, device="cpu", compute_type=compute_type)
        print("Model loaded.")

    return _model_cache[cache_key]


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def video_has_audio_stream(video_path: str) -> bool:
    """Check if a video file contains an audio stream using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        return "audio" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If ffprobe is missing, assume audio exists and let ffmpeg handle it
        return True


def extract_audio_from_video(video_path: str) -> str:
    """
    Extract audio from a video file to a temporary WAV file using ffmpeg.

    Args:
        video_path: Path to the video file.

    Returns:
        Path to the extracted .wav audio file (caller should clean up).

    Raises:
        RuntimeError: If extraction fails or video has no audio.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not video_has_audio_stream(video_path):
        raise RuntimeError(f"Video file has no audio track: {video_path}")

    # Create temp file for extracted audio
    temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(temp_fd)

    try:
        print("Extracting audio from video...")
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vn",                    # No video
                "-acodec", "pcm_s16le",   # 16-bit PCM WAV
                "-ar", "16000",           # 16kHz (Whisper's native rate)
                "-ac", "1",               # Mono
                temp_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr[-500:]}")

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            raise RuntimeError("ffmpeg produced empty audio file")

        return temp_path

    except Exception:
        # Clean up on failure
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def transcribe_with_timestamps(
    audio_path: str,
    model_size: str = "base",
    language: str | None = None,
    domain_category: str | None = None,
    max_duration: int | None = None,
) -> dict:
    """
    Transcribe an audio file and return segments with timestamps.

    Args:
        audio_path: Path to audio file (.wav, .mp3, etc.).
        model_size: Whisper model size.
        language: Force language code (e.g., 'en', 'zh'). None = auto-detect.
        domain_category: Domain for Cantonese vocabulary hints (e.g., 'iching').
        max_duration: Only transcribe first N seconds (for testing).

    Returns:
        Dict with 'text' (str), 'segments' (list of dicts), 'language' (str).
    """
    model = load_model(model_size)

    # Get domain-specific vocabulary prompt for Cantonese
    initial_prompt = get_domain_prompt(domain_category) if domain_category else None
    if initial_prompt:
        logger.info(f"Using domain prompt for '{domain_category}'")

    print(f"Transcribing (language: {language or 'auto-detect'})...")

    transcribe_kwargs = {
        "audio": audio_path,
        "language": language,
        "initial_prompt": initial_prompt,
        "log_progress": True,
    }
    if max_duration:
        transcribe_kwargs["clip_timestamps"] = f"0,{max_duration}"

    segments_generator, info = model.transcribe(**transcribe_kwargs)

    if info is None:
        raise RuntimeError("Transcription returned no info — model may have failed to process audio")

    # Collect segments
    segment_list = []
    for seg in segments_generator:
        if seg is None:
            continue
        segment_list.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip() if seg.text else "",
        })

    transcript = " ".join(seg["text"] for seg in segment_list)
    detected_language = info.language

    logger.info(f"Detected language: {detected_language} (probability: {info.language_probability:.3f})")

    # Garbled transcription detection — retry with English
    if not language and detected_language != "en":
        garbled_indicators = [
            "Fuck replacement",
            "Mae aa",
            "yn cfangygyng",
            "fel ddyn nad",
        ]
        if any(indicator in transcript for indicator in garbled_indicators):
            print("Transcription looks garbled, retrying with English...")
            retry_segments, retry_info = model.transcribe(
                audio=audio_path,
                language="en",
                initial_prompt=initial_prompt,
            )
            segment_list = []
            for seg in retry_segments:
                if seg is None:
                    continue
                segment_list.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip() if seg.text else "",
                })
            transcript = " ".join(seg["text"] for seg in segment_list)
            detected_language = "en"

    # Apply Cantonese corrections when Chinese-family language detected
    if detected_language in ("yue", "zh", "zh-TW", "zh-HK", "cmn"):
        original = transcript
        transcript = apply_cantonese_corrections(transcript, domain=domain_category)
        for seg in segment_list:
            seg["text"] = apply_cantonese_corrections(seg["text"], domain=domain_category)
        if transcript != original:
            print(f"Applied Cantonese corrections (domain: {domain_category or 'general'})")

    # Compute duration from last segment
    duration = segment_list[-1]["end"] if segment_list else 0

    print(f"Transcription complete: {len(segment_list)} segments, {duration:.1f}s, language={detected_language}")

    return {
        "text": transcript,
        "segments": segment_list,
        "language": detected_language,
        "duration": duration,
    }
