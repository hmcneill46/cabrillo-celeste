#!/usr/bin/env python3
"""Build a private Celeste JIT baseline test. Owner content stays in ignored artifacts."""
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
import shlex
import struct
import subprocess
import zipfile

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
BASE = SOURCE.parent / "managed-canary"
HOOK = SOURCE.parent / "hook-canary"
NATIVE = ROOT / ".build/ios-jit/game-native-output"
FNA_MANAGED = ROOT / ".build/ios-jit/launcher-backbuffer-managed"
MODS = ROOT / ".build/ios-jit/sj-lobby-mods"
HOOK_RUNTIME = ROOT / ".build/ios-jit/hook-runtime"
DEVELOPER = "/Applications/Xcode-26.6.app/Contents/Developer"
BUNDLE_ID = "io.github.hmcneill46.celeste.everest.jit.everest"
APP_VERSION = "0.12.1"
BUILD_NUMBER = "24"


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


def read_compiled_protocol(binary):
    """Inspect constants used by the native request builder, not BuildInfo claims."""
    magic, _, _, _, count, command_bytes, _, _ = struct.unpack_from("<8I", binary)
    assert magic == 0xfeedfacf
    cursor = 32; records = []
    for _ in range(count):
        command, size = struct.unpack_from("<2I", binary, cursor)
        assert size >= 8 and cursor + size <= 32 + command_bytes <= len(binary)
        if command == 0x19:  # LC_SEGMENT_64
            sections = struct.unpack_from("<I", binary, cursor + 64)[0]
            assert 72 + sections * 80 <= size
            for i in range(sections):
                section, segment, _, length, offset = struct.unpack_from("<16s16sQQI", binary, cursor + 72 + i * 80)
                if section.rstrip(b"\0") == b"__cjprotocol":
                    assert segment.rstrip(b"\0") == b"__TEXT" and length == 48 and offset + length <= len(binary)
                    records.append(struct.unpack_from("<8s5Q", binary, offset))
        cursor += size
    assert cursor == 32 + command_bytes and len(records) == 1
    tag, version, length, mailbox, response, error = records[0]
    assert tag == b"CJITM1\0\0"
    return dict(protocol=version, bytes_per_arena=length, arena_count=2,
                mailbox_bytes=mailbox, response_offset=response, error_offset=error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-id", default="launcher-backbuffer-20260912-24")
    parser.add_argument("--simulator", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,70}", args.build_id):
        parser.error("build-id must be lowercase letters/digits/hyphens")
    build_id = args.build_id + ("-simulator" if args.simulator else "")
    stage = ROOT / ".build/ios-jit/launcher-backbuffer" / build_id
    output = ROOT / "artifacts/ios-jit" / build_id
    stage.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "delivery-receipt.json").exists():
        raise RuntimeError("This kit was delivered. Choose a new build ID and version; preserve its exact symbols and files.")
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
    native_target = 'simulator' if args.simulator else 'ios'
    run(['python3', str(SOURCE/'build_native.py'), '--target', native_target])
    launcher_native=ROOT/'.build/ios-jit/launcher-backbuffer-native'/native_target
    launcher_receipt=json.loads((launcher_native/'receipt.json').read_text())
    assert all(digest(ROOT/name)==value for name,value in launcher_receipt['source_sha256'].items())
    assert all(digest(ROOT/name)==value for name,value in launcher_receipt['libraries'].items())
    sdk_name = "iphonesimulator" if args.simulator else "iphoneos"
    sdk = run(["xcrun", "--sdk", sdk_name, "--show-sdk-path"])
    xcode = run(["xcodebuild", "-version"])
    sdk_version = run(["xcrun", "--sdk", sdk_name, "--show-sdk-version"])
    assert "Xcode 26.6" in xcode, xcode
    arch = platform.machine() if args.simulator else "arm64"
    target = f"{arch}-apple-ios26.0" + ("-simulator" if args.simulator else "")
    app = stage / "Payload/CelesteJITEverest.app"
    # Only this build's generated .app is replaced; no AOT/private input touched.
    if app.exists():
        shutil.rmtree(app)
    app.mkdir(parents=True)
    sources = sorted(p for p in SOURCE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    sources += [SOURCE.parent / "native-probe/scripts/make_icon.swift"]
    sources += [p for p in BASE.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    sources += list((HOOK / "src").glob("*")) + [SOURCE / "scripts/celeste-jit-probe.js"]
    sources += [ROOT/'modern-ios/CelesteIOSFoundation'/n for n in ['TouchControlsPolicy.cs','PlatformPolicies.cs']]
    sources += [ROOT/'scripts/generate-ios-touch-assets.py',ROOT/'modern-ios/Assets/TouchControls/NOTICE.md']
    sources += list((ROOT/'modern-ios/Assets/TouchControls/Source').glob('*.svg'))
    game_receipt=json.loads((FNA_MANAGED/'receipt.json').read_text())
    assert all(digest(FNA_MANAGED/name)==value for name,value in game_receipt['managed_sha256'].items())
    assert all(digest(ROOT/name)==value for name,value in game_receipt['source_sha256'].items())
    mod_receipt=json.loads((MODS/'receipt.json').read_text())
    assert all(digest(MODS/name)==value['sha256'] for name,value in mod_receipt['files'].items())
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    dependencies = ROOT / '.build/ios-jit/everest-dependencies'
    build_info = {
        "build_id": build_id, "version": APP_VERSION, "build_number": BUILD_NUMBER, "protocol": "CJIT mailbox 1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "xcode": xcode, "sdk": sdk_name, "sdk_version": sdk_version, "target": target,
        "base_commit": run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "source_sha256": source_hashes,
        "fna_managed_receipt_sha256": digest(FNA_MANAGED / "fna-compatibility.json"),
        "fna_graphics_compatibility": game_receipt["fna_graphics_compatibility"],
        "fna_backbuffer_compatibility": game_receipt["fna_backbuffer_compatibility"],
        "fna_extension_upstream": json.loads((SOURCE / "fna-extension-pin.json").read_text()),
        "native_foundation_logical_sha256": "9fb302d221180e39f270ea5ebf48e18433b67bd0a40943c042a227fe0f8ad6a2",
        "script_template_sha256": digest(SOURCE / "scripts/celeste-jit-probe.js"),
        "device_jit_tested": False, "scope": "Retained Metal backbuffer readback, validated array segments and automatic renderer canary; build23 session contract retained",
        "ios_support": {"id":"CelesteIOS","version":"1.0.0","abi":1,"required":True,"sha256":digest(FNA_MANAGED/'CelesteIOS.dll')},
        "session_protocol_source_sha256":digest(SOURCE/'src/CJSession.c'),
        "launcher_native_receipt_sha256": digest(launcher_native/"receipt.json"),
        "launcher_native_libraries": launcher_receipt["libraries"],
        "launcher_dependency_commits": launcher_receipt["dependency_commits"],
        "diagnostics_policy": "bounded_v1",
        "vm_range_policy": "intersected_os_pages_v1",
        "vm_range_source_sha256": digest(SOURCE / "src/VMRange.c"),
        "reused_base_game_build": "content-20260911-14",
        "mod_download_manifest": {name:dict(row,url=mod_receipt["original_helpers"]["files"].get(name,{}).get("url")) for name,row in mod_receipt["files"].items()},
        "game_fixture_sha256":digest(FNA_MANAGED/'CelesteJITEverest.dll'),
        "game_fixture_bytes":(FNA_MANAGED/'CelesteJITEverest.dll').stat().st_size,
        "game_receipt_sha256":digest(FNA_MANAGED/'receipt.json'),
        "mod_zip_files":mod_receipt['files'],
        "mod_receipt_sha256":digest(MODS/'receipt.json'),
        "helper_pins_sha256":digest(SOURCE/"helper-pins.json"),
        "sj_release_manifest_sha256":digest(SOURCE/"sj-pins.json"),
        "original_helper_files":mod_receipt["original_helpers"]["files"],
        "mono8_utils_compatibility":game_receipt["mono8_utils_compatibility"],
        "everest_source_receipt_sha256":digest(ROOT/'.build/ios-jit/everest-source/source-receipt.json'),
        "everest_preparation_sha256":digest(ROOT/'.build/ios-jit/everest-game/preparation-receipt.json'),
        "private_owner_content":False, "private_prepared_game_il":True, "persistent_content_import":True,
        "runtime_pin": json.loads((BASE / "runtime-pin.json").read_text()),
        "runtime_patch_sha256": digest(BASE / "runtime-alias.patch"),
        "monomod_pin": json.loads((HOOK / "dependencies-pin.json").read_text()),
        "monomod_patch_sha256": digest(HOOK / "monomod-hosting.patch"),
        "monomod_dependencies_receipt_sha256": digest(dependencies / "receipt.json"),
        "aot_disabled": True, "interpreter_disabled": True, "bytes_per_arena": 268435456,
        "stikdebug_source_reference": "94bc9e8cf3b41f32f125f046abf33d913f4e1b2d",
        "livecontainer_source_reference": "3afa9eb9a53625e9b8bd8b932e5785fd716ad5ae",
        "default_route": "LiveContainer 1 probe -> LiveContainer 2 StikDebug; actual target PID",
    }
    # Reuse only the small trusted catalog; never package the game assets.
    accepted = ROOT / "artifacts/ios-jit/everest-canary-20260911-13"
    with zipfile.ZipFile(accepted / "CelesteJITEverest-unsigned.ipa") as archive:
        catalog_bytes = archive.read("Payload/CelesteJITEverest.app/GameContentManifest.json")
    assert hashlib.sha256(catalog_bytes).hexdigest() == "0498b136c5963dfecd7107d9bf29f60cba8424d96e323d595302a515bbae1670"
    content_manifest = json.loads(catalog_bytes)
    (app / "GameContentManifest.json").write_bytes(catalog_bytes)
    build_info.update(game_content_manifest_sha256=hashlib.sha256(catalog_bytes).hexdigest(),
                      game_content_aggregate_sha256=content_manifest["aggregate_sha256"],
                      game_content_bytes=sum(x["bytes"] for x in content_manifest["files"]),
                      bundled_content_files=0)
    (app / "BuildInfo.json").write_text(json.dumps(build_info, indent=2) + "\n")
    shutil.copy2(SOURCE / "scripts/celeste-jit-probe.js", app / "celeste-jit-probe.js")
    shutil.copy2(MODS/"CJITCodeCanary-v1.0.0.zip",app/"CJITCodeCanary-v1.0.0.zip")
    shutil.copy2(SOURCE/"sj-pins.json",app/"SJReleaseManifest.json")
    shutil.copy2(ROOT / "LICENSE", app / "REPOSITORY_LICENSE.txt")
    shutil.copy2(ROOT / "LICENSE", output / "REPOSITORY_LICENSE.txt")
    if (SOURCE / "THIRD_PARTY_NOTICES.md").exists():
        shutil.copy2(SOURCE / "THIRD_PARTY_NOTICES.md", app / "THIRD_PARTY_NOTICES.md")
    shutil.copy2(ROOT/'modern-ios/Assets/TouchControls/NOTICE.md',app/'TOUCH_ARTWORK_NOTICE.md')
    if (SOURCE / "licenses").exists():
        shutil.copytree(SOURCE / "licenses", app / "licenses")
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
        "CFBundleDevelopmentRegion": "en", "CFBundleDisplayName": "Celeste JIT Everest",
        "CFBundleExecutable": "CelesteJITEverest", "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0", "CFBundleName": "CelesteJITEverest",
        "CFBundlePackageType": "APPL", "CFBundleShortVersionString": APP_VERSION, "CFBundleVersion": BUILD_NUMBER,
        "MinimumOSVersion": "26.0", "LSRequiresIPhoneOS": True, "UIDeviceFamily": [1, 2],
        "CFBundleSupportedPlatforms": ["iPhoneSimulator" if args.simulator else "iPhoneOS"],
        "UIRequiredDeviceCapabilities": ["arm64"] if not args.simulator else [],
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"],
        "UISupportedInterfaceOrientations~ipad": ["UIInterfaceOrientationPortrait", "UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"],
        "UILaunchScreen": {}, "UIFileSharingEnabled": True, "LSSupportsOpeningDocumentsInPlace": True,
        "LSApplicationQueriesSchemes": ["livecontainer2", "stikdebug", "stikjit"],
        "UIApplicationSceneManifest": {"UIApplicationSupportsMultipleScenes": False, "UISceneConfigurations": {
            "UIWindowSceneSessionRoleApplication": [{"UISceneConfigurationName": "Default", "UISceneDelegateClassName": "CJSceneDelegate"}]}},
    }
    info.update(plistlib.loads(partial.read_bytes()))
    (app / "Info.plist").write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY))
    (app / "PkgInfo").write_bytes(b"APPL????")
    executable = app / "CelesteJITEverest"
    objects = []
    mod_object = stage / "CJModStore.o"
    run(["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk, "-fobjc-arc", "-O2", "-g", "-Wall", "-Wextra", "-Werror", "-Wno-deprecated-declarations", "-c", str(SOURCE / "src/CJModStore.m"), "-o", str(mod_object)])
    objects.append(str(mod_object))
    content_object = stage / "CJContentImport.o"
    run(["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk,
         "-fobjc-arc", "-O2", "-g", "-Wall", "-Wextra", "-Werror", "-Wno-deprecated-declarations",
         "-c", str(SOURCE / "src/CJContentImport.m"), "-o", str(content_object)])
    objects.append(str(content_object))
    log_object=stage/'CJEventStore.o'
    run(['xcrun','clang','-target',target,'-isysroot',sdk,'-fobjc-arc','-O2','-g','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-c',str(SOURCE/'src/CJEventStore.m'),'-o',str(log_object)])
    objects.append(str(log_object))
    for name in ("VMRange", "VMRangeDarwin", "CJFrameMetrics", "CJSession"):
        obj = stage / (name + ".o")
        run(["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk,
             "-std=c11", "-O2", "-g", "-Wall", "-Wextra", "-Werror", "-c", str(SOURCE / "src" / (name + ".c")), "-o", str(obj)])
        objects.append(str(obj))
    # Compiling a source file and linking with -g in one clang invocation also
    # creates <executable>.dSYM beside the executable on this Apple toolchain.
    # Compile an object first so symbols are emitted only to the explicit path.
    main_object = stage / "main.o"
    compile_args = ["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk,
                    "-I" + str(launcher_native), "-I" + str(SOURCE.parent / "native-probe/src"), "-I" + str(BASE / "src"), "-I" + str(HOOK / "src"), "-fobjc-arc", "-O2", "-g", "-fno-omit-frame-pointer", "-Wall", "-Wextra", "-Werror",
                    "-Wno-deprecated-declarations", "-c", str(SOURCE / "src/main.m"), "-o", str(main_object)]
    dependency_file = stage / "main.d"
    compile_args += ["-MMD", "-MF", str(dependency_file)]
    run(compile_args)
    dependencies = {Path(p).resolve() for p in shlex.split(dependency_file.read_text().replace("\\\n", " "))[1:]}
    expected_header = (BASE / "src/ProbeProtocol.h").resolve()
    assert expected_header in dependencies
    assert (SOURCE.parent / "native-probe/src/ProbeProtocol.h").resolve() not in dependencies
    assert (SOURCE / "src/VMRange.h").resolve() in dependencies
    assert (SOURCE.parent / "native-probe/src/VMRange.h").resolve() not in dependencies
    build_info["resolved_protocol_header"] = str(expected_header.relative_to(ROOT))
    build_info["resolved_protocol_header_sha256"] = digest(expected_header)
    shutil.copy2(dependency_file, output / "main-compiler-dependencies.d")
    link_args = ["xcrun", "swiftc", "-target", target, "-sdk", sdk, "-framework", "UIKit", "-framework", "Foundation", "-framework", "UniformTypeIdentifiers", "-framework", "QuartzCore", "-Xlinker", "-no_adhoc_codesign",
                 str(main_object), *objects, *[str(launcher_native/n) for n in ["libCJLauncher.a", "libZIPFoundation.a", "libCYaml.a"]], "-lz", "-o", str(executable)]
    if not args.simulator:
        base = ROOT / ".build/ios-jit/managed-runtime"
        native = base / "pack-ios-8.0.28/runtimes/ios-arm64/native"
        runtime = base / "mono-build-ios"
        compatibility = ROOT / '.build/ios-jit/sj-lobby-runtime'
        compatibility_receipt = json.loads((compatibility / 'receipt.json').read_text())
        assert digest(ROOT / '.build/ios-jit/sj-budget-runtime/ios/libmonosgen-2.0.a') == compatibility_receipt['targets']['ios']['original_sha256']
        libraries = [compatibility / 'ios/libmonosgen-2.0.a']
        assert digest(libraries[0]) == compatibility_receipt['targets']['ios']['sha256']
        assert digest(SOURCE.parent / 'sj-lobby/build_runtime.py') == compatibility_receipt['builder_sha256']
        build_info['mono_compatibility_receipt_sha256'] = digest(compatibility / 'receipt.json')
        build_info['mono_compatibility_patch_sha256'] = compatibility_receipt['patch_sha256']
        build_info['mono_ordinary_chunk_minimum_bytes'] = 16384
        build_info['inherited_mono_visibility_receipt_sha256'] = json.loads((ROOT/'.build/ios-jit/sj-budget-runtime/receipt.json').read_text())['inherited_visibility_receipt_sha256']
        shutil.copy2(compatibility / 'receipt.json', output / 'mono-compatibility-receipt.json')
        libraries += [runtime / ("mono/mini/libmono-component-" + name + ".a") for name in
                      ("marshal-ilgen-static", "debugger-stub-static", "hot_reload-stub-static", "diagnostics_tracing-stub-static")]
        libraries += [native / name for name in ['libSystem.Native.a', 'libSystem.IO.Compression.Native.a', 'libSystem.Security.Cryptography.Native.Apple.a']]
        assert all(p.is_file() for p in libraries), libraries
        patch = json.loads((base / "runtime-patch-receipt.json").read_text())
        for name, hashes in patch["files"].items():
            assert digest(base / "runtime-v8.0.28" / name) == hashes["patched_sha256"]
        config = (runtime / "config.h").read_text()
        assert "#define DISABLE_INTERPRETER 1" in config and "#define DISABLE_AOT 1" in config
        assert "#define DISABLE_JIT 1" not in config
        nm = run(["xcrun", "nm", "-u", str(libraries[0])])
        assert "_cj_mono_code_alloc" in nm and "_cj_mono_writable" in nm and "_cj_mono_flush" in nm
        names = sorted(set(line[1:] for lib in libraries[-3:] for line in run(["xcrun", "nm", "-g", "-U", "-j", str(lib)]).splitlines() if re.fullmatch(r"_(SystemNative_|CompressionNative_|AppleCryptoNative_)[A-Za-z0-9_]+", line)))
        assert len(names) > 100
        table = stage / "SystemNativeTable.c"
        table.write_text('#include <string.h>\n' + ''.join('extern void ' + name + '(void);\n' for name in names) +
                         'void *CJResolveSystemNative(const char *name) {\n' + ''.join('if (!strcmp(name, "' + name + '")) return (void *)&' + name + ';\n' for name in names) + 'return 0;\n}\n')
        native_libraries = [NATIVE / (name + ".xcframework") / "ios-arm64" / ("lib" + name + ".a") for name in ("FNA3D", "FAudio", "Theorafile", "SDL2", "ApplePlatformStubs")]
        native_manifest = json.loads((NATIVE / "normalized-manifest.json").read_text())
        assert native_manifest["logicalSetSha256"] == build_info["native_foundation_logical_sha256"]
        # Only FNA3D is overlaid; the accepted AOT/native foundation stays intact.
        graphics_native = ROOT / ".build/ios-jit/launcher-backbuffer-renderer"
        graphics_receipt = json.loads((graphics_native / "receipt.json").read_text())
        assert digest(SOURCE / "native/fna3d-callback.patch") == graphics_receipt["patch_sha256"]
        assert digest(SOURCE / "native/fna3d-backbuffer.patch") == graphics_receipt["backbuffer_patch_sha256"]
        assert digest(SOURCE / "native-build.py") == graphics_receipt["builder_sha256"]
        assert digest(native_libraries[0]) == graphics_receipt["base_ios_archive_sha256"]
        native_libraries[0] = ROOT / graphics_receipt["ios_archive"]
        assert digest(native_libraries[0]) == graphics_receipt["ios_archive_sha256"]
        assert all(digest(ROOT/name) == value for name,value in graphics_receipt["source_sha256"].items())
        build_info["graphics_native_patch_sha256"] = graphics_receipt["patch_sha256"]
        build_info["graphics_backbuffer_patch_sha256"] = graphics_receipt["backbuffer_patch_sha256"]
        build_info["graphics_native_receipt_sha256"] = digest(graphics_native / "receipt.json")
        shutil.copy2(graphics_native / "receipt.json", output / "graphics-native-receipt.json")
        fmod_stage=ROOT/'.build/ios-jit/celeste-fmod'
        native_libraries += [fmod_stage/'FMOD.xcframework/ios-arm64/libfmod_iphoneos-localized.a',fmod_stage/'FMODStudio.xcframework/ios-arm64/libfmodstudio_iphoneos-arm64.a']
        lua_stage=ROOT/'.build/ios-jit/everest-lua'
        lua_receipt=json.loads((lua_stage/'receipt.json').read_text())
        native_libraries.append(lua_stage/'ios/liblua54.a')
        build_info['lua_receipt_sha256']=digest(lua_stage/'receipt.json')
        shutil.copy2(lua_stage/'receipt.json',output/'lua-receipt.json')
        fmod_license=ROOT/'.build/ios-jit/device-evidence/2026-09-11/build-12-ready/packaged-app/FMOD-LICENSE.txt'
        shutil.copy2(fmod_license,app/'FMOD-LICENSE.txt')
        build_info['fmod_license_sha256']=digest(fmod_license)
        build_info['fmod_version']='1.10.09; build 97915; native iOS CoreAudio'
        build_info['fmod_manifest_sha256']=digest(fmod_stage/'fmod-ios-manifest.json')
        shutil.copy2(fmod_stage/'fmod-ios-manifest.json',output/'fmod-ios-manifest.json')
        exports = set()
        for lib in native_libraries:
            exports.update(line[1:] for line in run(["xcrun", "nm", "-g", "-U", "-j", str(lib)]).splitlines() if re.fullmatch(r"_(FMOD_[A-Za-z0-9_]+|SDL_[A-Za-z0-9_]+|FNA3D_[A-Za-z0-9_]+|FAudio[A-Za-z0-9_]*|F3DAudio[A-Za-z0-9_]*|FACT[A-Za-z0-9_]*|FAPO[A-Za-z0-9_]*|XNA_[A-Za-z0-9_]+|stb_vorbis_[A-Za-z0-9_]+|tf_[A-Za-z0-9_]+|luaL?_[A-Za-z0-9_]+|luaopen_[A-Za-z0-9_]+)", line))
        assert len(exports) > 500
        fna_table = stage / "FNAStaticTable.c"
        fna_table.write_text('#include <string.h>\n' + ''.join('extern void ' + n + '(void);\n' for n in sorted(exports)) +
            'void *CJResolveFNAStatic(const char *name) {\n' + ''.join('if (!strcmp(name,"' + n + '")) return (void *)&' + n + ';\n' for n in sorted(exports)) + 'return 0;\n}\n')
        (stage / "native-export-table.json").write_text(json.dumps(sorted(exports), indent=2) + "\n")
        for source_file in [SOURCE / "src/CJHookCodeArena.c", BASE / "src/CanaryNative.c", BASE / "src/CJNativeResolver.c", BASE / "src/CJMonoThread.c", SOURCE / "src/CJGraphicsManaged.m", SOURCE / "src/CJGraphicsPlatform.m", SOURCE / "src/CJHookNative.c", table, fna_table]:
            obj = stage / (source_file.stem + ".o")
            options = ["-fobjc-arc", "-Wno-deprecated-declarations"] if source_file.suffix == ".m" else ["-std=c11"]
            run(["xcrun", "--sdk", sdk_name, "clang", "-target", target, "-isysroot", sdk, "-O2", "-g", "-Wall", "-Wextra", "-Werror",
                 "-I" + str(SOURCE / "src"), "-I" + str(HOOK / "src"), "-I" + str(NATIVE / "SDL2.xcframework/ios-arm64/Headers"), "-I" + str(BASE / "src"), "-I" + str(SOURCE.parent / "native-probe/src"), "-I" + str(native / "include/mono-2.0"), *options, "-c", str(source_file), "-o", str(obj)])
            link_args.append(str(obj))
        libraries += native_libraries
        for framework in ("AVFoundation", "AudioToolbox", "CoreBluetooth", "CoreGraphics", "CoreHaptics", "CoreMotion", "CoreVideo", "GameController", "Metal", "OpenGLES"):
            link_args += ["-framework", framework]
        link_args += list(map(str, libraries)) + ["-lc++", "-liconv", "-lz", "-framework", "Security", "-framework", "CoreFoundation"]
        managed = app / "Managed"; managed.mkdir()
        bcl = base / "pack-ios-8.0.28/runtimes/ios-arm64/lib/net8.0"
        for file in list(bcl.glob("*.dll")) + [native / "System.Private.CoreLib.dll"]:
            shutil.copy2(file, managed / file.name)
        for file in (base / "pack-ios-8.0.28").glob("*.TXT"): shutil.copy2(file, app / file.name)
        build_info["native_library_sha256"] = {str(file.relative_to(ROOT)): digest(file) for file in libraries}
        build_info["framework_assembly_sha256"] = {file.name: digest(file) for file in managed.glob("*.dll")}
        for name in game_receipt['managed_sha256']:
            if name == 'EverestSplash.dll': continue
            shutil.copy2(FNA_MANAGED/name, managed/name)
        shutil.copytree(FNA_MANAGED/'orig',managed/'orig')
        build_info['everest_assembly_sha256']={p.name:digest(p) for p in managed.glob('*.dll') if p.name in game_receipt['managed_sha256']}
        build_info['fna_assembly_sha256']=digest(managed/'FNA.dll')
        shutil.copy2(FNA_MANAGED/'receipt.json',output/'managed-receipt.json')
        build_info["runtime_config_sha256"] = digest(runtime / "config.h")
        (app / "BuildInfo.json").write_text(json.dumps(build_info, indent=2) + "\n")
    shutil.copy2(launcher_native/"receipt.json",output/"launcher-native-receipt.json")
    run(link_args)
    build_info["compiled_protocol"] = read_compiled_protocol(executable.read_bytes())
    assert build_info["compiled_protocol"] == dict(protocol=1, bytes_per_arena=268435456,
           arena_count=2, mailbox_bytes=96, response_offset=48, error_offset=88)
    assert build_info["compiled_protocol"]["bytes_per_arena"] == build_info["bytes_per_arena"]
    (app / "BuildInfo.json").write_text(json.dumps(build_info, indent=2) + "\n")
    dsym = output / "CelesteJITEverest.app.dSYM"
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
        deliverable = output / "CelesteJITEverest.app"
        if deliverable.exists():
            shutil.rmtree(deliverable)
        shutil.copytree(app, deliverable)
    else:
        deliverable = output / "CelesteJITEverest-unsigned.ipa"
        with zipfile.ZipFile(deliverable, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(app.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(stage))
        with zipfile.ZipFile(deliverable) as archive:
            assert archive.testzip() is None
            assert archive.read("Payload/CelesteJITEverest.app/CelesteJITEverest") == executable.read_bytes()
            validate_payload_members((name, archive.read(name)) for name in archive.namelist())
    shutil.copy2(SOURCE / "scripts/celeste-jit-probe.js", output / "celeste-jit-probe-TEMPLATE.js")
    shutil.copy2(MODS/"CJITCodeCanary-v1.0.0.zip",output/"CJITCodeCanary-v1.0.0.zip")
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
