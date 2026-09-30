#!/usr/bin/env python3
"""Check FMOD SDK access locally; never download or publish SDK components.

`probe` needs no credentials. `check-account` asks privately in a real terminal,
checks the exact pinned SDK in the authenticated catalogue, then logs out. This
uses the website flow observed on 2026-09-30, not a promised public FMOD API.
"""

import argparse
import base64
from dataclasses import dataclass
import getpass
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://www.fmod.com"
USER_AGENT = "Cabrillo-FMOD-Preparation/1.0"
LOCK = ROOT / "experiments/ios-jit/launcher-owned-game/public-build/fmod-inputs.json"
VERSION = "1.10.09"
FILENAME = "fmodstudioapi11009ios-installer.dmg"
# Public website assets are inspected, never executed or committed to this repo.
# Re-review the sign-in/download implementation if these change.
WEBSITE_ASSETS = {
    "/bundle.js": "358709ab352db862f028436d555e069251c6b463898019799b311b00084ce6f5",
    "/download.chunk.js": "3bd5c44d2dd377aedd4d2c917894c2df164988aa7aaa4cea9f6bc2ba05e9340f",
}
API_PATHS = {"/api-login", "/api-downloads", "/api-logout", "/api-get-download-link"}
MAX_RESPONSE = 8 * 1024 * 1024


class AccessError(Exception):
    """A deliberately non-sensitive message suitable for console output."""


@dataclass(frozen=True, repr=False)
class Session:
    token: str
    user: str


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an account password or token, even to the same host.
        return None


