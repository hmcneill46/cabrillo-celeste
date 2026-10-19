#!/usr/bin/env python3
"""Exercise real Apple ZIP picker/delegate/staging in a simulator-only build53 fixture.

The simulator cannot reproduce iOS provisioning-profile enforcement. Its receipt
only claims normal picker compatibility, hook availability/status, exact staged
bytes, cancellation, repeated selection, and preservation of synthetic source.
"""
import argparse
import hashlib
import json
import os
import platform
import plistlib
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/ios-jit/launcher-signing-picker"
BASE = ROOT / "experiments/ios-jit/launcher-owned-game/src"
BUNDLE = "io.github.hmcneill46.cabrillo.signingpicker.preview"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--developer-dir", type=Path)
    args = parser.parse_args()
    work = ROOT / args.work
    if work.resolve() != work.absolute() or ROOT / ".build" not in work.parents or work.exists():
        raise ValueError("Use a fresh directory below this checkout's .build")
    work.mkdir(parents=True)
    developer = args.developer_dir or Path(subprocess.check_output(["xcode-select", "-p"], text=True).strip())
    env = dict(os.environ, DEVELOPER_DIR=str(developer), CLANG_MODULE_CACHE_PATH=str(work / "module-cache"))
    commands = []

    def run(command, label, timeout=600):
        command = list(map(str, command))
        commands.append(command)
        with (work / (label + ".log")).open("w") as log:
            result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        output = (work / (label + ".log")).read_text()
        if result.returncode:
            raise RuntimeError(label + " failed: " + output[-4000:])
        return output.strip()

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    version = run(["xcodebuild", "-version"], "xcode-version")
    if not version.startswith("Xcode 26.6\n"):
        raise ValueError("Use the documented Xcode 26.6")
    sdk = run(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"], "sdk")
    arch = platform.machine()
    if arch not in ("x86_64", "arm64"):
        raise ValueError("Unsupported simulator host architecture")
    app = work / "PickerPreview.app"
    app.mkdir()
    settings = dict(CFBundleIdentifier=BUNDLE, CFBundleDisplayName="Picker53 Fixture", CFBundleName="PickerPreview",
                    CFBundleExecutable="PickerPreview", CFBundlePackageType="APPL", CFBundleVersion="53",
                    CFBundleShortVersionString="1.0", MinimumOSVersion="26.0", UIDeviceFamily=[1, 2],
                    LSRequiresIPhoneOS=True, UILaunchScreen={}, UIFileSharingEnabled=True,
                    LSSupportsOpeningDocumentsInPlace=True,
                    UISupportedInterfaceOrientations=["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"])
    (app / "Info.plist").write_bytes(plistlib.dumps(settings))
    with zipfile.ZipFile(app / "synthetic.zip", "w", compression=zipfile.ZIP_STORED) as archive:
        item = zipfile.ZipInfo("README.txt", date_time=(2026, 10, 19, 0, 0, 0))
        archive.writestr(item, b"Synthetic public build53 document picker fixture; no game data.\n")
    sources = [SOURCE / "tests/PickerPreview.m", SOURCE / "src/CJDocumentPickerCompatibility.m",
               BASE / "CJContentImport.m", BASE / "CJLoadingState.m"]
    inputs = sources + [SOURCE / "src/CJDocumentPickerCompatibility.h", BASE / "CJContentImport.h", BASE / "CJLoadingState.h",
                       SOURCE / "tests/PickerUITests.swift", SOURCE / "tests/PickerUITests.pbxproj.template",
                       SOURCE / "tests/PickerUITests.xcscheme", Path(__file__).resolve()]
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    run(["xcrun", "--sdk", "iphonesimulator", "clang", "-fobjc-arc", "-fblocks", "-g",
         "-target", arch + "-apple-ios26.0-simulator", "-isysroot", sdk, "-DCJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING=1",
         "-I", BASE, "-I", SOURCE / "src", *sources,
         "-framework", "Foundation", "-framework", "UIKit", "-framework", "UniformTypeIdentifiers", "-framework", "Security",
         "-o", app / "PickerPreview"], "preview-build")
    run(["codesign", "--force", "--sign", "-", app], "sign")
    devices = json.loads(run(["xcrun", "simctl", "list", "devices", "available", "--json"], "devices"))
    selected = [device for group in devices["devices"].values() for device in group if device["udid"] == args.device]
    if len(selected) != 1:
        raise ValueError("Select one available iOS simulator")
    booted_here = selected[0]["state"] != "Booted"
    try:
        if booted_here:
            run(["xcrun", "simctl", "boot", args.device], "boot")
        run(["xcrun", "simctl", "bootstatus", args.device, "-b"], "boot-status")
        run(["xcrun", "simctl", "install", args.device, app], "install")
        project = work / "Picker.xcodeproj"
        project.mkdir()
        (project / "project.pbxproj").write_text((SOURCE / "tests/PickerUITests.pbxproj.template").read_text().replace("SOURCE_PATH", str(SOURCE / "tests/PickerUITests.swift")))
        schemes = project / "xcshareddata/xcschemes"
        schemes.mkdir(parents=True)
        (schemes / "PickerUITests.xcscheme").write_bytes((SOURCE / "tests/PickerUITests.xcscheme").read_bytes())
        result = work / "UITests.xcresult"
        output = run(["xcodebuild", "test", "-project", project, "-scheme", "PickerUITests", "-destination", "platform=iOS Simulator,id=" + args.device,
                      "-derivedDataPath", work / "DerivedData", "-parallel-testing-enabled", "NO", "-maximum-concurrent-test-simulator-destinations", "1",
                      "-resultBundlePath", result, "-test-timeouts-enabled", "YES", "-default-test-execution-time-allowance", "120",
                      "-maximum-test-execution-time-allowance", "180"], "uitests")
        for sentinel in ("PASS_ORIGINAL_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT", "PASS_COMPATIBILITY_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT"):
            if sentinel not in output:
                raise ValueError("Missing actual UI pass: " + sentinel)
        run(["xcrun", "xcresulttool", "export", "attachments", "--path", result, "--output-path", work / "screenshots"], "screenshots")
        container = Path(run(["xcrun", "simctl", "get_app_container", args.device, BUNDLE, "data"], "container"))
        outcomes = {}
        for mode in ("original", "compatibility"):
            raw = (container / "Documents" / ("UIResult-" + mode + ".json")).read_bytes()
            (work / ("UIResult-" + mode + ".json")).write_bytes(raw)
            outcome = json.loads(raw)
            assert outcome["mode"] == mode and outcome["selections"] == 2 and outcome["cancellations"] == 1, outcome
            assert outcome["staged"] and outcome["source_preserved"], outcome
            assert outcome["source_sha256"] == outcome["staged_sha256"] == sha(app / "synthetic.zip"), outcome
            assert outcome["staged_bytes"] == (app / "synthetic.zip").stat().st_size, outcome
            if mode == "compatibility":
                assert outcome["compatibility_status"]["installed"] and outcome["synthetic_requested_host_rewritten"], outcome
                assert outcome["first_prepare_status"]["installed"] and outcome["picker_constructions_before_first_prepare"] == 0, outcome
            outcomes[mode] = outcome
        assert hashes == {str(path.relative_to(ROOT)): sha(path) for path in inputs}, "UI inputs changed during test"
        receipt = dict(status="PASS_SIGNING_PICKER_REAL_APPLE_UI", device=selected[0], xcode=version,
                       source_sha256=hashes, synthetic_zip_sha256=sha(app / "synthetic.zip"), outcomes=outcomes,
                       real_document_picker_and_delegate=True, real_production_archive_staging=True,
                       actual_apple_configuration_hook_tested=True, synthetic_identity_test_seam=True,
                       hook_installed_before_first_picker_initialization=True,
                       production_device_build_has_no_test_seam=True,
                       physical_signing_mismatch_reproduced=False, physical_device_tested=False,
                       game_or_jit_tested=False, simulator_booted_here=booted_here,
                       limitations="Simulator validates picker/staging compatibility; physical provisioning-profile enforcement and the owner's unchanged-ID install still need a phone test.",
                       log_sha256=sha(work / "uitests.log"), commands=commands)
        (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(receipt["status"])
    finally:
        if booted_here:
            run(["xcrun", "simctl", "shutdown", args.device], "shutdown")


if __name__ == "__main__":
    main()
