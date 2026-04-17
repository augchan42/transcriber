"""
Resumable YouTube video upload via the YouTube Data API v3.

Uses only `requests` (no googleapis client) so the portable .exe stays small.

Flow:
1. Load refresh token from secrets/yt-tokens.json, mint a fresh access token.
2. POST metadata to /upload/youtube/v3/videos?uploadType=resumable — get a
   session URL back in the Location header.
3. Write the session URL to a .resume sidecar next to the video.
4. PUT the file in chunks. On network failure we can re-query the session URL
   for the last received byte and continue from there.
5. On success, delete the sidecar.

If the sidecar exists on a subsequent run, we skip step 2 and resume.
"""

import json
import os
import time
from typing import Callable

import requests

from yt_auth import get_secrets_dir, load_client_credentials


UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB — multiple of 256 KB as required by API
MAX_RETRIES = 5

VALID_PRIVACY = ("private", "unlisted", "public")


def load_tokens(secrets_dir: str | None = None) -> dict:
    secrets_dir = secrets_dir or get_secrets_dir()
    path = os.path.join(secrets_dir, "yt-tokens.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No yt-tokens.json in {secrets_dir}. "
            "Click 'Sign in to YouTube' first."
        )
    with open(path) as f:
        return json.load(f)


def save_tokens(tokens: dict, secrets_dir: str | None = None) -> None:
    secrets_dir = secrets_dir or get_secrets_dir()
    path = os.path.join(secrets_dir, "yt-tokens.json")
    with open(path, "w") as f:
        json.dump(tokens, f, indent=2)


