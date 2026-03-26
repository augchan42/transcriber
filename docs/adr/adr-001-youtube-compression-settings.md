# ADR-001: YouTube Video Compression Settings

**Date:** 2026-03-26
**Status:** Accepted

## Context

We need to compress long-form video before uploading to YouTube. The goal is maximum file size reduction (8-12x) with negligible quality loss in the final YouTube stream. YouTube re-encodes all uploads regardless, so we can compress aggressively on our end.

Audio loudness is normalized to -16 LUFS so the same output is compatible with Spotify (-14 LUFS) and Apple Podcasts (-16 LUFS) if we expand later.

## Decision

Single-pass H.264 CRF encoding with loudness-normalized AAC audio.

### FFmpeg command

```bash
ffmpeg -y -i input.mp4 \
  -c:v libx264 \
  -crf 28 \
  -preset slow \
  -profile:v high \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:a aac \
  -b:a 96k \
  -ar 48000 \
  output.mp4
```

### Flag-by-flag rationale and sources

| Flag | Value | Why | Source |
|------|-------|-----|--------|
| `-c:v libx264` | H.264 codec | YouTube's recommended upload codec. H.265 works but H.264 is faster to encode and universally compatible. | [YouTube recommended upload encoding settings](https://support.google.com/youtube/answer/1722171?hl=en) |
| `-crf 28` | Constant Rate Factor | CRF 28 is the aggressive end of acceptable quality. Since YouTube re-encodes everything to VP9/AV1, the quality difference vs CRF 18 is negligible after their processing. This is where the big file size savings come from. Range: 0 (lossless) to 51 (worst). | [FFmpeg H.264 encoding guide](https://trac.ffmpeg.org/wiki/Encode/H.264); [Mux compression guide](https://www.mux.com/articles/how-to-compress-video-files-while-maintaining-quality-with-ffmpeg) |
| `-preset slow` | Encoding speed/efficiency tradeoff | Slower presets squeeze more compression at the same quality. `slow` is a good tradeoff; `veryslow` has diminishing returns. | [FFmpeg H.264 preset docs](https://trac.ffmpeg.org/wiki/Encode/H.264#Preset) |
| `-profile:v high` | H.264 High profile | Enables all encoding efficiency features (B-frames, CABAC, 8x8 transforms). YouTube explicitly recommends High profile. | [YouTube recommended upload encoding settings](https://support.google.com/youtube/answer/1722171?hl=en) |
| `-pix_fmt yuv420p` | Pixel format | Required for compatibility with all players and platforms. | [YouTube recommended upload encoding settings](https://support.google.com/youtube/answer/1722171?hl=en) |
| `-movflags +faststart` | MP4 metadata placement | Moves the moov atom to the beginning of the file so playback/upload can start before the full file is downloaded. | [FFmpeg MP4 muxer docs](https://ffmpeg.org/ffmpeg-formats.html#mov_002c-mp4_002c-ismv) |
| `-af loudnorm=I=-16:TP=-1.5:LRA=11` | EBU R128 loudness normalization | Normalizes integrated loudness to -16 LUFS with -1.5 dBTP true peak ceiling. -16 LUFS is the target for YouTube and Apple Podcasts; Spotify uses -14 LUFS but normalizes down gracefully from -16. LRA=11 allows natural dynamic range for speech. | [Apple Podcasts audio requirements](https://podcasters.apple.com/support/893-audio-requirements); [Podcast Loudness Standards 2026](https://sone.app/blog/podcast-loudness-standards-2026-spotify-apple-youtube); [FFmpeg loudnorm filter](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) |
| `-c:a aac` | AAC-LC audio codec | YouTube's recommended audio codec. Universal compatibility. | [YouTube recommended upload encoding settings](https://support.google.com/youtube/answer/1722171?hl=en) |
| `-b:a 96k` | Audio bitrate | 96 kbps is sufficient for speech content (podcasts, lectures). Spotify recommends 96 kbps mono minimum. Our presets go up to 192k for high quality. | [Spotify podcast specification](https://support.spotify.com/us/creators/article/podcast-specification-doc/); [Apple Podcasts audio requirements](https://podcasters.apple.com/support/893-audio-requirements) |
| `-ar 48000` | Audio sample rate 48 kHz | YouTube's preferred sample rate. Also standard for broadcast/streaming. | [YouTube recommended upload encoding settings](https://support.google.com/youtube/answer/1722171?hl=en) |

### Quality presets

| Preset | CRF | Audio | Use case | Expected compression |
|--------|-----|-------|----------|---------------------|
| `max_compression` (default) | 28 | 96k | Long-form talk content, lectures | 8-12x |
| `balanced` | 23 | 128k | General video content | 5-8x |
| `high_quality` | 18 | 192k | High-motion or visually important content | 3-5x |

## Alternatives considered

- **Two-pass encoding:** Better for targeting a specific file size, but adds complexity and doubles encode time. CRF single-pass is simpler and good enough since we don't have a target bitrate.
- **H.265 (HEVC):** ~50% better compression than H.264 at equivalent quality, but significantly slower to encode on CPU and less universally supported. YouTube accepts it but recommends H.264.
- **Dual-pass loudnorm:** Analyzes the full file first, then applies precise correction. More accurate but adds a full extra pass. Single-pass loudnorm is sufficient for our use case.
- **AV1:** Best compression available but extremely slow to encode on CPU. Not practical for long videos without hardware encoding.
