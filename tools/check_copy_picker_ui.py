#!/usr/bin/env python3
"""Exercise build54 copy picker and original open control using real Apple UI.

The simulator cannot reproduce iOS provisioning-profile enforcement. Its receipt
only claims observed controller modes, local-copy URL relationships, exact staged
bytes, cancellation, repeated selection, and preservation of synthetic source.
"""
import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/ios-jit/launcher-copy-picker"
ORIGINAL = ROOT / "experiments/ios-jit/launcher-signing-picker"
BASE = ROOT / "experiments/ios-jit/launcher-owned-game/src"
BUNDLE = "io.github.hmcneill46.cabrillo.copypicker.preview"


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

    def picker_arguments(path, selector):
        source = path.read_text()
        opening = re.search(r"(?m)^- \(void\)" + selector + r"\s*\{", source)
        if not opening:
            raise ValueError("Missing picker action " + selector)
        rest = source[opening.end():]
        following = re.search(r"(?m)^- \(", rest)
        body = rest[:following.start()] if following else rest
        constructor = re.search(r"initForOpeningContentTypes:\s*@\[\s*(UTType\w+)\s*\]\s*asCopy:\s*(YES|NO)", body)
        multiple = re.search(r"allowsMultipleSelection\s*=\s*(YES|NO)", body)
        if not constructor or not multiple:
            raise ValueError("Unrecognized picker arguments in " + selector)
        return dict(content_type=constructor.group(1), as_copy=constructor.group(2) == "YES", allows_multiple_selection=multiple.group(1) == "YES")

    source_arguments = {}
    for selector, multiple in (("importContent", False), ("importDLL", True)):
        current = picker_arguments(SOURCE / "src/main.m", selector)
        original = picker_arguments(ORIGINAL / "src/main.m", selector)
        assert current == dict(content_type="UTTypeItem", as_copy=True, allows_multiple_selection=multiple), current
        assert original == dict(content_type="UTTypeItem", as_copy=False, allows_multiple_selection=multiple), original
        source_arguments[selector] = dict(build54=current, control53=original)
    for name in ("CJDocumentPickerCompatibility.h", "CJDocumentPickerCompatibility.m"):
        assert (SOURCE / "src" / name).read_bytes() == (ORIGINAL / "src" / name).read_bytes(), "Compatibility helper must stay53-identical"
    version = run(["xcodebuild", "-version"], "xcode-version")
    if not version.startswith("Xcode 26.6\n"):
        raise ValueError("Use the documented Xcode 26.6")
    sdk = run(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"], "sdk")
    arch = platform.machine()
    if arch not in ("x86_64", "arm64"):
        raise ValueError("Unsupported simulator host architecture")
    app = work / "PickerPreview.app"
    app.mkdir()
    settings = dict(CFBundleIdentifier=BUNDLE, CFBundleDisplayName="Picker54 Fixture", CFBundleName="PickerPreview",
                    CFBundleExecutable="PickerPreview", CFBundlePackageType="APPL", CFBundleVersion="54",
                    CFBundleShortVersionString="1.0", MinimumOSVersion="26.0", UIDeviceFamily=[1, 2],
                    LSRequiresIPhoneOS=True, UILaunchScreen={}, UIFileSharingEnabled=True,
                    LSSupportsOpeningDocumentsInPlace=True,
                    UISupportedInterfaceOrientations=["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"])
    (app / "Info.plist").write_bytes(plistlib.dumps(settings))
    with zipfile.ZipFile(app / "synthetic.zip", "w", compression=zipfile.ZIP_STORED) as archive:
        item = zipfile.ZipInfo("README.txt", date_time=(2026, 10, 19, 0, 0, 0))
        archive.writestr(item, b"Synthetic public build54 document picker fixture; no game data.\n")
    sources = [SOURCE / "tests/PickerPreview.m", SOURCE / "src/CJDocumentPickerCompatibility.m",
               BASE / "CJContentImport.m", BASE / "CJLoadingState.m"]
    inputs = sources + [SOURCE / "src/CJDocumentPickerCompatibility.h", BASE / "CJContentImport.h", BASE / "CJLoadingState.h",
                       SOURCE / "tests/PickerUITests.swift", SOURCE / "tests/PickerUITests.pbxproj.template",
                       SOURCE / "tests/PickerUITests.xcscheme", SOURCE / "src/main.m", ORIGINAL / "src/main.m",
                       ORIGINAL / "src/CJDocumentPickerCompatibility.h", ORIGINAL / "src/CJDocumentPickerCompatibility.m", Path(__file__).resolve()]
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    run(["xcrun", "--sdk", "iphonesimulator", "clang", "-fobjc-arc", "-fblocks", "-g",
         "-target", arch + "-apple-ios26.0-simulator", "-isysroot", sdk,
         "-I", BASE, "-I", SOURCE / "src", *sources,
         "-framework", "Foundation", "-framework", "UIKit", "-framework", "UniformTypeIdentifiers", "-framework", "Security",
         "-o", app / "PickerPreview"], "preview-build")
    symbols = run(["nm", "-g", app / "PickerPreview"], "fixture-symbols")
    assert "CJDocumentPickerCompatibilityTestEnvironment" not in symbols, "Fixture must use production identity acquisition"
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
        for sentinel in ("PASS_OPEN53_CONTROL_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT", "PASS_COPY54_REAL_APPLE_PICKER_STAGE_CANCEL_REPEAT"):
            if sentinel not in output:
                raise ValueError("Missing actual UI pass: " + sentinel)
        run(["xcrun", "xcresulttool", "export", "attachments", "--path", result, "--output-path", work / "screenshots"], "screenshots")
        container = Path(run(["xcrun", "simctl", "get_app_container", args.device, BUNDLE, "data"], "container"))
        outcomes = {}
        for mode in ("open-control53", "copy54"):
            raw = (container / "Documents" / ("UIResult-" + mode + ".json")).read_bytes()
            (work / ("UIResult-" + mode + ".json")).write_bytes(raw)
            outcome = json.loads(raw)
            assert outcome["mode"] == mode and outcome["selections"] == 2 and outcome["cancellations"] == 1, outcome
            assert outcome["staged"] and outcome["source_preserved"], outcome
            assert outcome["source_sha256"] == outcome["staged_sha256"] == sha(app / "synthetic.zip"), outcome
            assert outcome["staged_bytes"] == (app / "synthetic.zip").stat().st_size, outcome
            assert outcome["entitlement_test_seam"] is False and outcome["returned_copy_removed"] is False, outcome
            copy = mode == "copy54"
            assert outcome["requested_as_copy"] == copy and outcome["presentations"] == 3, outcome
            observations = outcome["picker_observations"]
            assert len(observations) == 3, outcome
            for observation in observations:
                assert observation["mode_matches_request"] and not observation["allows_multiple_selection"], observation
                assert observation["controller_mode"] == ("Import" if copy else "Open"), observation
            selections = outcome["selection_observations"]
            assert len(selections) == 2, outcome
            for selection in selections:
                assert selection["selected_url_is_file"] and selection["source_preserved"] and selection["staged"], selection
                assert selection["staged_sha256"] == sha(app / "synthetic.zip"), selection
                if copy:
                    assert not selection["selected_url_equals_original_source"], "Import mode must supply a distinct local copy"
            outcomes[mode] = outcome
        assert hashes == {str(path.relative_to(ROOT)): sha(path) for path in inputs}, "UI inputs changed during test"
        receipt = dict(status="PASS_COPY54_PICKER_REAL_APPLE_UI", device=selected[0], xcode=version,
                       source_sha256=hashes, synthetic_zip_sha256=sha(app / "synthetic.zip"), outcomes=outcomes,
                       real_document_picker_and_delegate=True, real_production_archive_staging=True,
                       production_picker_argument_comparison=source_arguments,
                       source_arguments_verified_before_compilation=True,
                       entitlement_test_seam=False,
                       local_copy_distinct_from_original_verified=True,
                       returned_url_cleanup_performed=False,
                       physical_signing_mismatch_reproduced=False, physical_device_tested=False,
                       game_or_jit_tested=False, simulator_booted_here=booted_here,
                       limitations="Both normal-identity simulator controls work; this does not reproduce the owner's iOS27 open-mode failure or prove the unchanged-ID physical54 fix.",
                       log_sha256=sha(work / "uitests.log"), commands=commands)
        (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(receipt["status"])
    finally:
        if booted_here:
            run(["xcrun", "simctl", "shutdown", args.device], "shutdown")


if __name__ == "__main__":
    main()
