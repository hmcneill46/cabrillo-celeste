#!/usr/bin/env python3
"""Check a cooperative loading package, preserved dependencies and matching symbols."""
import argparse
import datetime
import hashlib
import json
import plistlib
import struct
import zipfile
from loading_inputs import validate_managed, REPLACEMENTS
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/ios-jit/launcher-loading-release"
APP_NAME = "CelesteJITEverest"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def macho(data, executable=False):
    require(len(data) >= 32, "Truncated Mach-O")
    magic, cpu, _, filetype, count, command_bytes = struct.unpack_from("<6I", data)
    require(magic == 0xfeedfacf and cpu == 0x100000c, "Expected arm64 Mach-O")
    require(command_bytes <= len(data) - 32, "Truncated Mach-O commands")
    cursor, uuids, builds, dylibs = 32, [], [], []
    for _ in range(count):
        require(cursor + 8 <= 32 + command_bytes, "Truncated load command")
        command, size = struct.unpack_from("<II", data, cursor)
        require(size >= 8 and size % 8 == 0 and cursor + size <= 32 + command_bytes, "Invalid load command size")
        require(command != 0x1d, "Embedded Mach-O signature")
        if command == 0x1b:
            require(size == 24, "Invalid UUID command")
            uuids.append(data[cursor + 8:cursor + 24].hex())
        if command == 0x32:
            require(size >= 24, "Invalid build-version command")
            builds.append(struct.unpack_from("<3I", data, cursor + 8))
        if command in {0xc, 0x80000018, 0x8000001f}:
            require(size >= 24, "Invalid library command")
            offset = struct.unpack_from("<I", data, cursor + 8)[0]
            require(24 <= offset < size, "Invalid library name offset")
            name = data[cursor + offset:cursor + size].split(b"\0", 1)[0].decode()
            dylibs.append(name)
        cursor += size
    require(cursor == 32 + command_bytes and len(uuids) == 1, "Invalid Mach-O command count/UUID")
    if executable:
        require(filetype == 2 and builds == [(2, 0x1a0000, 0x1a0500)], "Expected iOS 26.0 / SDK 26.5 executable")
        require(all(n.startswith(("/System/Library/", "/usr/lib/", "@rpath/libswift")) for n in dylibs), "Unbundled native dependency")
    return uuids[0]


def compiled_protocol(data):
    """Read the native request constants from __TEXT,__cjprotocol."""
    cursor, records = 32, []
    count, command_bytes = struct.unpack_from("<2I", data, 16)
    for _ in range(count):
        command, size = struct.unpack_from("<II", data, cursor)
        require(size >= 8 and cursor + size <= 32 + command_bytes <= len(data), "Invalid protocol load command")
        if command == 0x19:
            require(size >= 72, "Truncated segment")
            sections = struct.unpack_from("<I", data, cursor + 64)[0]
            require(72 + sections * 80 <= size, "Truncated section headers")
            for i in range(sections):
                section, segment, _, length, offset = struct.unpack_from("<16s16sQQI", data, cursor + 72 + i * 80)
                if section.rstrip(b"\0") == b"__cjprotocol":
                    require(segment.rstrip(b"\0") == b"__TEXT" and length == 48 and offset + length <= len(data), "Invalid protocol section")
                    records.append(struct.unpack_from("<8s5Q", data, offset))
        cursor += size
    require(len(records) == 1 and records[0][0] == b"CJITM1\0\0", "Missing or duplicate compiled protocol")
    _, version, length, mailbox, response, error = records[0]
    return dict(protocol=version, bytes_per_arena=length, arena_count=2,
                mailbox_bytes=mailbox, response_offset=response, error_offset=error)


