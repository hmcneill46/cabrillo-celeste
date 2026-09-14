#!/usr/bin/env python3
"""One-time, read-only import of the JIT lane and the build28 dependency capsule."""
import argparse
import hashlib
import json
import plistlib
import shutil
import zipfile
from pathlib import Path
from macho_identity import uuid_range, without_uuid_hash

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    assert source != ROOT and not (ROOT / ".private/migration/import.json").exists()
    artifact = source / "artifacts/ios-jit/launcher-catalogue-20260913-28"
    build = json.loads((artifact / "build-receipt.json").read_text())
    ipa = artifact / "CelesteJITEverest-unsigned.ipa"
    assert sha(ipa) == build["ipa_sha256"] == "87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2"
    inventory, inputs, aliases = {}, {}, {}

    def copy(path, dest, reason, private=False, logical=None):
        path, dest = Path(path), ROOT / dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            assert sha(dest) == sha(path), dest
        else:
            shutil.copy2(path, dest)
        row = dict(sha256=sha(dest), bytes=dest.stat().st_size, reason=reason)
        inventory[str(dest.relative_to(ROOT))] = row
        if private:
            inputs[str(dest.relative_to(ROOT))] = row
        if logical:
            aliases[logical] = str(dest.relative_to(ROOT))

    def tree(path, dest, reason, private=False):
        for p in sorted(path.rglob("*")):
            if p.is_file() and not {"__pycache__", ".git", ".DS_Store"}.intersection(p.parts):
                copy(p, Path(dest) / p.relative_to(path), reason, private)

    tree(source / "experiments/ios-jit", "experiments/ios-jit", "JIT implementation, runtime patches, regression fixtures or versioned implementation history")
    tree(source / "docs/ios-jit", "docs/ios-jit", "JIT architecture, research, implementation and acceptance record")
    copy(source / "AGENTS.md", "docs/history/LEGACY_AGENTS_BUILD28.md", "Historical development constraints and accepted-build evidence")
    copy(source / "LICENSE", "LICENSE", "Inherited project license and attribution")
    reused = ["modern-ios/CelesteIOSFoundation/TouchControlsPolicy.cs", "modern-ios/CelesteIOSFoundation/PlatformPolicies.cs", "scripts/generate-ios-touch-assets.py", "scripts/finalize-apple-archive.py", "modern-ios/Assets/TouchControls/NOTICE.md"]
    reused += [str(p.relative_to(source)) for p in (source / "modern-ios/Assets/TouchControls/Source").glob("*.svg")]
    for name in reused:
        copy(source / name, name, "Proven shared control policy/artwork or native archive utility used by the JIT lane; no AOT app/project")

    native = json.loads((artifact / "launcher-native-receipt.json").read_text())
    for logical in native["source_sha256"]:
        if logical.startswith(".build/ios-jit/launcher-catalogue-native-dependencies/"):
            relative = logical.split("launcher-catalogue-native-dependencies/", 1)[1]
            copy(source / logical, "vendor/" + relative, "Pinned ZIP or YAML parser source compiled into the native launcher", logical=logical)
    for dependency in ["ZIPFoundation", "Yams"]:
        base = source / ".build/ios-jit/launcher-catalogue-native-dependencies" / dependency
        for p in base.glob("LICENSE*"):
            copy(p, Path("vendor") / dependency / p.name, "Vendored dependency license")
    for logical, digest in build["native_library_sha256"].items():
        assert sha(source / logical) == digest
        copy(source / logical, ".private/inputs/" + logical, "Accepted pinned JIT runtime, graphics/audio or FMOD link dependency", True, logical)
    for logical in [".build/ios-jit/game-native-output/SDL2.xcframework/ios-arm64/Headers", ".build/ios-jit/managed-runtime/pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0"]:
        path = source / logical
        tree(path, ".private/inputs/" + logical, "Headers matching the pinned SDL or Mono native archive", True)
        aliases[logical] = ".private/inputs/" + logical
    pre = "Payload/CelesteJITEverest.app/"
    entries = []
    with zipfile.ZipFile(ipa) as archive:
        for z in archive.infolist():
            assert z.filename.startswith(pre)
            name = z.filename[len(pre):]
            assert name and not z.is_dir()
            data = archive.read(z)
            if name == "CelesteJITEverest":
                start, end = uuid_range(data)
                executable_identity = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), uuid_hex=data[start:end].hex(), without_uuid_sha256=without_uuid_hash(data))
            entries.append(dict(name=name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), date_time=z.date_time, compress_type=z.compress_type, create_system=z.create_system, create_version=z.create_version, extract_version=z.extract_version, flag_bits=z.flag_bits, volume=z.volume, internal_attr=z.internal_attr, external_attr=z.external_attr, extra=z.extra.hex(), comment=z.comment.hex()))
            if name == "Info.plist":
                bundle_settings = plistlib.loads(data)
            # Rebuild all launcher/native code and compiled icon assets. Never import the executable.
            if name == "CelesteJITEverest" or name == "Info.plist" or name == "Assets.car" or name.startswith("AppIcon"):
                continue
            dest = ROOT / ".private/resources/build28" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            reason = "Frozen accepted managed runtime/game IL dependency" if name.startswith("Managed/") else "Exact build28 resource or historical embedded provenance for byte reproduction"
            row = dict(sha256=sha(dest), bytes=len(data), reason=reason)
            inputs[str(dest.relative_to(ROOT))] = row
            inventory[str(dest.relative_to(ROOT))] = row
    # The reference is metadata only; there is no prebuilt app/executable/IPA in the capsule.
    metadata = dict(schema=1, canonical_root=str(source), build=build, native=native, entries=entries, bundle_settings=bundle_settings, aliases=aliases, native_object_mtimes={}, executable_identity=executable_identity)
    stages = [source / ".build/ios-jit/launcher-catalogue/launcher-catalogue-20260913-28", source / ".build/ios-jit/launcher-catalogue-native/ios"]
    for stage in stages:
        for p in stage.glob("*.o"):
            metadata["native_object_mtimes"][str(p.relative_to(source))] = p.stat().st_mtime
    private = ROOT / ".private/migration"
    private.mkdir(parents=True, exist_ok=True)
    (private / "build28-replay.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (private / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (private / "import.json").write_text(json.dumps(dict(source=str(source), destination=str(ROOT), source_ipa_sha256=sha(ipa), source_ipa_bytes=ipa.stat().st_size, input_files=len(inputs), input_bytes=sum(x["bytes"] for x in inputs.values()), no_original_executable_imported=True), indent=2) + "\n")
    public = {p:v for p,v in inventory.items() if not p.startswith(".private/")}
    (ROOT / "docs/MIGRATION_FILE_INVENTORY.json").write_text(json.dumps(dict(schema=1, files=public, private_categories=dict(pinned_native_dependencies=True, accepted_managed_payload=True, headers=True, historical_packaging_metadata=True), private_inputs_ignored_by_git=True), indent=2) + "\n")
    fixtures = {}
    for group, base, names in [
        ("catalogue", source / ".build/ios-jit/launcher-catalogue-service", ["community-downloads.json", "community-spring.json", "community-categories.json", "community-subcategories.yaml", "spring-profile.json"]),
        ("install", source / ".build/ios-jit/launcher-catalogue-install-tests/fixtures", ["candidates.json", "root.zip", "helper-old.zip", "helper-new.zip", "leaf-new.zip", "helper-repacked.zip"]),
    ]:
        for name in names:
            dest = ROOT / ".private/test-inputs" / group / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(base / name, dest)
            fixtures[str(dest.relative_to(ROOT))] = dict(sha256=sha(dest), bytes=dest.stat().st_size, source=str(base / name), reason="Dated public service response or synthetic mod fixture for native regression testing")
    (ROOT / ".private/test-inputs/inputs.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    print(json.dumps(dict(public_files=len(public), public_bytes=sum(x["bytes"] for x in public.values()), private_files=len(inputs), private_bytes=sum(x["bytes"] for x in inputs.values()), copied_original_executable=False), indent=2))


if __name__ == "__main__":
    main()
