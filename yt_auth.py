"""
YouTube OAuth 2.0 authorization.

One-time (or rarely) — opens a browser, user approves, refresh token is saved
to secrets/yt-tokens.json. Format matches the hongkongaipodcast-site TypeScript
version so both projects can share the same tokens file.

Run directly (`python yt_auth.py`) or call `run_auth_flow()` from the GUI.
"""

import glob
import http.server
import json
import os
import socket
import sys
import threading
import time
import urllib.parse
import webbrowser

import requests


OAUTH_PORT = 3333
REDIRECT_URI = f"http://localhost:{OAUTH_PORT}"
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_secrets_dir() -> str:
    """Resolve secrets/ dir: next to .exe when frozen, else next to this script."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "secrets")


def find_client_secret(secrets_dir: str) -> str:
    """Find client_secret_*.json in the secrets folder."""
    matches = glob.glob(os.path.join(secrets_dir, "client_secret_*.json"))
    if not matches:
        raise FileNotFoundError(
            f"No client_secret_*.json in {secrets_dir}. "
            "Download it from Google Cloud Console (OAuth client, Desktop type)."
        )
    return matches[0]


def load_client_credentials(secrets_dir: str | None = None) -> dict:
    """Load client_id + client_secret from the OAuth client JSON."""
    secrets_dir = secrets_dir or get_secrets_dir()
    path = find_client_secret(secrets_dir)
    with open(path) as f:
        data = json.load(f)
    installed = data.get("installed") or data.get("web")
    if not installed:
        raise ValueError(f"Unexpected client_secret.json format in {path}")
    return installed


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except OSError:
            return False


def run_auth_flow(secrets_dir: str | None = None, log=print) -> dict:
    """
    Run the interactive OAuth flow. Opens browser, catches redirect, exchanges
    the code for tokens, writes them to secrets/yt-tokens.json.

    Returns the saved token dict.
    """
    secrets_dir = secrets_dir or get_secrets_dir()
    os.makedirs(secrets_dir, exist_ok=True)
    creds = load_client_credentials(secrets_dir)

    if not _port_free(OAUTH_PORT):
        raise RuntimeError(
            f"Port {OAUTH_PORT} is in use. Close the other app and try again."
        )

    params = {
        "client_id": creds["client_id"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    received_code: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            qs = urllib.parse.urlparse(self.path).query
            parsed = urllib.parse.parse_qs(qs)
            if "code" in parsed:
                received_code["code"] = parsed["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"<h1>Authorized!</h1><p>You can close this tab.</p>"
                )
            else:
                err = parsed.get("error", ["unknown"])[0]
                received_code["error"] = err
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Authorization failed: {err}".encode())

    server = http.server.HTTPServer(("localhost", OAUTH_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        log("Opening browser for Google sign-in...")
        webbrowser.open(auth_url)

        # Wait up to 5 minutes for the user to finish
        deadline = time.time() + 300
        while time.time() < deadline and not received_code:
            time.sleep(0.2)
    finally:
        server.shutdown()

    if "error" in received_code:
        raise RuntimeError(f"OAuth error: {received_code['error']}")
    if "code" not in received_code:
        raise RuntimeError("Timed out waiting for authorization.")

    log("Exchanging code for tokens...")
    resp = requests.post(
        TOKEN_URL,
        data={
            "code": received_code["code"],
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Token exchange failed: {resp.status_code} {resp.text}")

    tokens = resp.json()
    # Add expiry_date (ms since epoch) for compat with the TS version
    if "expires_in" in tokens:
        tokens["expiry_date"] = int((time.time() + tokens["expires_in"]) * 1000)

    tokens_path = os.path.join(secrets_dir, "yt-tokens.json")
    with open(tokens_path, "w") as f:
        json.dump(tokens, f, indent=2)
    log(f"Tokens saved to {tokens_path}")
    return tokens


if __name__ == "__main__":
    try:
        run_auth_flow()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
