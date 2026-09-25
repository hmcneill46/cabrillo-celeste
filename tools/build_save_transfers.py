#!/usr/bin/env python3
"""Build save transfers with the pinned, scoped precision repair of build32.

This issues fresh metadata and linker/dSYM identities. The runtime and native
renderer and all managed assemblies remain pinned; only the native launcher changes.
"""
import argparse
import datetime
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import zipfile
from save_transfer_inputs import validate_managed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/ios-jit/launcher-save-transfers"
DEVELOPER = "/Applications/Xcode-26.6.app/Contents/Developer"
XCODE = "Xcode 26.6\nBuild version 17F113"
TARGET = "arm64-apple-ios26.0"
APP_NAME = "CelesteJITEverest"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def local_path(name, root=ROOT):
    """Reject traversal and symlink aliases, including aliases within Cabrillo."""
    path = root / name
    resolved = path.resolve()
    if root not in resolved.parents or resolved != path.absolute():
        raise ValueError("Expected an unaliased path inside Cabrillo: " + str(name))
    return resolved


def fresh_output(name, category, root=ROOT):
    path = local_path(name, root)
    if root / category not in path.parents or path.exists():
        raise ValueError(f"Choose a new directory under {category}: {name}")
    return path


def load_inputs(managed_receipt):
    managed, overlay = validate_managed(managed_receipt)
    payload = read_json(SOURCE / "ManagedPayload.json")
    if sha(local_path(managed_receipt)) != payload["receipt_sha256"] or managed["resources"] != payload["resources"]:
        raise ValueError("Build34 requires its exact validated save/precision managed payload")
    identity = read_json(SOURCE / "BuildIdentity.json")
    settings = plistlib.loads((SOURCE / "Info.plist").read_bytes())
    if (int(identity["build_number"]) <= 33 or identity["version"] == "0.15.0"
            or identity["build_id"] == "launcher-catalogue-20260913-28"):
        raise ValueError("Changed source requires a new version/build identity")
    if (settings["CFBundleVersion"] != identity["build_number"]
            or settings["CFBundleShortVersionString"] != identity["version"]
            or settings["CFBundleDisplayName"] != identity["product"]
            or settings["CFBundleIdentifier"] != "io.github.hmcneill46.celeste.everest.jit.everest"
            or settings["CFBundleExecutable"] != APP_NAME):
        raise ValueError("Build metadata or existing guest identity differs")
    lock = read_json(SOURCE / "Dependencies.json")
    manifest = local_path(lock["capsule_manifest"])
    if sha(manifest) != lock["capsule_manifest_sha256"]:
        raise ValueError("Private capsule lock changed")
    capsule = read_json(manifest)
    for name, row in capsule.items():
        path = local_path(name)
        if ROOT / ".private" not in path.parents or sha(path) != row["sha256"]:
            raise ValueError("Changed or missing private dependency: " + name)
    for name, digest in lock["shared_source_sha256"].items():
        if sha(local_path(name)) != digest:
            raise ValueError("Changed shared/vendor input: " + name)
    for row in lock["native_libraries"]:
        if capsule[row["path"]]["sha256"] != row["sha256"]:
            raise ValueError("Native library not pinned by capsule: " + row["path"])
    resources = local_path(lock["resource_root"])
    actual_resources = {str(p.relative_to(ROOT)) for p in resources.rglob("*") if p.is_file()}
    expected_resources = {n for n in capsule if n.startswith(lock["resource_root"] + "/")}
    if actual_resources != expected_resources:
        raise ValueError("Unexpected or missing private resource")
    baseline = read_json(resources / "BuildInfo.json")
    if sha(resources / "BuildInfo.json") != lock["baseline_build_info_sha256"]:
        raise ValueError("Changed baseline dependency provenance")
    runtime = read_json(SOURCE / "RuntimeIdentity.json")
    if runtime != baseline["bundled_runtime_identity"]:
        raise ValueError("Managed payload reuse cannot change its runtime identity")
    sources = [p for d in [SOURCE / "src", SOURCE / "native"] for p in d.rglob("*") if p.is_file()]
    sources += [SOURCE / n for n in ["BuildIdentity.json", "Dependencies.json", "ManagedPayload.json", "Info.plist",
        "RuntimeIdentity.json", "CompatibilityDownloads.json", "RuntimeCompatibleReleases.json", "THIRD_PARTY_NOTICES.md"]]
    sources += [Path(__file__), ROOT / "tools/verify_save_transfers.py", ROOT / "tools/loading_inputs.py", ROOT / "tools/save_transfer_inputs.py"]
    managed_sources = dict(managed.get("public_source_sha256", {}))
    if "base_receipt" in managed:
        managed_sources.update(read_json(local_path(managed["base_receipt"]))["public_source_sha256"])
        managed_sources.update(managed["source_sha256"])
    sources += [local_path(n) for n in managed_sources]
    sources += [local_path(n) for n in lock["shared_source_sha256"]]
    for path in sources:
        local_path(path)
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(sources))}
    return identity, settings, lock, baseline, hashes, managed, overlay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-inputs", action="store_true", help="Verify dependencies and identity without creating output")
    parser.add_argument("--work", default=".build/save-transfers-build34")
    parser.add_argument("--managed", required=True, help="Explicit loading managed receipt inside Cabrillo")
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--output", default="artifacts/cabrillo-build34")
    args = parser.parse_args()
    identity, settings, lock, baseline, source_hashes, managed, overlay = load_inputs(args.managed)
    if args.check_inputs:
        print(json.dumps(dict(status="PASS_LOADING_INPUTS", build=identity,
                              source_files=len(source_hashes), native_libraries=len(lock["native_libraries"])), indent=2))
        return
    work = fresh_output(args.work, ".build")
    output = fresh_output(args.output, "artifacts")
    env = dict(os.environ, DEVELOPER_DIR=DEVELOPER,
               CLANG_MODULE_CACHE_PATH=str(work / "module-cache"),
               SWIFT_MODULECACHE_PATH=str(work / "module-cache"))
    if subprocess.check_output(["xcodebuild", "-version"], env=env, text=True).strip() != XCODE:
        raise RuntimeError("Use the pinned Xcode 26.6 / 17F113")
    sdk = subprocess.check_output(["xcrun", "--sdk", "iphoneos", "--show-sdk-path"], env=env, text=True).strip()
    sdk_version = subprocess.check_output(["xcrun", "--sdk", "iphoneos", "--show-sdk-version"], env=env, text=True).strip()
    if sdk_version != "26.5":
        raise RuntimeError("Expected iPhoneOS SDK 26.5")
    created = datetime.datetime.now(datetime.timezone.utc).isoformat()
    work.mkdir(parents=True)
    output.mkdir(parents=True)
    native, stage = work / "native", work / "stage"
    native.mkdir()
    stage.mkdir()
    commands, compiled = [], []

    def run(command):
        command = list(map(str, command))
        commands.append(command)
        with (output / "build.log").open("a") as log:
            log.write(repr(command) + "\n")
            log.flush()
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError("Command failed; see " + str(output / "build.log"))

    swift_flags = ["-swift-version", "5", "-O", "-g", "-target", TARGET, "-sdk", sdk,
                   "-module-cache-path", work / "module-cache"]
    zip_sources = sorted((ROOT / "vendor/ZIPFoundation/Sources/ZIPFoundation").glob("*.swift"))
    run(["xcrun", "swiftc", *swift_flags, "-module-name", "ZIPFoundation", "-emit-library", "-static",
         "-emit-module", "-emit-module-path", native / "ZIPFoundation.swiftmodule", "-o", native / "libZIPFoundation.a", *zip_sources])
    compiled.extend(zip_sources)
    yaml = ROOT / "vendor/Yams/Sources/CYaml"
    yaml_objects = []
    for source in sorted((yaml / "src").glob("*.c")):
        obj = native / (source.stem + ".o")
        run(["xcrun", "clang", "-target", TARGET, "-isysroot", sdk, "-DYAML_DECLARE_STATIC", "-O2", "-g",
             "-I" + str(yaml / "include"), "-c", source, "-o", obj])
        yaml_objects.append(obj)
        compiled.append(source)
    run(["xcrun", "libtool", "-static", "-o", native / "libCYaml.a", *yaml_objects])
    swift_sources = sorted((SOURCE / "native").glob("*.swift"))
    run(["xcrun", "swiftc", *swift_flags, "-module-name", "CJLauncher", "-I", native, "-I", yaml / "include",
         "-emit-library", "-static", "-emit-module", "-emit-module-path", native / "CJLauncher.swiftmodule",
         "-emit-objc-header-path", native / "CJLauncher-Swift.h", "-o", native / "libCJLauncher.a", *swift_sources])
    compiled.extend(swift_sources)
    libraries = [local_path(r["path"]) for r in lock["native_libraries"]]

    def make_table(name, resolver, paths, pattern, minimum):
        names = set()
        for path in paths:
            symbols = subprocess.check_output(["xcrun", "nm", "-g", "-U", "-j", str(path)], env=env, text=True)
            names.update(line[1:] for line in symbols.splitlines() if re.fullmatch(pattern, line))
        if len(names) < minimum:
            raise RuntimeError("Incomplete symbol table: " + name)
        names = sorted(names)
        source = stage / name
        source.write_text('#include <string.h>\n' + ''.join('extern void ' + n + '(void);\n' for n in names)
            + 'void *' + resolver + '(const char *name) {\n'
            + ''.join('if (!strcmp(name,"' + n + '")) return (void *)&' + n + ';\n' for n in names) + 'return 0;\n}\n')
        return source

    tables = [make_table("SystemNativeTable.c", "CJResolveSystemNative", [p for p in libraries if p.name.startswith("libSystem.")],
                        r"_(SystemNative_|CompressionNative_|AppleCryptoNative_)[A-Za-z0-9_]+", 100),
              make_table("FNAStaticTable.c", "CJResolveFNAStatic", libraries,
                        r"_(FMOD_[A-Za-z0-9_]+|SDL_[A-Za-z0-9_]+|FNA3D_[A-Za-z0-9_]+|FAudio[A-Za-z0-9_]*|F3DAudio[A-Za-z0-9_]*|FACT[A-Za-z0-9_]*|FAPO[A-Za-z0-9_]*|XNA_[A-Za-z0-9_]+|stb_vorbis_[A-Za-z0-9_]+|tf_[A-Za-z0-9_]+|luaL?_[A-Za-z0-9_]+|luaopen_[A-Za-z0-9_]+)", 500)]
    includes = [SOURCE / "src", native, ROOT / "experiments/ios-jit/managed-canary/src"]
    includes += [local_path(n) for n in lock["include_directories"]]
    native_sources = sorted(p for p in (SOURCE / "src").iterdir() if p.suffix in {".c", ".m"})
    native_sources += [ROOT / "experiments/ios-jit/managed-canary/src" / n for n in ["CanaryNative.c", "CJNativeResolver.c", "CJMonoThread.c"]]
    native_sources += tables
    objects = []
    for source in native_sources:
        obj = stage / (source.stem + ".o")
        run(["xcrun", "clang", "-target", TARGET, "-isysroot", sdk, "-O2", "-g", "-Wall", "-Wextra", "-Werror",
             "-Wno-deprecated-declarations", *(["-fobjc-arc"] if source.suffix == ".m" else []),
             *(["-std=c11"] if source.suffix == ".c" else []),
             *(["-fno-omit-frame-pointer"] if source.name == "main.m" else []),
             *("-I" + str(p) for p in includes), "-c", source, "-o", obj])
        objects.append(obj)
        compiled.append(source)
    if any(str(p.relative_to(ROOT)) not in source_hashes for p in compiled if p not in tables):
        raise RuntimeError("Compilation consumed an unrecorded source")
    native_receipt = dict(status="PASS_FRESH_NATIVE_COMPILATION", created_utc=created, xcode=XCODE,
        target=TARGET, source_sha256=source_hashes, generated_sources={p.name: sha(p) for p in tables},
        compiled_source_count=len(compiled), library_sha256={p.name: sha(p) for p in native.glob("*.a")},
        reused_native_libraries=lock["native_libraries"], commands=list(commands))
    write_json(output / "native-receipt.json", native_receipt)
    if args.compile_only:
        print("PASS_LOADING_NATIVE_COMPILATION"); return
    shutil.copyfile(local_path(args.managed), output / "managed-receipt.json")
    shutil.copyfile(local_path(args.managed).parent / "repair.json", output / "repair.json")
    app = stage / "Payload" / (APP_NAME + ".app")
    shutil.copytree(overlay, app, copy_function=shutil.copyfile,
                    ignore=shutil.ignore_patterns("BuildInfo.json"))
    for name in ["RuntimeIdentity.json", "CompatibilityDownloads.json", "RuntimeCompatibleReleases.json", "THIRD_PARTY_NOTICES.md"]:
        shutil.copyfile(SOURCE / name, app / name)
    assets = stage / "Assets.xcassets"
    icon = assets / "AppIcon.appiconset"
    icon.mkdir(parents=True)
    write_json(assets / "Contents.json", {"info": {"author": "xcode", "version": 1}})
    write_json(icon / "Contents.json", {"images": [{"filename": "AppIcon.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}], "info": {"author": "xcode", "version": 1}})
    run(["xcrun", "swift", ROOT / "experiments/ios-jit/native-probe/scripts/make_icon.swift", icon / "AppIcon.png"])
    run(["xcrun", "actool", assets, "--compile", app, "--platform", "iphoneos", "--minimum-deployment-target", "26.0",
         "--target-device", "iphone", "--target-device", "ipad", "--app-icon", "AppIcon", "--output-partial-info-plist", stage / "asset-info.plist"])
    settings.update(plistlib.loads((stage / "asset-info.plist").read_bytes()))
    (app / "Info.plist").write_bytes(plistlib.dumps(settings, fmt=plistlib.FMT_BINARY))
    # Only stable runtime/content contracts are inherited. Build/source/native
    # receipts, dates, executable identities and acceptance never come from 28.
    inherited = ["protocol", "compiled_protocol", "bytes_per_arena", "runtime_pin", "monomod_pin",
                 "bundled_runtime_identity", "bundled_runtime_identity_sha256", "reflection_flags",
                 "game_content_aggregate_sha256", "game_content_bytes", "mod_download_manifest",
                 "aot_disabled", "interpreter_disabled", "private_prepared_game_il", "ios_support"]
    info = {key: baseline[key] for key in inherited}
    info.update(identity, created_utc=created, xcode=XCODE, sdk="iphoneos", sdk_version=sdk_version,
        target=TARGET, base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        working_tree_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        source_sha256=source_hashes, launcher_native_receipt_sha256=sha(output / "native-receipt.json"),
        managed_build_receipt_sha256=sha(output / "managed-receipt.json"),
        loading=dict(abi=1, scheduler="main CADisplayLink", ready_gate="first_draw_and_post_present_readback", passive_game_startup=True, non_preemptible_steps=True),
        precision_repair=dict(schema=1, original_float_sites=10, lava_float_setters=2, lava_double_constants=1, preserved_double_sites=10, changed_method_bodies=4),
        save_transfers=dict(schema=1, unchanged_file_contents=True, vanilla_slots=3, staged_profile_swap=True, retained_rollback=True, main_only_mod_choice=True),
        profile_backups=dict(schema=1, exact_restore=True, retained_rollback=True, fresh_process_required=True, arbitrary_save_slots=True, mod_archives_included=False),
        script_template_sha256=sha(app / "celeste-jit-probe.js"),
        compatibility_downloads_sha256=sha(app / "CompatibilityDownloads.json"),
        runtime_compatible_releases_sha256=sha(app / "RuntimeCompatibleReleases.json"),
        game_content_manifest_sha256=sha(app / "GameContentManifest.json"),
        game_fixture_sha256=sha(app / "Managed/CelesteJITEverest.dll"),
        reused_dependencies=dict(baseline_build_id=baseline["build_id"], baseline_build_info_sha256=lock["baseline_build_info_sha256"],
            capsule_manifest_sha256=lock["capsule_manifest_sha256"], managed_rebuilt=True, native_runtime_rebuilt=False,
            managed_sha256={str(p.relative_to(app / "Managed")): sha(p) for p in sorted((app / "Managed").rglob("*")) if p.is_file()}))
    write_json(app / "BuildInfo.json", info)
    executable = app / APP_NAME
    frameworks = ["UIKit", "Foundation", "UniformTypeIdentifiers", "QuartzCore", "AVFoundation", "AudioToolbox",
                  "CoreBluetooth", "CoreGraphics", "CoreHaptics", "CoreMotion", "CoreVideo", "GameController", "Metal",
                  "OpenGLES", "Security", "CoreFoundation"]
    run(["xcrun", "swiftc", "-target", TARGET, "-sdk", sdk, "-Xlinker", "-no_adhoc_codesign", *objects,
         native / "libCJLauncher.a", native / "libZIPFoundation.a", native / "libCYaml.a", *libraries,
         *(arg for framework in frameworks for arg in ["-framework", framework]), "-lc++", "-liconv", "-lz", "-o", executable])
    run(["xcrun", "dsymutil", executable, "-o", output / (APP_NAME + ".app.dSYM")])
    run(["xcrun", "strip", "-S", executable])
    # Reject mid-build edits before producing a distributable-looking archive.
    for name, digest in source_hashes.items():
        if sha(local_path(name)) != digest:
            raise RuntimeError("Source changed during build: " + name)
    validate_managed(args.managed)
    ipa = output / f"Cabrillo-{identity['version']}-build-{identity['build_number']}-unsigned.ipa"
    with zipfile.ZipFile(ipa, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                archive.write(path, str(path.relative_to(stage)))
    receipt = dict(status="BUILD_COMPLETE_AWAITING_PACKAGE_VERIFICATION", build=identity,
        actual_created_utc=created, completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ipa=ipa.name, ipa_sha256=sha(ipa), bytes=ipa.stat().st_size, executable_sha256=sha(executable),
        source_sha256=source_hashes, app_files={str(p.relative_to(app)): sha(p) for p in sorted(app.rglob("*")) if p.is_file()},
        compiled_source_count=len(compiled), native_receipt_sha256=sha(output / "native-receipt.json"),
        managed_receipt_sha256=sha(output / "managed-receipt.json"),
        commands=commands, historical_uuid_restoration=False, historical_package_metadata_replayed=False,
        original_executable_copied=False, managed_rebuilt=True, device_tested=False)
    write_json(output / "build-receipt.json", receipt)
    from verify_save_transfers import verify
    verified = verify(output)
    write_json(output / "verification.json", verified)
    print(json.dumps(verified, indent=2))


if __name__ == "__main__":
    main()