class Client:
    def __init__(self):
        # No browser cookies, saved sessions, .netrc or password-store access.
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, path, authorization=None, data=None):
        parsed = urllib.parse.urlsplit(path)
        if parsed.scheme or parsed.netloc or parsed.fragment or parsed.path not in API_PATHS | WEBSITE_ASSETS.keys():
            raise AccessError("Unexpected FMOD endpoint; review required.")
        if parsed.query:
            query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            if parsed.path != "/api-get-download-link" or set(query) != {"path", "filename", "user_id"} \
                    or any(len(values) != 1 or not values[0] for values in query.values()):
                raise AccessError("Unexpected FMOD endpoint parameters; review required.")
        if authorization is not None and parsed.path not in API_PATHS:
            raise AccessError("Credentials cannot be sent to a website asset.")
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if authorization is not None:
            headers["Authorization"] = authorization
        if data is not None:
            # Match the website's XMLHttpRequest.send(JSON.stringify(null)).
            headers["Content-Type"] = "text/plain;charset=UTF-8"
        request = urllib.request.Request(ORIGIN + path, data=data, headers=headers)
        try:
            try:
                response = self.opener.open(request, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                status = response.code
                # Discard error bodies: servers can echo submitted credentials.
                body = response.read(MAX_RESPONSE + 1) if status == 200 else b""
        except (urllib.error.URLError, OSError, ValueError):
            raise AccessError("FMOD request failed; no response details were logged.") from None
        if len(body) > MAX_RESPONSE:
            raise AccessError("FMOD response exceeded the expected size.")
        if 300 <= status < 400:
            raise AccessError("FMOD returned a redirect; it was not followed.")
        return status, body


def read_json(body):
    try:
        value = json.loads(body)
    except (ValueError, UnicodeError, RecursionError):
        raise AccessError("FMOD returned an unexpected response format.") from None
    if not isinstance(value, dict):
        raise AccessError("FMOD returned an unexpected response structure.")
    return value


def probe(client):
    lock = json.loads(LOCK.read_text())
    if lock["version"] != VERSION:
        raise AccessError("The pinned FMOD version changed; review required.")
    for path, expected in WEBSITE_ASSETS.items():
        status, body = client.request(path)
        if status != 200 or hashlib.sha256(body).hexdigest() != expected:
            raise AccessError("FMOD's website changed or was unavailable; re-review before sign-in.")
    status, _ = client.request("/api-downloads")
    if status != 401:
        raise AccessError("The anonymous catalogue check did not reach the expected sign-in boundary.")
    return {
        "schema": 1,
        "status": "CREDENTIALS_REQUIRED",
        "origin": ORIGIN,
        "website_assets_sha256": WEBSITE_ASSETS,
        "anonymous_catalogue_http_status": status,
        "fmod_version": VERSION,
        "expected_filename": FILENAME,
        "device_archives_sha256": {
            name: row["sha256"] for name, row in lock["deviceArchives"].items()
        },
        "authentication_attempted": False,
        "sdk_downloaded": False,
        "scope": "Public website flow and authentication boundary only; no SDK or build validation.",
    }


def prompt_credentials():
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise AccessError("Run check-account yourself in Terminal for hidden credential entry.")
    # Never let getpass fall back to echoing a password on an unsupported TTY.
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            username = getpass.getpass("FMOD username or email (hidden): ")
            password = getpass.getpass("FMOD password (hidden): ")
        except (EOFError, getpass.GetPassWarning):
            raise AccessError("Hidden credential entry is unavailable; no sign-in attempted.") from None
    if not username or not password:
        raise AccessError("Both FMOD credentials are required; no sign-in attempted.")
    return username, password


def credentials(from_environment=False):
    if not from_environment:
        return prompt_credentials()
    # Explicit CI mode only. Remove these from this process's environment so
    # later native build/mount subprocesses cannot inherit the account secrets.
    username = os.environ.pop("CABRILLO_FMOD_USERNAME", "")
    password = os.environ.pop("CABRILLO_FMOD_PASSWORD", "")
    if not username or not password:
        raise AccessError("Both CABRILLO_FMOD_USERNAME and CABRILLO_FMOD_PASSWORD must be supplied privately.")
    return username, password


def login(client, username, password):
    # encodeURIComponent() both values, lowercase the username, then Base64.
    # Standard HTTP Basic alone would corrupt spaces, ':' and non-ASCII input.
    safe = "~!*'()-._"
    value = urllib.parse.quote(username.lower(), safe=safe) + ":" + urllib.parse.quote(password, safe=safe)
    authorization = "Basic " + base64.b64encode(value.encode("ascii")).decode("ascii")
    status, body = client.request("/api-login", authorization, b"null")
    if status != 200:
        raise AccessError("FMOD sign-in was not accepted. Check the account or sign in on fmod.com.")
    response = read_json(body)
    token = response.get("token")
    user = str(response.get("user", ""))
    if response.get("redir") or not isinstance(token, str) or not token or len(token) > 16384:
        raise AccessError("FMOD sign-in needs browser verification or a protocol review.")
    if not all(33 <= ord(char) <= 126 for char in token):
        raise AccessError("FMOD returned an invalid session format.")
    if not user.isascii() or not user.isdigit() or len(user) > 20:
        raise AccessError("FMOD returned an invalid account identifier format.")
    return Session(token, user)


def sdk_available(catalogue):
    """Select only the exact requested SDK; never substitute a newer version."""
    try:
        candidates = []
        for category in catalogue["downloads"]["categories"]:
            for product in category["products"]:
                if product["title"] != "FMOD Engine":
                    continue
                for version in product["versions"]:
                    if version["version"] != VERSION:
                        continue
                    for platform in version["platforms"]:
                        for slot in (1, 2):
                            prefix = "dl" + str(slot)
                            if platform.get(prefix + "filename") == FILENAME:
                                sdk_path = platform.get(prefix + "Path")
                                candidates.append({"path": sdk_path, "filename": FILENAME})
                                if platform.get(prefix + "disabled") or not isinstance(sdk_path, str) or not sdk_path:
                                    raise AccessError("The pinned FMOD SDK is listed but unavailable to this account.")
        if len(candidates) != 1:
            raise AccessError("The exact pinned FMOD iOS SDK was absent or ambiguous; no substitute selected.")
        return candidates[0]
    except (KeyError, TypeError, AttributeError):
        raise AccessError("FMOD's catalogue format changed; review required.") from None


def check_account(client, receipt, username, password):
    session = login(client, username, password)
    try:
        status, body = client.request("/api-downloads", "FMOD " + session.token)
        if status != 200:
            raise AccessError("FMOD did not authorize access to the download catalogue.")
        sdk_available(read_json(body))
    finally:
        # Use only the newly created session. No browser session is touched.
        status, _ = client.request("/api-logout", "FMOD " + session.token)
        if status not in (200, 204):
            raise AccessError("The temporary FMOD session could not be closed; no session was saved locally.")
    return dict(receipt, status="PINNED_SDK_LISTED", authentication_attempted=True,
                temporary_session_closed=True,
                scope="Exact SDK listed for this account; download, SDK hashes and build still unverified.")


def report_path(value):
    path = (ROOT / value).absolute()
    if path.resolve() != path or ROOT / ".build" not in path.parents:
        raise AccessError("Reports must use a normal path beneath this checkout's ignored .build directory.")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("probe", "check-account"))
    parser.add_argument("--report", help="Optional safe receipt in this checkout's .build directory")
    parser.add_argument("--credentials-from-env", action="store_true",
                        help="Explicit unattended mode; consume CABRILLO_FMOD_USERNAME/PASSWORD")
    args = parser.parse_args(argv)
    try:
        destination = report_path(args.report) if args.report else None
        client = Client()
        receipt = probe(client)
        if args.command == "check-account":
            print("Sign in only to https://www.fmod.com; credentials and the session stay in memory.")
            username, password = credentials(args.credentials_from_env)
            try:
                receipt = check_account(client, receipt, username, password)
            finally:
                del username, password
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        return 0
    except AccessError as error:
        print("FMOD access check stopped: " + str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("FMOD access check cancelled.", file=sys.stderr)
        return 130
    except Exception:
        # Raw exceptions/tracebacks can retain credentials or signed URLs.
        print("FMOD access check stopped unexpectedly; no exception details were logged.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
