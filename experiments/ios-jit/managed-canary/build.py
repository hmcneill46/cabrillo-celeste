#!/usr/bin/env python3
"""Build the imported-DLL managed JIT canary. Device IPA has no code signature/profile."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import shutil
import struct
import subprocess
import zipfile

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
DEVELOPER = "/Applications/Xcode-26.6.app/Contents/Developer"
BUNDLE_ID = "io.github.hmcneill46.celeste.everest.jit.canary"
APP_VERSION = "0.2.2"
BUILD_NUMBER = "6"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_payload_members(members):
    """Debug symbols belong beside the IPA, never inside its installable app."""
    for name, data in members:
        if any(part.lower().endswith(".dsym") for part in PurePosixPath(name).parts):
            raise ValueError(f"Debug-symbol bundle in app payload: {name}")
        endian = {b"\xcf\xfa\xed\xfe": "<", b"\xce\xfa\xed\xfe": "<",
                  b"\xfe\xed\xfa\xcf": ">", b"\xfe\xed\xfa\xce": ">"}.get(data[:4])
        if endian and len(data) >= 16 and struct.unpack_from(endian + "I", data, 12)[0] == 10:
            raise ValueError(f"MH_DSYM debug-symbol file in app payload: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-id", default="managed-canary-20260911-06")
    parser.add_argument("--simulator", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,70}", args.build_id):
        parser.error("build-id must be lowercase letters/digits/hyphens")
    build_id = args.build_id + ("-simulator" if args.simulator else "")
    stage = ROOT / ".build/ios-jit/managed-canary" / build_id
    output = ROOT / "artifacts/ios-jit" / build_id
    stage.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DEVELOPER_DIR=DEVELOPER)
    env["CLANG_MODULE_CACHE_PATH"] = str(stage / "module-cache")
    commands = []

    def run(argv):
        commands.append(list(map(str, argv)))
        result = subprocess.run(argv, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with (stage / "build.log").open("a") as stream:
            stream.write("\n" + repr(argv) + "\n" + result.stdout)
        if result.returncode:
            raise RuntimeError(f"Command failed: {argv[0]}\n{result.stdout}")
        return result.stdout.strip()

    (stage / "build.log").write_text("")
    sdk_name = "iphonesimulator" if args.simulator else "iphoneos"
    sdk = run(["xcrun", "--sdk", sdk_name, "--show-sdk-path"])
    xcode = run(["xcodebuild", "-version"])
    sdk_version = run(["xcrun", "--sdk", sdk_name, "--show-sdk-version"])
    assert "Xcode 26.6" in xcode, xcode
    arch = platform.machine() if args.simulator else "arm64"
    target = f"{arch}-apple-ios26.0" + ("-simulator" if args.simulator else "")
    app = stage / "Payload/CelesteJITCanary.app"
    # Only this build's generated .app is replaced; no AOT/private input touched.
    if app.exists():
        shutil.rmtree(app)
    app.mkdir(parents=True)
    sources = sorted(p for p in SOURCE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    sources += list((SOURCE.parent / "native-probe/src").glob("VMRange*")) + [SOURCE.parent / "native-probe/scripts/make_icon.swift"]
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    build_info = {
        "build_id": build_id, "version": APP_VERSION, "build_number": BUILD_NUMBER, "protocol": "CJIT mailbox 1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "xcode": xcode, "sdk": sdk_name, "sdk_version": sdk_version, "target": target,
        "base_commit": run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "source_sha256": source_hashes,
        "script_template_sha256": digest(SOURCE / "scripts/celeste-jit-probe.js"),
        "device_jit_tested": False, "scope": "Custom Mono ARM64 JIT; imported DLL and Reflection.Emit. No game or hooks",
        "runtime_pin": json.loads((SOURCE / "runtime-pin.json").read_text()),
        "runtime_patch_sha256": digest(SOURCE / "runtime-alias.patch"),
        "aot_disabled": True, "interpreter_disabled": True, "bytes_per_arena": 4194304,
        "stikdebug_source_reference": "94bc9e8cf3b41f32f125f046abf33d913f4e1b2d",
        "livecontainer_source_reference": "3afa9eb9a53625e9b8bd8b932e5785fd716ad5ae",
        "default_route": "LiveContainer 1 probe -> LiveContainer 2 StikDebug; actual target PID",
    }
    (app / "BuildInfo.json").write_text(json.dumps(build_info, indent=2) + "\n")
    shutil.copy2(SOURCE / "scripts/celeste-jit-probe.js", app / "celeste-jit-probe.js")
    shutil.copy2(ROOT / "LICENSE", app / "REPOSITORY_LICENSE.txt")
    shutil.copy2(ROOT / "LICENSE", output / "REPOSITORY_LICENSE.txt")
    if (SOURCE / "THIRD_PARTY_NOTICES.md").exists():
        shutil.copy2(SOURCE / "THIRD_PARTY_NOTICES.md", app / "THIRD_PARTY_NOTICES.md")
    catalog = stage / "Assets.xcassets"
    icon = catalog / "AppIcon.appiconset"
    icon.mkdir(parents=True, exist_ok=True)
    (catalog / "Contents.json").write_text(json.dumps({"info": {"author": "xcode", "version": 1}}))
    (icon / "Contents.json").write_text(json.dumps({"images": [{"filename": "AppIcon.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}], "info": {"author": "xcode", "version": 1}}))
    run(["xcrun", "swift", str(SOURCE.parent / "native-probe/scripts/make_icon.swift"), str(icon / "AppIcon.png")])
    partial = stage / "asset-info.plist"
    run(["xcrun", "actool", str(catalog), "--compile", str(app), "--platform", sdk_name,
         "--minimum-deployment-target", "26.0", "--target-device", "iphone", "--target-device", "ipad",
         "--app-icon", "AppIcon", "--output-partial-info-plist", str(partial)])
    info = {
        "CFBundleDevelopmentRegion": "en", "CFBundleDisplayName": "Celeste JIT Canary",
        "CFBundleExecutable": "CelesteJITCanary", "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0", "CFBundleName": "CelesteJITCanary",
        "CFBundlePackageType": "APPL", "CFBundleShortVersionString": APP_VERSION, "CFBundleVersion": BUILD_NUMBER,
        "MinimumOSVersion": "26.0", "LSRequiresIPhoneOS": True, "UIDeviceFamily": [1, 2],
        "CFBundleSupportedPlatforms": ["iPhoneSimulator" if args.simulator else "iPhoneOS"],
        "UIRequiredDeviceCapabilities": ["arm64"] if not args.simulator else [],
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
        "UISupportedInterfaceOrientations~ipad": ["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"],
        "UILaunchScreen": {}, "UIFileSharingEnabled": True, "LSSupportsOpeningDocumentsInPlace": True,
        "LSApplicationQueriesSchemes": ["livecontainer2", "stikdebug", "stikjit"],
        "UIApplicationSceneManifest": {"UIApplicationSupportsMultipleScenes": False, "UISceneConfigurations": {
            "UIWindowSceneSessionRoleApplication": [{"UISceneConfigurationName": "Default", "UISceneDelegateClassName": "CJSceneDelegate"}]}},
    }
    info.update(plistlib.loads(partial.read_bytes()))
    (app / "Info.plist").write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY))
    (app / "PkgInfo").write_bytes(b"APPL????")
    executable = app / "CelesteJITCanary"
    objects = []
    for name in ("VMRange", "VMRangeDarwin"):
        obj = stage / (name + ".o")
        run(["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk,
             "-std=c11", "-O2", "-g", "-Wall", "-Wextra", "-Werror", "-c", str(SOURCE.parent / "native-probe/src" / (name + ".c")), "-o", str(obj)])
        objects.append(str(obj))
    # Compiling a source file and linking with -g in one clang invocation also
    # creates <executable>.dSYM beside the executable on this Apple toolchain.
    # Compile an object first so symbols are emitted only to the explicit path.
    main_object = stage / "main.o"
    compile_args = ["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk,
                    "-I" + str(SOURCE.parent / "native-probe/src"), "-fobjc-arc", "-O2", "-g", "-fno-omit-frame-pointer", "-Wall", "-Wextra", "-Werror",
                    "-Wno-deprecated-declarations", "-c", str(SOURCE / "src/main.m"), "-o", str(main_object)]
    run(compile_args)
    link_args = ["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk,
                 "-fobjc-arc", "-framework", "UIKit", "-framework", "Foundation", "-framework", "UniformTypeIdentifiers", "-Wl,-no_adhoc_codesign",
                 str(main_object), *objects, "-o", str(executable)]
    if not args.simulator:
        base = ROOT / ".build/ios-jit/managed-runtime"
        native = base / "pack-ios-8.0.28/runtimes/ios-arm64/native"
        runtime = base / "mono-build-ios"
        libraries = [runtime / "mono/mini/libmonosgen-2.0.a"]
        libraries += [runtime / ("mono/mini/libmono-component-" + name + ".a") for name in
                      ("marshal-ilgen-static", "debugger-stub-static", "hot_reload-stub-static", "diagnostics_tracing-stub-static")]
        libraries.append(native / "libSystem.Native.a")
        assert all(p.is_file() for p in libraries), libraries
        patch = json.loads((base / "runtime-patch-receipt.json").read_text())
        for name, hashes in patch["files"].items():
            assert digest(base / "runtime-v8.0.28" / name) == hashes["patched_sha256"]
        config = (runtime / "config.h").read_text()
        assert "#define DISABLE_INTERPRETER 1" in config and "#define DISABLE_AOT 1" in config
        assert "#define DISABLE_JIT 1" not in config
        nm = run(["xcrun", "nm", "-u", str(libraries[0])])
        assert "_cj_mono_code_alloc" in nm and "_cj_mono_writable" in nm and "_cj_mono_flush" in nm
        names = sorted(set(line[1:] for line in run(["xcrun", "nm", "-g", "-U", "-j", str(native / "libSystem.Native.a")]).splitlines() if re.fullmatch(r"_SystemNative_[A-Za-z0-9_]+", line)))
        assert len(names) > 100
        table = stage / "SystemNativeTable.c"
        table.write_text('#include <string.h>\n' + ''.join('extern void ' + name + '(void);\n' for name in names) +
                         'void *CJResolveSystemNative(const char *name) {\n' + ''.join('if (!strcmp(name, "' + name + '")) return (void *)&' + name + ';\n' for name in names) + 'return 0;\n}\n')
        for source_file in [SOURCE / "src/CJCodeArena.c", SOURCE / "src/CanaryNative.c", SOURCE / "src/CJNativeResolver.c", SOURCE / "src/CJMonoThread.c", SOURCE / "src/CJManaged.m", table]:
            obj = stage / (source_file.stem + ".o")
            options = ["-fobjc-arc", "-Wno-deprecated-declarations"] if source_file.suffix == ".m" else ["-std=c11"]
            run(["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk, "-O2", "-g", "-Wall", "-Wextra", "-Werror",
                 "-I" + str(SOURCE / "src"), "-I" + str(native / "include/mono-2.0"), *options, "-c", str(source_file), "-o", str(obj)])
            link_args.append(str(obj))
        link_args += list(map(str, libraries)) + ["-lc++", "-liconv", "-lz", "-framework", "Security", "-framework", "CoreFoundation"]
        managed = app / "Managed"; managed.mkdir()
        bcl = base / "pack-ios-8.0.28/runtimes/ios-arm64/lib/net8.0"
        for file in list(bcl.glob("*.dll")) + [native / "System.Private.CoreLib.dll"]:
            shutil.copy2(file, managed / file.name)
        for file in (base / "pack-ios-8.0.28").glob("*.TXT"): shutil.copy2(file, app / file.name)
        build_info["native_library_sha256"] = {str(file.relative_to(ROOT)): digest(file) for file in libraries}
        build_info["framework_assembly_sha256"] = {file.name: digest(file) for file in managed.glob("*.dll")}
        build_info["runtime_config_sha256"] = digest(runtime / "config.h")
        (app / "BuildInfo.json").write_text(json.dumps(build_info, indent=2) + "\n")
    run(link_args)
    dsym = output / "CelesteJITCanary.app.dSYM"
    run(["xcrun", "dsymutil", str(executable), "-o", str(dsym)])
    if not args.simulator:
        run(["xcrun", "strip", "-S", str(executable)])
    validate_payload_members((str(p.relative_to(app)), p.read_bytes()) for p in app.rglob("*") if p.is_file())
    load_commands = run(["xcrun", "otool", "-l", str(executable)])
    assert "LC_CODE_SIGNATURE" not in load_commands, "Unexpected executable signature"
    assert not (app / "embedded.mobileprovision").exists()
    assert not (app / "_CodeSignature").exists()
    (output / "macho-load-commands.txt").write_text(load_commands + "\n")
    if args.simulator:
        run(["codesign", "--force", "--sign", "-", str(app)])
        deliverable = output / "CelesteJITCanary.app"
        if deliverable.exists():
            shutil.rmtree(deliverable)
        shutil.copytree(app, deliverable)
    else:
        deliverable = output / "CelesteJITCanary-unsigned.ipa"
        with zipfile.ZipFile(deliverable, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(app.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(stage))
        with zipfile.ZipFile(deliverable) as archive:
            assert archive.testzip() is None
            assert archive.read("Payload/CelesteJITCanary.app/CelesteJITCanary") == executable.read_bytes()
            validate_payload_members((name, archive.read(name)) for name in archive.namelist())
    shutil.copy2(SOURCE / "scripts/celeste-jit-probe.js", output / "celeste-jit-probe-TEMPLATE.js")
    for name in ("INSTALL.md", "THIRD_PARTY_NOTICES.md"):
        if (SOURCE / name).exists():
            shutil.copy2(SOURCE / name, output / name)
    if (SOURCE / "PHONE_README.txt").exists():
        shutil.copy2(SOURCE / "PHONE_README.txt", output / "README-FIRST.txt")
    receipt = dict(build_info, simulator=args.simulator,
                   unsigned_device_executable=not args.simulator,
                   executable_sha256=digest(executable),
                   executable_uuid=run(["xcrun", "dwarfdump", "--uuid", str(executable)]).split(" (")[0],
                   compile_command=compile_args, link_command=link_args, build_commands=commands,
                   debug_symbols_outside_app=True,
                   deliverable=str(deliverable.relative_to(ROOT)))
    if not args.simulator:
        receipt["ipa_sha256"] = digest(deliverable)
    (output / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    shutil.copy2(stage / "build.log", output / "build.log")
    files = sorted(p for p in output.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    (output / "SHA256SUMS.txt").write_text("".join(f"{digest(p)}  {p.relative_to(output)}\n" for p in files))
    print(json.dumps({"deliverable": str(deliverable), "receipt": str(output / "build-receipt.json"),
                      "device_execution": "NOT TESTED", "unsigned_device_ipa": not args.simulator}, indent=2))


if __name__ == "__main__":
    main()
