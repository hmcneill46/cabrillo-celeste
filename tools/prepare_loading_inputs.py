#!/usr/bin/env python3
"""One-time, read-only import of explicit managed-build inputs into Cabrillo.

The normal loading builder never accesses the legacy checkout. This importer
requires its path explicitly, refuses an existing capsule, copies bytes (never
hard links), and records every input. SDKs, game IL and reference source stay
private. No build or Git mutation runs in the source checkout.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".private/loading-inputs"
PINS = {
    "": "d72e94f4b9e62b91cbdea674587ed39d53de9550",
    "external/MonoMod": "dfc30a1506d37fb88a2c2be004f525205f46a24c",
    "external/MonoMod/external/iced": "c50f29b7bc305696895c075f3fc7719751426b12",
    "external/NLua": "b3524288712743fb2394dcf615d14d0dac3276e2",
    "lib-ext": "591f7c12fcb4e8fda9ef5ef1b331b5ed40d3fb1f",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", required=True, type=Path)
    args = parser.parse_args()
    legacy = args.legacy.resolve()
    if DEST.exists() or ROOT in legacy.parents or legacy == ROOT:
        raise ValueError("Use the explicit read-only legacy source and a new capsule")
    build = legacy / ".build/ios-jit"
    source = build / "launcher-runtime-everest-source/Everest"
    for name, pin in PINS.items():
        actual = subprocess.check_output(["git", "-C", str(source / name), "rev-parse", "HEAD"], text=True).strip()
        if actual != pin:
            raise ValueError("Source revision differs: " + name)
    DEST.mkdir(parents=True)
    manifest = {}

    def copy(src, name):
        dst = DEST / name
        if dst.exists():
            raise ValueError("Duplicate capsule path: " + str(name))
        if not src.is_file():
            raise ValueError("Missing required input: " + str(src))
        data = src.read_bytes()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        shutil.copymode(src, dst)
        digest = hashlib.sha256(data).hexdigest()
        if hashlib.sha256(dst.read_bytes()).hexdigest() != digest:
            raise ValueError("Copy differs")
        manifest[str(dst.relative_to(ROOT))] = {"bytes": len(data), "sha256": digest}

    def tree(src, name):
        for file in sorted(src.rglob("*")):
            if file.is_file():
                copy(file, Path(name) / file.relative_to(src))

    # Working source includes the recorded embedded/MonoMod hosting patches.
    # Git's tracked inventory excludes previous bin/obj outputs and caches.
    for name in PINS:
        repo = source / name
        tracked = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"]).decode().split("\0")
        for file in filter(None, tracked):
            if (repo / file).is_file():
                copy(repo / file, Path("source/Everest") / name / file)
    for name in ["source-receipt.json", "embedded-source-patch.json"]:
        copy(source.parent / name, Path("provenance") / name)
    for source_name, destination in [
        ("managed-runtime/dotnet-sdk-8.0.422", "sdk8"),
        ("hook-runtime/dotnet-sdk-9.0.300", "sdk9"),
        ("launcher-runtime-everest-dependencies/nuget", "nuget"),
        ("launcher-runtime-everest-game/orig", "orig"),
        ("celeste-game/touch-assets", "touch-assets"),
    ]:
        tree(build / source_name, destination)
    # Exact pre-platform inputs allow comparison of the new upstream patch.
    for name in ["Celeste.dll", "FNA.dll", "MMHOOK_Celeste.dll"]:
        copy(build / "launcher-runtime-everest-game/prepared" / name, Path("accepted-prepared") / name)
    copy(build / "graphics-managed/FNA.dll", "fna-before-everest.dll")
    # Existing host runtime and selected native dependencies, independent of iOS.
    tree(build / "managed-runtime/pack-osx-8.0.28/runtimes/osx-x64", "host/runtime")
    copy(build / "launcher-resolution-reflection/host/System.Private.CoreLib.dll", "host/reflection/System.Private.CoreLib.dll")
    copy(build / "sj-lobby-runtime/host/libmonosgen-2.0.a", "host/native/libmonosgen-2.0.a")
    for name in ["marshal-ilgen-static", "debugger-stub-static", "hot_reload-stub-static", "diagnostics_tracing-stub-static"]:
        filename = "libmono-component-" + name + ".a"
        copy(build / "managed-runtime/mono-build-host-coop/mono/mini" / filename, Path("host/native") / filename)
    for name, file in {"libFNA3D.0.dylib": "launcher-backbuffer-renderer/host/libFNA3D.0.dylib", "liblua54.dylib": "everest-lua/host/liblua54.dylib"}.items():
        copy(build / file, Path("host/native") / name)
    # Host-test libraries already copied into this historical test directory.
    for name in ["libSDL2-2.0.0.dylib", "libfmod.dylib", "libfmodstudio.dylib"]:
        copy(build / "launcher-catalogue-host-test" / name, Path("host/native") / name)
    (DEST / "manifest.json").write_text(json.dumps({"schema": 1, "pins": PINS, "files": manifest}, indent=2) + "\n")
    print("PINNED_LOADING_INPUTS", len(manifest), sum(v["bytes"] for v in manifest.values()), flush=True)


if __name__ == "__main__":
    main()