def verify(directory):
    receipt = json.loads((directory / "build-receipt.json").read_text())
    managed, overlay = validate_managed(directory / "managed-receipt.json")
    payload = json.loads((SOURCE / "ManagedPayload.json").read_text())
    require(digest((directory / "managed-receipt.json").read_bytes()) == payload["receipt_sha256"] and managed["resources"] == payload["resources"], "Changed build31 managed dependency")
    identity = json.loads((SOURCE / "BuildIdentity.json").read_text())
    lock = json.loads((SOURCE / "Dependencies.json").read_text())
    require(receipt["build"] == identity, "Unexpected development identity")
    require(Path(receipt["ipa"]).name == receipt["ipa"], "Invalid IPA name")
    ipa = directory / receipt["ipa"]
    require(digest(ipa.read_bytes()) == receipt["ipa_sha256"] and ipa.stat().st_size == receipt["bytes"], "IPA hash/size mismatch")
    require(receipt["ipa_sha256"] != lock["baseline_ipa_sha256"], "Unexpected historical IPA")
    for key in ["historical_uuid_restoration", "historical_package_metadata_replayed", "original_executable_copied", "device_tested"]:
        require(receipt[key] is False, "Unexpected preparation claim: " + key)
    require(receipt["managed_rebuilt"] is True, "Managed loading changes were not built")
    for name, expected in receipt["source_sha256"].items():
        path = ROOT / name
        require(ROOT in path.resolve().parents and not path.is_symlink(), "Source outside Cabrillo")
        require(digest(path.read_bytes()) == expected, "Source changed since compilation: " + name)
    prefix = "Payload/" + APP_NAME + ".app/"
    with zipfile.ZipFile(ipa) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and archive.testzip() is None, "Duplicate entry or ZIP CRC failure")
        require(set(names) == {prefix + n for n in receipt["app_files"]}, "Package entry set differs")
        require(not any(".dSYM" in n or "_CodeSignature" in n or "embedded.mobileprovision" in n or ".." in Path(n).parts for n in names), "Invalid package contents")
        for name, expected in receipt["app_files"].items():
            require(digest(archive.read(prefix + name)) == expected, "Package file changed: " + name)
        info = json.loads(archive.read(prefix + "BuildInfo.json"))
        settings = plistlib.loads(archive.read(prefix + "Info.plist"))
        for key, value in identity.items():
            require(info[key] == value, "Stale BuildInfo: " + key)
        require(settings["CFBundleIdentifier"] == "io.github.hmcneill46.celeste.everest.jit.everest", "Guest bundle identifier changed")
        require(settings["CFBundleExecutable"] == APP_NAME and settings["CFBundleName"] == APP_NAME, "Guest executable identity changed")
        require(settings["CFBundleVersion"] == identity["build_number"] and settings["CFBundleShortVersionString"] == identity["version"], "Stale version")
        require(settings["CFBundleDisplayName"] == "Cabrillo" and settings["UIDeviceFamily"] == [1, 2], "Display name/device family changed")
        require(info["created_utc"] == receipt["actual_created_utc"], "BuildInfo date differs from fresh compilation")
        require(datetime.datetime.fromisoformat(info["created_utc"]) > datetime.datetime(2026, 9, 14, tzinfo=datetime.timezone.utc), "Historical build date")
        require(info["source_sha256"] == receipt["source_sha256"], "Stale source receipt")
        native_digest = digest((directory / "native-receipt.json").read_bytes())
        require(native_digest == receipt["native_receipt_sha256"] == info["launcher_native_receipt_sha256"], "Stale native receipt")
        native = json.loads((directory / "native-receipt.json").read_text())
        require(native["source_sha256"] == receipt["source_sha256"] and native["compiled_source_count"] == receipt["compiled_source_count"], "Native compilation provenance differs")
        require(info["compiled_protocol"] == dict(protocol=1, bytes_per_arena=268435456, arena_count=2,
            mailbox_bytes=96, response_offset=48, error_offset=88), "Changed JIT protocol metadata")
        managed_digest = digest((directory / "managed-receipt.json").read_bytes())
        require(managed_digest == receipt["managed_receipt_sha256"] == info["managed_build_receipt_sha256"], "Stale managed receipt")
        resource_root = ROOT / lock["resource_root"]
        expected_managed = {n[len("Managed/"):]: h for n, h in managed["resources"].items() if n.startswith("Managed/")}
        actual_managed = {n[len(prefix + "Managed/"):]: digest(archive.read(n)) for n in names if n.startswith(prefix + "Managed/")}
        require(expected_managed == actual_managed == info["reused_dependencies"]["managed_sha256"], "Verified loading managed payload changed")
        require(sum(n.endswith(".dll") for n in actual_managed) == 201, "Managed assembly count changed")
        for name in ["RuntimeIdentity.json", "CompatibilityDownloads.json", "RuntimeCompatibleReleases.json", "THIRD_PARTY_NOTICES.md"]:
            require(archive.read(prefix + name) == (SOURCE / name).read_bytes(), "Stale lane resource: " + name)
        for path in resource_root.rglob("*"):
            name = str(path.relative_to(resource_root))
            if path.is_file() and name not in REPLACEMENTS | {"BuildInfo.json", "RuntimeIdentity.json", "CompatibilityDownloads.json", "RuntimeCompatibleReleases.json", "THIRD_PARTY_NOTICES.md"}:
                require(archive.read(prefix + name) == path.read_bytes(), "Reused resource changed: " + name)
        executable = archive.read(prefix + APP_NAME)
        require(digest(executable) == receipt["executable_sha256"], "Executable receipt differs")
        uuid = macho(executable, executable=True)
        require(compiled_protocol(executable) == info["compiled_protocol"], "Compiled protocol differs from BuildInfo")
        require(uuid != lock["baseline_executable_uuid"], "Historical executable UUID reused")
    dwarf = directory / (APP_NAME + ".app.dSYM/Contents/Resources/DWARF/" + APP_NAME)
    require(macho(dwarf.read_bytes()) == uuid, "dSYM does not match the executable")
    return dict(status="PASS_NEW_BUILD_PACKAGE_AND_SYMBOLS", build_id=identity["build_id"],
        ipa_sha256=receipt["ipa_sha256"], bytes=receipt["bytes"], executable_uuid=uuid,
        compiled_source_count=receipt["compiled_source_count"], managed_assemblies=201, rebuilt_managed_assemblies=4, preserved_managed_assemblies=197,
        unsigned=True, symbols_outside_ipa=True, device_tested=False, cooperative_loading_implemented=True, uninterruptible_step_limit=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify(args.directory.resolve())
    (args.directory / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