def get_access_token(secrets_dir: str | None = None) -> str:
    """Return a valid access token, refreshing it if expired."""
    secrets_dir = secrets_dir or get_secrets_dir()
    tokens = load_tokens(secrets_dir)

    # Refresh if missing, or within 60s of expiry
    expiry_ms = tokens.get("expiry_date", 0)
    needs_refresh = (
        not tokens.get("access_token")
        or expiry_ms < int((time.time() + 60) * 1000)
    )
    if not needs_refresh:
        return tokens["access_token"]

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("No refresh_token in yt-tokens.json. Re-run Sign in to YouTube.")

    creds = load_client_credentials(secrets_dir)
    resp = requests.post(
        TOKEN_URL,
        data={
            "refresh_token": refresh_token,
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Token refresh failed: {resp.status_code} {resp.text}")

    data = resp.json()
    tokens["access_token"] = data["access_token"]
    if "expires_in" in data:
        tokens["expiry_date"] = int((time.time() + data["expires_in"]) * 1000)
    # Google may rotate the refresh_token; keep the new one if provided
    if data.get("refresh_token"):
        tokens["refresh_token"] = data["refresh_token"]
    save_tokens(tokens, secrets_dir)
    return tokens["access_token"]


def _resume_sidecar(video_path: str) -> str:
    return video_path + ".resume"


def _start_resumable_session(
    access_token: str,
    video_path: str,
    title: str,
    description: str,
    privacy: str,
    category_id: str,
) -> str:
    """POST metadata, return the resumable session URL."""
    file_size = os.path.getsize(video_path)
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Length": str(file_size),
        "X-Upload-Content-Type": "video/*",
    }
    resp = requests.post(
        UPLOAD_URL,
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers=headers,
        data=json.dumps(metadata),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Could not start upload session: {resp.status_code} {resp.text}"
        )
    session_url = resp.headers.get("Location")
    if not session_url:
        raise RuntimeError("Upload session URL missing from response headers.")
    return session_url


def _query_upload_offset(session_url: str, file_size: int) -> int:
    """Ask the server how many bytes it has; return next byte to send."""
    resp = requests.put(
        session_url,
        headers={
            "Content-Length": "0",
            "Content-Range": f"bytes */{file_size}",
        },
        timeout=30,
    )
    if resp.status_code in (200, 201):
        # Already complete
        return file_size
    if resp.status_code == 308:
        rng = resp.headers.get("Range")  # e.g. "bytes=0-1048575"
        if not rng:
            return 0
        end = int(rng.split("-")[1])
        return end + 1
    if resp.status_code == 404:
        raise RuntimeError("Upload session expired. Please retry from the start.")
    raise RuntimeError(f"Offset query failed: {resp.status_code} {resp.text}")


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    privacy: str = "unlisted",
    category_id: str = "22",
    secrets_dir: str | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    log: Callable[[str], None] = print,
) -> dict:
    """
    Upload a video with automatic resume on failure.

    Args:
        video_path: Path to the video file.
        title: Video title (max 100 chars).
        description: Video description.
        privacy: 'private', 'unlisted', or 'public'.
        category_id: YouTube category ID (22 = People & Blogs).
        secrets_dir: Override secrets folder location.
        on_progress: Called with (bytes_sent, total_bytes) after each chunk.
        log: Logger function.

    Returns:
        Dict with 'video_id' and 'url'.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if privacy not in VALID_PRIVACY:
        raise ValueError(f"privacy must be one of {VALID_PRIVACY}")
    if len(title) > 100:
        raise ValueError("Title must be 100 characters or fewer.")

    file_size = os.path.getsize(video_path)
    sidecar = _resume_sidecar(video_path)

    access_token = get_access_token(secrets_dir)

    # Reuse an existing session if present
    session_url = None
    if os.path.isfile(sidecar):
        try:
            with open(sidecar) as f:
                saved = json.load(f)
            if saved.get("file_size") == file_size and saved.get("session_url"):
                session_url = saved["session_url"]
                log(f"Resuming previous upload session for {os.path.basename(video_path)}")
        except (json.JSONDecodeError, OSError):
            session_url = None

    if session_url is None:
        log("Starting new upload session...")
        session_url = _start_resumable_session(
            access_token, video_path, title, description, privacy, category_id
        )
        with open(sidecar, "w") as f:
            json.dump({"session_url": session_url, "file_size": file_size}, f)

    # Find out how much was already uploaded (0 for a new session)
    try:
        offset = _query_upload_offset(session_url, file_size)
    except RuntimeError as e:
        # Expired session — throw away the sidecar and start fresh
        if "expired" in str(e).lower():
            os.unlink(sidecar)
            log("Previous session expired; starting fresh.")
            return upload_video(
                video_path, title, description, privacy, category_id,
                secrets_dir, on_progress, log,
            )
        raise

    if offset >= file_size:
        log("Upload already complete on server; finalizing...")

    # Stream chunks from offset → end
    retries = 0
    with open(video_path, "rb") as f:
        f.seek(offset)
        while offset < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            end = offset + len(chunk) - 1

            try:
                resp = requests.put(
                    session_url,
                    headers={
                        "Content-Length": str(len(chunk)),
                        "Content-Range": f"bytes {offset}-{end}/{file_size}",
                    },
                    data=chunk,
                    timeout=300,
                )
            except requests.RequestException as e:
                retries += 1
                if retries > MAX_RETRIES:
                    raise RuntimeError(f"Upload failed after {MAX_RETRIES} retries: {e}")
                backoff = 2 ** retries
                log(f"Network error, retrying in {backoff}s ({retries}/{MAX_RETRIES})...")
                time.sleep(backoff)
                # Re-sync offset with the server before retrying
                offset = _query_upload_offset(session_url, file_size)
                f.seek(offset)
                continue

            if resp.status_code in (200, 201):
                # Final chunk — upload complete
                result = resp.json()
                video_id = result.get("id")
                if os.path.exists(sidecar):
                    os.unlink(sidecar)
                url = f"https://youtu.be/{video_id}" if video_id else None
                log(f"Upload complete: {url}")
                if on_progress:
                    on_progress(file_size, file_size)
                return {"video_id": video_id, "url": url, "response": result}
            if resp.status_code == 308:
                # Chunk accepted, more to go
                offset = end + 1
                retries = 0
                if on_progress:
                    on_progress(offset, file_size)
                continue
            if resp.status_code in (500, 502, 503, 504):
                retries += 1
                if retries > MAX_RETRIES:
                    raise RuntimeError(
                        f"Server error after {MAX_RETRIES} retries: {resp.status_code}"
                    )
                backoff = 2 ** retries
                log(f"Server error {resp.status_code}, retrying in {backoff}s...")
                time.sleep(backoff)
                offset = _query_upload_offset(session_url, file_size)
                f.seek(offset)
                continue

            raise RuntimeError(f"Upload failed: {resp.status_code} {resp.text}")

    raise RuntimeError("Upload ended without a success response.")


def format_size(bytes_: int) -> str:
    if bytes_ >= 1_073_741_824:
        return f"{bytes_ / 1_073_741_824:.2f} GB"
    if bytes_ >= 1_048_576:
        return f"{bytes_ / 1_048_576:.1f} MB"
    return f"{bytes_ / 1024:.0f} KB"
