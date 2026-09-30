#!/usr/bin/env python3
"""Download Cabrillo's pinned SDK directly from FMOD into a private local directory.

Uses hidden terminal prompts, a temporary FMOD session and a vendor-issued link.
Never saves account credentials, tokens, the catalogue or signed download URLs.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

import check_fmod_access as access

# Independently measured from the retained original before the official fetch.
ARCHIVE_SHA256 = "7f1934f248df7202b8efb6951570f60c52566217e230f26ed3682a6447336e5f"
ARCHIVE_BYTES = 143583015
LICENSE_SHA256 = "c181e2efedd10cb670974ca89779db5ddc38f1991a6c05e98e9d11691be002e1"
DOWNLOAD_HOST = "d2m8b09s60for2.cloudfront.net"


def download_url(client, session):
    status, body = client.request("/api-downloads", "FMOD " + session.token)
    if status != 200:
        raise access.AccessError("FMOD did not authorize its download catalogue.")
    entry = access.sdk_available(access.read_json(body))
    query = urllib.parse.urlencode(dict(entry, user_id=session.user))
    status, body = client.request("/api-get-download-link?" + query, "FMOD " + session.token)
    if status != 200:
        raise access.AccessError("FMOD did not issue a download link for the pinned SDK.")
    url = access.read_json(body).get("url")
    validate_download_url(url)
    return url


def validate_download_url(url):
    if not isinstance(url, str) or len(url) > 16384 or any(ord(char) <= 32 for char in url):
        raise access.AccessError("FMOD returned an invalid download link.")
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    # Observed in the successful official 2026-09-30 SDK download. Re-review if
    # FMOD changes CDN. A separate client sends no account headers or cookies.
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment \
            or parsed.port not in (None, 443) \
            or host != DOWNLOAD_HOST:
        raise access.AccessError("FMOD's download destination needs review; no request was sent.")
    if urllib.parse.unquote(parsed.path).split("/")[-1] != access.FILENAME:
        raise access.AccessError("FMOD's download link names a different file.")
    return host


def private_work(value):
    path = (access.ROOT / value).absolute()
    if path.resolve() != path or access.ROOT / ".private" not in path.parents:
        raise access.AccessError("Choose a normal, fresh directory beneath this checkout's ignored .private directory.")
    if path.exists():
        raise access.AccessError("The private work directory already exists; choose a fresh one.")
    return path


def fetch_archive(url, work):
    validate_download_url(url)
    destination = work / access.FILENAME
    partial = work / (access.FILENAME + ".partial")
    opener = urllib.request.build_opener(access.NoRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": access.USER_AGENT})
    digest = hashlib.sha256()
    size = 0
    owns_partial = False
    try:
        with opener.open(request, timeout=60) as response:
            if response.code != 200:
                raise access.AccessError("FMOD's SDK download did not return a file.")
            length = response.headers.get("Content-Length")
            if length is not None and length != str(ARCHIVE_BYTES):
                raise access.AccessError("FMOD's SDK download size differs from the pinned installer.")
            with partial.open("xb") as stream:
                owns_partial = True
                os.chmod(partial, 0o600)
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > ARCHIVE_BYTES:
                        raise access.AccessError("FMOD's SDK download exceeded the pinned installer size.")
                    digest.update(block)
                    stream.write(block)
        if size != ARCHIVE_BYTES or digest.hexdigest() != ARCHIVE_SHA256:
            raise access.AccessError("FMOD's SDK installer checksum differs; nothing will be mounted.")
        if destination.exists():
            raise access.AccessError("SDK destination unexpectedly exists; it was not replaced.")
        partial.rename(destination)
    except urllib.error.HTTPError as error:
        error.close()
        raise access.AccessError("SDK transfer failed; the signed URL and server details were not logged.") from None
    except (urllib.error.URLError, OSError, ValueError):
        raise access.AccessError("SDK transfer failed; the signed URL and server details were not logged.") from None
    finally:
        if owns_partial and partial.exists():
            partial.unlink()
    return destination


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def checked_sdk_file(root, name):
    path = root / name
    if path.resolve() != path or not path.is_file():
        raise access.AccessError("The mounted FMOD SDK contains an unexpected or aliased input.")
    return path


def validate_sdk(root):
    lock = json.loads(access.LOCK.read_text())
    hashes = {}
    for kind, row in lock["deviceArchives"].items():
        digest = sha(checked_sdk_file(root, row["path"]))
        if digest != row["sha256"]:
            raise access.AccessError("An FMOD device library differs from Cabrillo's pinned input.")
        hashes[kind] = digest
    if sha(checked_sdk_file(root, "doc/LICENSE.TXT")) != LICENSE_SHA256:
        raise access.AccessError("The SDK license differs from the reviewed version.")
    if access.VERSION not in checked_sdk_file(root, "doc/revision.txt").read_text():
        raise access.AccessError("The SDK revision does not identify the pinned version.")
    return hashes


def run_hdiutil(*arguments):
    result = subprocess.run(["/usr/bin/hdiutil", *map(str, arguments)], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if result.returncode:
        raise access.AccessError("macOS could not mount or detach the SDK image; no license prompt was accepted.")


def stage_sdk(archive, work):
    # Validate before mounting even when called separately from the downloader.
    if archive.stat().st_size != ARCHIVE_BYTES or sha(archive) != ARCHIVE_SHA256:
        raise access.AccessError("The SDK installer changed before mounting.")
    mount = work / "mount"
    mount.mkdir(mode=0o700)
    mounted = False
    try:
        run_hdiutil("attach", "-readonly", "-nobrowse", "-noautoopen", "-mountpoint", mount, archive)
        mounted = True
        source = mount / "FMOD Programmers API"
        hashes = validate_sdk(source)
        target = work / "sdk"
        target.mkdir(mode=0o700)
        lock = json.loads(access.LOCK.read_text())
        names = [row["path"] for row in lock["deviceArchives"].values()]
        names += ["doc/LICENSE.TXT", "doc/revision.txt"]
        for name in names:
            output = target / name
            output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(checked_sdk_file(source, name), output)
            os.chmod(output, 0o600)
        if validate_sdk(target) != hashes:
            raise access.AccessError("Staged FMOD inputs changed during copying.")
    finally:
        # A failed attach may still have created the requested mount point.
        if mounted or os.path.ismount(mount):
            run_hdiutil("detach", mount)
    return target, hashes


def fetch(client, work, receipt, username, password):
    session = access.login(client, username, password)
    try:
        url = download_url(client, session)
        host = validate_download_url(url)
        print("Downloading the pinned FMOD iOS installer; its temporary URL is not logged.", flush=True)
        archive = fetch_archive(url, work)
    finally:
        status, _ = client.request("/api-logout", "FMOD " + session.token)
        if status not in (200, 204):
            raise access.AccessError("The temporary FMOD session could not be closed; no session was saved locally.")
    print("Installer checksum matches. Validating and staging its iOS libraries.", flush=True)
    sdk, hashes = stage_sdk(archive, work)
    return dict(receipt, status="PASS_OFFICIAL_FMOD_SDK", authentication_attempted=True,
                sdk_downloaded=True, temporary_session_closed=True,
                archive_sha256=ARCHIVE_SHA256, archive_bytes=ARCHIVE_BYTES,
                device_archives_sha256=hashes, license_sha256=LICENSE_SHA256,
                download_host=host, sdk_path=str(sdk.relative_to(access.ROOT)),
                scope="Official authenticated download and exact SDK input validation; no IPA build or Actions run.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, help="Fresh directory under .private for the SDK")
    parser.add_argument("--report", required=True, help="Safe receipt under .build")
    parser.add_argument("--credentials-from-env", action="store_true",
                        help="Explicit unattended mode; consume CABRILLO_FMOD_USERNAME/PASSWORD")
    args = parser.parse_args(argv)
    try:
        work = private_work(args.work)
        report = access.report_path(args.report)
        client = access.Client()
        receipt = access.probe(client)
        print("Sign in only to https://www.fmod.com; credentials and the session stay in memory.")
        username, password = access.credentials(args.credentials_from_env)
        work.mkdir(parents=True, mode=0o700)
        try:
            receipt = fetch(client, work, receipt, username, password)
        finally:
            del username, password
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        return 0
    except access.AccessError as error:
        print("FMOD SDK fetch stopped: " + str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("FMOD SDK fetch cancelled.", file=sys.stderr)
        return 130
    except Exception:
        print("FMOD SDK fetch stopped unexpectedly; no exception details were logged.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
