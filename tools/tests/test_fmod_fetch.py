"""Official SDK transport/staging controls using tiny synthetic data only."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_fmod_access as access
import fetch_fmod_sdk as fetch
from test_fmod_access import catalogue

URL = "https://" + fetch.DOWNLOAD_HOST + "/sdk/" + access.FILENAME + "?Signature=synthetic-secret"


class Response(io.BytesIO):
    def __init__(self, data, length=None):
        super().__init__(data)
        self.code = 200
        self.headers = {} if length is None else {"Content-Length": str(length)}


class FmodFetchControls(unittest.TestCase):
    def test_download_url_comes_from_authenticated_exact_catalogue_entry(self):
        client = Mock()
        client.request.side_effect = [(200, json.dumps(catalogue()).encode()),
                                      (200, json.dumps({"url": URL}).encode())]
        self.assertEqual(fetch.download_url(client, access.Session("synthetic-token", "123")), URL)
        path, authorization = client.request.call_args.args
        self.assertTrue(path.startswith("/api-get-download-link?"))
        self.assertEqual(access.urllib.parse.parse_qs(path.split("?", 1)[1]),
            {"path": ["synthetic-ios-path"], "filename": [access.FILENAME], "user_id": ["123"]})
        self.assertEqual(authorization, "FMOD synthetic-token")

    def test_wrong_file_untrusted_host_and_credentials_in_url_are_rejected(self):
        for value in ["http://" + fetch.DOWNLOAD_HOST + "/sdk/" + access.FILENAME,
                      "https://www.fmod.com.evil.invalid/" + access.FILENAME,
                      "https://evilcloudfront.net/" + access.FILENAME,
                      "https://other.cloudfront.net/" + access.FILENAME,
                      "https://user:password@www.fmod.com/" + access.FILENAME,
                      "https://www.fmod.com:8443/" + access.FILENAME,
                      "https://www.fmod.com/other.dmg", URL + "#fragment", URL + "\n"]:
            with self.subTest(value=value), self.assertRaises(access.AccessError):
                fetch.validate_download_url(value)

    def test_transfer_sends_no_account_header_and_validates_whole_file(self):
        data = b"small synthetic SDK fixture"
        opener = Mock()
        opener.open.return_value = Response(data, len(data))
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(fetch, "ARCHIVE_BYTES", len(data)), \
                patch.object(fetch, "ARCHIVE_SHA256", hashlib.sha256(data).hexdigest()), \
                patch("urllib.request.build_opener", return_value=opener):
            path = fetch.fetch_archive(URL, Path(directory))
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.header_items(), [("User-agent", access.USER_AGENT)])

    def test_partial_corrupt_and_oversized_downloads_cannot_become_installer(self):
        expected = b"synthetic SDK"
        for actual, length in [(b"bad", None), (expected + b"too large", None),
                               (expected, len(expected) + 1)]:
            with self.subTest(actual=actual, length=length), tempfile.TemporaryDirectory() as directory:
                opener = Mock()
                opener.open.return_value = Response(actual, length)
                with patch.object(fetch, "ARCHIVE_BYTES", len(expected)), \
                        patch.object(fetch, "ARCHIVE_SHA256", hashlib.sha256(expected).hexdigest()), \
                        patch("urllib.request.build_opener", return_value=opener):
                    with self.assertRaises(access.AccessError):
                        fetch.fetch_archive(URL, Path(directory))
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_preexisting_partial_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            partial = Path(directory) / (access.FILENAME + ".partial")
            partial.write_bytes(b"preexisting data")
            opener = Mock()
            opener.open.return_value = Response(b"synthetic")
            with patch("urllib.request.build_opener", return_value=opener), self.assertRaises(access.AccessError):
                fetch.fetch_archive(URL, Path(directory))
            self.assertEqual(partial.read_bytes(), b"preexisting data")

    def test_failed_download_logs_out_and_never_mounts(self):
        client = Mock()
        client.request.return_value = (204, b"")
        with patch.object(access, "login", return_value=access.Session("synthetic-token", "123")), \
                patch.object(fetch, "download_url", return_value=URL), \
                patch.object(fetch, "fetch_archive", side_effect=access.AccessError("Synthetic transfer failure")), \
                patch.object(fetch, "stage_sdk") as stage, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(access.AccessError):
                fetch.fetch(client, Path("unused"), {}, "fake", "fake")
        client.request.assert_called_once_with("/api-logout", "FMOD synthetic-token")
        stage.assert_not_called()

    def test_changed_archive_cannot_mount(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(fetch, "run_hdiutil") as mount:
            archive = Path(directory) / "synthetic.dmg"
            archive.write_bytes(b"changed")
            with self.assertRaises(access.AccessError):
                fetch.stage_sdk(archive, Path(directory))
            mount.assert_not_called()

    def test_sdk_validation_rejects_changed_library_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            data = b"synthetic archive"
            library = root / "api/library.a"
            library.parent.mkdir()
            library.write_bytes(data)
            lock = root / "lock.json"
            lock.write_text(json.dumps({"deviceArchives": {"fixture": {"path": "api/library.a",
                "sha256": hashlib.sha256(data).hexdigest()}}}))
            (root / "doc").mkdir()
            (root / "doc/LICENSE.TXT").write_bytes(b"synthetic license")
            (root / "doc/revision.txt").write_text(access.VERSION)
            with patch.object(access, "LOCK", lock), \
                    patch.object(fetch, "LICENSE_SHA256", hashlib.sha256(b"synthetic license").hexdigest()):
                fetch.validate_sdk(root)
                library.write_bytes(b"changed")
                with self.assertRaises(access.AccessError):
                    fetch.validate_sdk(root)
                library.unlink()
                library.symlink_to(root / "doc/LICENSE.TXT")
                with self.assertRaises(access.AccessError):
                    fetch.validate_sdk(root)

    def test_success_receipt_contains_no_signed_url_or_account(self):
        client = Mock()
        client.request.return_value = (204, b"")
        with patch.object(access, "login", return_value=access.Session("synthetic-token", "123")), \
                patch.object(fetch, "download_url", return_value=URL), \
                patch.object(fetch, "fetch_archive", return_value=Path("fixture.dmg")), \
                patch.object(fetch, "stage_sdk", return_value=(access.ROOT / ".private/fixture/sdk", {})), \
                contextlib.redirect_stdout(io.StringIO()):
            receipt = fetch.fetch(client, access.ROOT / ".private/fixture", {}, "fake@example.invalid", "fake-password")
        self.assertEqual(receipt["status"], "PASS_OFFICIAL_FMOD_SDK")
        for secret in [URL, "synthetic-secret", "synthetic-token", "fake@example.invalid", "fake-password"]:
            self.assertNotIn(secret, json.dumps(receipt))

    def test_sdk_work_cannot_be_public_or_reused(self):
        for value in [".build/sdk", "public/sdk", ".private/../public/sdk", ".private"]:
            with self.subTest(value=value), self.assertRaises(access.AccessError):
                fetch.private_work(value)


if __name__ == "__main__":
    unittest.main()
