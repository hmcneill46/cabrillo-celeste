#!/usr/bin/env python3
"""Build Cabrillo using repository sources and explicitly locked local runtime inputs."""
import argparse
import datetime
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import zipfile
from pathlib import Path
from macho_identity import reproduce_uuid, uuid_range, without_uuid_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/ios-jit/launcher-catalogue"
DEVELOPER = "/Applications/Xcode-26.6.app/Contents/Developer"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduce-build28", action="store_true", help="Preserve historical resources/ZIP metadata and require exact source hashes")
    parser.add_argument("--work", default=".build/reproduce-build28")
    parser.add_argument("--output", default="artifacts/reproduce-build28")
    args = parser.parse_args()
    if not args.reproduce_build28:
        parser.error("Use --reproduce-build28. This locked migration recipe does not issue new release identities.")
    work, output = (ROOT / args.work).resolve(), (ROOT / args.output).resolve()
    assert ROOT in work.parents and ROOT in output.parents and work != output
    if work.exists():
        raise RuntimeError("Use an empty work directory. Retain previous build evidence or choose --work.")
    if output.exists():
        raise RuntimeError("Use an empty output directory or choose --output.")
    meta = json.loads((ROOT / ".private/migration/build28-replay.json").read_text())
    inputs = json.loads((ROOT / ".private/migration/inputs.json").read_text())
    for name, row in inputs.items():
        assert sha(ROOT / name) == row["sha256"], name
    original = meta["build"]
    if args.reproduce_build28:
        for name, digest in original["source_sha256"].items():
            assert sha(ROOT / name) == digest, name
    work.mkdir(parents=True)
    output.mkdir(parents=True)
    old = meta["canonical_root"]
    old_native = ".build/ios-jit/launcher-catalogue-native/ios"
    old_stage = ".build/ios-jit/launcher-catalogue/launcher-catalogue-20260913-28"
    tree = work / "tree"
    native, stage = tree / old_native, tree / old_stage
    native.mkdir(parents=True)
    stage.mkdir(parents=True)
    env = dict(os.environ, DEVELOPER_DIR=DEVELOPER, CLANG_MODULE_CACHE_PATH=str(work / "module-cache"))
    commands = []

    def run(cmd):
        cmd = list(map(str, cmd))
        commands.append(cmd)
        with (output / "build.log").open("a") as log:
            log.write(repr(cmd) + "\n"); log.flush()
            result = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}); see {output / 'build.log'}")

    def resolve(logical):
        if logical.startswith(old_stage) or logical.startswith(old_native):
            return tree / logical
        prefix = ".build/ios-jit/launcher-catalogue-native-dependencies/"
        if logical.startswith(prefix):
            return ROOT / "vendor" / logical[len(prefix):]
        if logical in meta["aliases"]:
            return ROOT / meta["aliases"][logical]
        if (ROOT / logical).exists():
            return ROOT / logical
        p = ROOT / ".private/inputs" / logical
        if p.exists():
            return p
        raise FileNotFoundError(logical)

    def rewrite(token):
        for flag in ["-I", "-iquote", "-L", "-F", ""]:
            prefix = flag + old + "/"
            if token.startswith(prefix):
                return flag + str(resolve(token[len(prefix):]))
        return token

    maps = [(ROOT, old), (ROOT / ".private/inputs", old), (tree, old), (ROOT / "vendor", old + "/.build/ios-jit/launcher-catalogue-native-dependencies")]
    # Keep new Clang module-cache paths real so the fresh dSYM can find them.
    maps.append((work / "module-cache", str(work / "module-cache")))
    c_maps = [f"-ffile-prefix-map={a}={b}" for a,b in maps] + ["-fdebug-compilation-dir=" + old]
    swift_maps = [x for a,b in maps for x in ["-file-prefix-map", str(a) + "=" + b, "-debug-prefix-map", str(a) + "=" + b]] + ["-file-compilation-dir", old]
    sdk = subprocess.check_output(["xcrun", "--sdk", "iphoneos", "--show-sdk-path"], env=env, text=True).strip()
    assert subprocess.check_output(["xcodebuild", "-version"], env=env, text=True).strip() == original["xcode"]
    target = "arm64-apple-ios26.0"
    # Compile dependencies from pinned source: none of these three archives is imported.
    zip_sources = sorted((ROOT / "vendor/ZIPFoundation/Sources/ZIPFoundation").glob("*.swift"))
    run(["xcrun", "swiftc", "-swift-version", "5", "-O", "-target", target, "-sdk", sdk, "-module-name", "ZIPFoundation", "-emit-library", "-static", "-emit-module", "-emit-module-path", native / "ZIPFoundation.swiftmodule", "-o", native / "libZIPFoundation.a", *swift_maps, *zip_sources])
    yaml = ROOT / "vendor/Yams/Sources/CYaml"
    yaml_objects = []
    for source in sorted((yaml / "src").glob("*.c")):
        obj = native / (source.stem + ".o")
        run(["xcrun", "clang", "-target", target, "-isysroot", sdk, "-DYAML_DECLARE_STATIC", "-O2", "-g", "-I" + str(yaml / "include"), *c_maps, "-c", source, "-o", obj])
        yaml_objects.append(obj)
    run(["xcrun", "libtool", "-static", "-o", native / "libCYaml.a", *yaml_objects])
    swift_sources = sorted((SOURCE / "native").glob("*.swift"))
    run(["xcrun", "swiftc", "-swift-version", "5", "-O", "-g", "-target", target, "-sdk", sdk, "-module-name", "CJLauncher", "-I", native, "-I", yaml / "include", "-emit-library", "-static", "-emit-module", "-emit-module-path", native / "CJLauncher.swiftmodule", "-emit-objc-header-path", native / "CJLauncher-Swift.h", "-o", native / "libCJLauncher.a", *swift_maps, *swift_sources])
    # Generate the native symbol tables from the actual pinned link libraries.
    import re
    libraries = [resolve(n) for n in original["native_library_sha256"]]
    system = [p for p in libraries if p.name.startswith("libSystem.")]
    def symbols(paths, pattern):
        found = set()
        for p in paths:
            text = subprocess.check_output(["xcrun", "nm", "-g", "-U", "-j", str(p)], env=env, text=True)
            found.update(line[1:] for line in text.splitlines() if re.fullmatch(pattern, line))
        return sorted(found)
    names = symbols(system, r"_(SystemNative_|CompressionNative_|AppleCryptoNative_)[A-Za-z0-9_]+")
    assert len(names) > 100
    (stage / "SystemNativeTable.c").write_text('#include <string.h>\n' + ''.join('extern void ' + name + '(void);\n' for name in names) + 'void *CJResolveSystemNative(const char *name) {\n' + ''.join('if (!strcmp(name, "' + name + '")) return (void *)&' + name + ';\n' for name in names) + 'return 0;\n}\n')
    names = symbols(libraries, r"_(FMOD_[A-Za-z0-9_]+|SDL_[A-Za-z0-9_]+|FNA3D_[A-Za-z0-9_]+|FAudio[A-Za-z0-9_]*|F3DAudio[A-Za-z0-9_]*|FACT[A-Za-z0-9_]*|FAPO[A-Za-z0-9_]*|XNA_[A-Za-z0-9_]+|stb_vorbis_[A-Za-z0-9_]+|tf_[A-Za-z0-9_]+|luaL?_[A-Za-z0-9_]+|luaopen_[A-Za-z0-9_]+)")
    assert len(names) > 500
    (stage / "FNAStaticTable.c").write_text('#include <string.h>\n' + ''.join('extern void ' + n + '(void);\n' for n in names) + 'void *CJResolveFNAStatic(const char *name) {\n' + ''.join('if (!strcmp(name,"' + n + '")) return (void *)&' + n + ';\n' for n in names) + 'return 0;\n}\n')
    for command in original["build_commands"]:
        if "clang" in command and "-c" in command:
            run([rewrite(t) for t in command] + c_maps)
    app = stage / "Payload/CelesteJITEverest.app"
    shutil.copytree(ROOT / ".private/resources/build28", app)
    # Rebuild the icon catalogue with actool, rather than copying compiled assets.
    assets = stage / "Assets.xcassets"
    icon = assets / "AppIcon.appiconset"
    icon.mkdir(parents=True)
    (assets / "Contents.json").write_text(json.dumps({"info":{"author":"xcode","version":1}}))
    (icon / "Contents.json").write_text(json.dumps({"images":[{"filename":"AppIcon.png","idiom":"universal","platform":"ios","size":"1024x1024"}],"info":{"author":"xcode","version":1}}))
    run(["xcrun", "swift", ROOT / "experiments/ios-jit/native-probe/scripts/make_icon.swift", icon / "AppIcon.png"])
    run(["xcrun", "actool", assets, "--compile", app, "--platform", "iphoneos", "--minimum-deployment-target", "26.0", "--target-device", "iphone", "--target-device", "ipad", "--app-icon", "AppIcon", "--output-partial-info-plist", stage / "asset-info.plist"])
    settings = meta["bundle_settings"]
    (app / "Info.plist").write_bytes(plistlib.dumps(settings, fmt=plistlib.FMT_BINARY))
    for logical, time in meta["native_object_mtimes"].items():
        path = resolve(logical)
        if path.is_file():
            os.utime(path, (time, time))
    executable = app / "CelesteJITEverest"
    attempts = []
    # This Xcode linker produces two observed orders for objc_msgSend GOT entries,
    # even with identical objects and -reproducible. Relink (never rewrite code)
    # a bounded number of times, accepting only the full locked non-UUID hash.
    for attempt in range(8):
        run([rewrite(t) for t in original["link_command"]])
        candidate = work / "stripped-candidate"
        shutil.copy2(executable, candidate)
        run(["xcrun", "strip", "-S", candidate])
        digest = without_uuid_hash(candidate.read_bytes())
        attempts.append(dict(attempt=attempt + 1, without_uuid_sha256=digest))
        if digest == meta["executable_identity"]["without_uuid_sha256"]:
            break
    else:
        (output / "link-attempts.json").write_text(json.dumps(attempts, indent=2) + "\n")
        raise RuntimeError("No byte-identical link after eight attempts; refuse historical identity")
    run(["xcrun", "dsymutil", executable, "--object-prefix-map", old + "=" + str(ROOT), "-o", output / "CelesteJITEverest.app.dSYM"])
    run(["xcrun", "strip", "-S", executable])
    generated_executable_sha256 = sha(executable)
    generated = executable.read_bytes()
    u0, u1 = uuid_range(generated)
    generated_uuid = generated[u0:u1].hex()
    if args.reproduce_build28:
        # This succeeds only when all other bytes match the historical executable.
        # It cannot mask a changed instruction, data byte, resource or load command.
        executable.write_bytes(reproduce_uuid(generated, meta["executable_identity"]))
        dwarf = output / "CelesteJITEverest.app.dSYM/Contents/Resources/DWARF/CelesteJITEverest"
        data = dwarf.read_bytes(); d0, d1 = uuid_range(data)
        assert data[d0:d1].hex() == generated_uuid, "Symbols must belong to this fresh build"
        dwarf.write_bytes(data[:d0] + bytes.fromhex(meta["executable_identity"]["uuid_hex"]) + data[d1:])
    actual = {str(p.relative_to(app)):dict(sha256=sha(p), bytes=p.stat().st_size) for p in app.rglob("*") if p.is_file()}
    expected = {r["name"]:r for r in meta["entries"]}
    differences = {n:dict(expected=expected.get(n,{}).get("sha256"), actual=actual.get(n,{}).get("sha256")) for n in sorted(set(actual)|set(expected)) if actual.get(n,{}).get("sha256") != expected.get(n,{}).get("sha256")}
    ipa = output / "CelesteJITEverest-unsigned.ipa"
    with zipfile.ZipFile(ipa, "w", zipfile.ZIP_DEFLATED) as archive:
        for entry in meta["entries"]:
            z = zipfile.ZipInfo("Payload/CelesteJITEverest.app/" + entry["name"], tuple(entry["date_time"]))
            for name in ["compress_type","create_system","create_version","extract_version","flag_bits","volume","internal_attr","external_attr"]:
                setattr(z, name, entry[name])
            z.extra, z.comment = bytes.fromhex(entry["extra"]), bytes.fromhex(entry["comment"])
            archive.writestr(z, (app / entry["name"]).read_bytes())
    receipt = dict(status="PASS_EXACT_BUILD28_REPRODUCTION" if sha(ipa)==original["ipa_sha256"] else "BUILD_COMPLETE_COMPARISON_DIFFERENCES", reproduction=args.reproduce_build28, actual_created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), ipa_sha256=sha(ipa), reference_ipa_sha256=original["ipa_sha256"], bytes=ipa.stat().st_size, file_differences=differences, compiled_source_count=len(swift_sources)+len(zip_sources)+len(yaml_objects)+sum("clang" in c and "-c" in c for c in original["build_commands"]), compiled_commands=commands, pinned_dependencies_reused=True, original_executable_copied=False, linker_executable_sha256=generated_executable_sha256, linker_uuid=generated_uuid, link_attempts=attempts, historical_uuid_normalized_only_after_all_other_bytes_matched=args.reproduce_build28)
    (output / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k:v for k,v in receipt.items() if k!="compiled_commands"}, indent=2))
    if receipt["status"] != "PASS_EXACT_BUILD28_REPRODUCTION":
        raise RuntimeError("Fresh package does not match build28; see build-receipt.json")


if __name__ == "__main__":
    main()
