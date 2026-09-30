"""Local FMOD preparation boundaries; synthetic accounts, never live sign-ins."""

import base64
import contextlib
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_fmod_access as fmod


def catalogue(filename=fmod.FILENAME, disabled=False):
    return {"downloads": {"categories": [{"products": [{"title": "FMOD Engine",
        "versions": [{"version": fmod.VERSION, "platforms": [{
            "dl1filename": filename, "dl1Path": "synthetic-ios-path",
            "dl1disabled": disabled}]}]}]}]}}


class FmodAccessControls(unittest.TestCase):
    def test_probe_reaches_boundary_without_authentication(self):
        fixture = b"synthetic public website"
        hashes = {path: hashlib.sha256(fixture).hexdigest() for path in fmod.WEBSITE_ASSETS}
        client = Mock()
        client.request.side_effect = [(200, fixture), (200, fixture), (401, b"")]
        with patch.object(fmod, "WEBSITE_ASSETS", hashes):
            receipt = fmod.probe(client)
        self.assertEqual(receipt["status"], "CREDENTIALS_REQUIRED")
        self.assertFalse(receipt["authentication_attempted"])
        self.assertFalse(receipt["sdk_downloaded"])
        self.assertEqual([call.args for call in client.request.call_args_list],
                         [("/bundle.js",), ("/download.chunk.js",), ("/api-downloads",)])

    def test_website_change_stops_before_credential_prompt(self):
        client = Mock()
        client.request.return_value = (200, b"changed login implementation")
        with patch.object(fmod, "Client", return_value=client), \
                patch.object(fmod, "prompt_credentials") as prompt, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fmod.main(["check-account"]), 2)
        prompt.assert_not_called()
        self.assertEqual(client.request.call_count, 1)

    def test_nonterminal_cannot_echo_or_read_credentials(self):
        with patch.object(sys.stdin, "isatty", return_value=False), \
                patch.object(fmod.getpass, "getpass") as prompt:
            with self.assertRaisesRegex(fmod.AccessError, "Terminal"):
                fmod.prompt_credentials()
        prompt.assert_not_called()

    def test_getpass_echo_fallback_is_rejected(self):
        with patch.object(sys.stdin, "isatty", return_value=True), \
                patch.object(sys.stderr, "isatty", return_value=True), \
                patch.object(fmod.getpass, "getpass", side_effect=fmod.getpass.GetPassWarning):
            with self.assertRaisesRegex(fmod.AccessError, "Hidden credential entry"):
                fmod.prompt_credentials()

    def test_explicit_environment_credentials_are_removed_before_subprocesses(self):
        values = {"CABRILLO_FMOD_USERNAME": "synthetic-user", "CABRILLO_FMOD_PASSWORD": "synthetic-password"}
        with patch.dict(os.environ, values), patch.object(fmod, "prompt_credentials") as prompt:
            self.assertEqual(fmod.credentials(True), ("synthetic-user", "synthetic-password"))
            self.assertNotIn("CABRILLO_FMOD_USERNAME", os.environ)
            self.assertNotIn("CABRILLO_FMOD_PASSWORD", os.environ)
            prompt.assert_not_called()

    def test_partial_environment_credentials_fail_without_prompt_or_leak(self):
        with patch.dict(os.environ, {"CABRILLO_FMOD_USERNAME": "synthetic-user"}, clear=True), \
                patch.object(fmod, "prompt_credentials") as prompt:
            with self.assertRaises(fmod.AccessError) as result:
                fmod.credentials(True)
            self.assertNotIn("synthetic-user", str(result.exception))
            self.assertNotIn("CABRILLO_FMOD_USERNAME", os.environ)
            prompt.assert_not_called()

    def test_password_encoding_matches_website_with_unicode_and_delimiters(self):
        client = Mock()
        client.request.return_value = (200, b'{"token":"synthetic-session","user":123}')
        self.assertEqual(fmod.login(client, "TeST+Ü@example.invalid", "p:a ss/雪!").token, "synthetic-session")
        args = client.request.call_args.args
        self.assertEqual(args[0], "/api-login")
        self.assertEqual(args[2], b"null")
        self.assertEqual(base64.b64decode(args[1].split(" ", 1)[1]),
                         b"test%2B%C3%BC%40example.invalid:p%3Aa%20ss%2F%E9%9B%AA!")

    def test_account_failure_is_one_attempt_and_does_not_echo_server_body(self):
        client = Mock()
        client.request.return_value = (401, b'{"message":"synthetic-password-must-not-appear"}')
        with self.assertRaises(fmod.AccessError) as result:
            fmod.login(client, "fake@example.invalid", "synthetic-password-must-not-appear")
        self.assertNotIn("synthetic-password", str(result.exception))
        self.assertEqual(client.request.call_count, 1)

    def test_login_redirect_and_unsafe_token_are_rejected(self):
        for response in [{"redir": "https://example.invalid", "token": "synthetic"},
                         {"token": "injected\r\nheader"}, {"token": ""}, {"token": 7}]:
            with self.subTest(response=response):
                client = Mock()
                client.request.return_value = (200, json.dumps(response).encode())
                with self.assertRaises(fmod.AccessError):
                    fmod.login(client, "fake", "fake")

    def test_exact_sdk_selection_rejects_absence_duplicates_disabled_and_wrong_version(self):
        fmod.sdk_available(catalogue())
        absent = catalogue("fmodstudioapi20400ios-installer.dmg")
        duplicate = catalogue()
        products = duplicate["downloads"]["categories"][0]["products"]
        products.append(products[0].copy())
        wrong_version = catalogue()
        wrong_version["downloads"]["categories"][0]["products"][0]["versions"][0]["version"] = "2.04.00"
        for value in [absent, duplicate, catalogue(disabled=True), wrong_version, {"downloads": None}]:
            with self.subTest(value=value), self.assertRaises(fmod.AccessError):
                fmod.sdk_available(value)

    def test_success_closes_session_and_receipt_excludes_account_and_catalogue(self):
        client = Mock()
        client.request.side_effect = [(200, b'{"token":"private-synthetic-token","user":123}'),
            (200, json.dumps(catalogue()).encode()), (200, b"{}")]
        result = fmod.check_account(client, {"sdk_downloaded": False}, "fake@example.invalid", "fake-password")
        self.assertEqual(result["status"], "PINNED_SDK_LISTED")
        self.assertTrue(result["temporary_session_closed"])
        self.assertFalse(result["sdk_downloaded"])
        self.assertEqual(client.request.call_args.args, ("/api-logout", "FMOD private-synthetic-token"))
        for private in ["private-synthetic-token", "fake@example.invalid", "fake-password", "synthetic-ios-path"]:
            self.assertNotIn(private, json.dumps(result))

    def test_failed_catalogue_and_interrupt_still_close_session(self):
        for failure in [(401, b""), (200, b"not json"), KeyboardInterrupt()]:
            with self.subTest(failure=failure):
                client = Mock()
                client.request.side_effect = [(200, b'{"token":"synthetic-session","user":123}'), failure, (204, b"")]
                with self.assertRaises((fmod.AccessError, KeyboardInterrupt)):
                    fmod.check_account(client, {}, "fake", "fake")
                self.assertEqual(client.request.call_args.args, ("/api-logout", "FMOD synthetic-session"))

    def test_logout_failure_cannot_report_success(self):
        client = Mock()
        client.request.side_effect = [(200, b'{"token":"synthetic-session","user":123}'),
            (200, json.dumps(catalogue()).encode()), (500, b"")]
        with self.assertRaisesRegex(fmod.AccessError, "could not be closed"):
            fmod.check_account(client, {}, "fake", "fake")

    def test_client_refuses_unknown_endpoint_and_credentials_on_assets(self):
        client = fmod.Client()
        client.opener = Mock()
        for path, credential in [("https://example.invalid/steal", "secret"),
                                 ("/api-login?redirect=elsewhere", "secret"), ("/bundle.js", "secret")]:
            with self.subTest(path=path), self.assertRaises(fmod.AccessError):
                client.request(path, credential)
        client.opener.open.assert_not_called()

    def test_actual_http_redirect_does_not_forward_authorization(self):
        seen = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append(self.path)
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                self.send_response(302)
                self.send_header("Location", "/credential-trap")
                self.end_headers()

            def do_GET(self):
                seen.append(self.path)
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with patch.object(fmod, "ORIGIN", "http://127.0.0.1:" + str(server.server_port)), \
                        patch("urllib.request.getproxies", return_value={}):
                    with self.assertRaisesRegex(fmod.AccessError, "redirect"):
                        fmod.Client().request("/api-login", "Basic synthetic-test-credential", b"null")
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(seen, ["/api-login"])

    def test_error_response_body_is_not_read_and_network_details_are_not_exposed(self):
        client = fmod.Client()
        body = io.BytesIO(b"synthetic-secret")
        body.read = Mock(wraps=body.read)
        error = urllib.error.HTTPError(fmod.ORIGIN, 401, "synthetic-secret", {}, body)
        client.opener = Mock()
        client.opener.open.side_effect = error
        self.assertEqual(client.request("/api-login", "Basic synthetic-secret", b"null"), (401, b""))
        body.read.assert_not_called()
        client.opener.open.side_effect = urllib.error.URLError("synthetic-secret")
        with self.assertRaises(fmod.AccessError) as result:
            client.request("/api-downloads")
        self.assertNotIn("synthetic-secret", str(result.exception))

    def test_unexpected_exception_does_not_print_traceback_or_credentials(self):
        out = io.StringIO()
        with patch.object(fmod, "probe", side_effect=RuntimeError("synthetic-secret")), \
                contextlib.redirect_stderr(out):
            self.assertEqual(fmod.main(["probe"]), 2)
        self.assertNotIn("synthetic-secret", out.getvalue())
        self.assertNotIn("Traceback", out.getvalue())

    def test_reports_stay_in_ignored_directory(self):
        self.assertEqual(fmod.report_path(".build/fmod-access.json"), fmod.ROOT / ".build/fmod-access.json")
        for value in ["receipt.json", ".build/../public.json", "/tmp/outside.json"]:
            with self.subTest(value=value), self.assertRaises(fmod.AccessError):
                fmod.report_path(value)


if __name__ == "__main__":
    unittest.main()
