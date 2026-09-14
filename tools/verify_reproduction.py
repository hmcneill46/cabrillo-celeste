#!/usr/bin/env python3
"""Independently verify the complete reproduced build28 package and its symbols."""
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path
from macho_identity import reproduce_uuid, uuid_range

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    meta = json.loads((ROOT / ".private/migration/build28-replay.json").read_text())
    expected_hash = "87db3cf1936fc3a0253cbddbe6cb40466f024a1bbe98dcda93d7efd5c2bbcea2"
    ipa = directory / "CelesteJITEverest-unsigned.ipa"
    digest = hashlib.sha256(ipa.read_bytes()).hexdigest()
    if digest != expected_hash or ipa.stat().st_size != 23812187:
        raise RuntimeError("IPA is not the exact delivered build28")
    with zipfile.ZipFile(ipa) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        prefix = "Payload/CelesteJITEverest.app/"
        expected_names = {prefix + row["name"] for row in meta["entries"]}
        if len(archive.namelist()) != len(expected_names) or set(archive.namelist()) != expected_names:
            raise RuntimeError("Unexpected or duplicate package entries")
        for row in meta["entries"]:
            if hashlib.sha256(archive.read(prefix + row["name"])).hexdigest() != row["sha256"]:
                raise RuntimeError("Changed package entry: " + row["name"])
        executable = archive.read(prefix + "CelesteJITEverest")
        if any(".dSYM/" in name or "_CodeSignature/" in name for name in expected_names):
            raise RuntimeError("Symbols or signature inside IPA")
    # Check the Mach-O itself, not just the absence of a signature directory.
    count = struct.unpack_from("<I", executable, 16)[0]
    cursor = 32
    for _ in range(count):
        command, size = struct.unpack_from("<II", executable, cursor)
        if command == 0x1d:
            raise RuntimeError("Unexpected embedded code signature")
        cursor += size
    start, end = uuid_range(executable)
    dwarf = (directory / "CelesteJITEverest.app.dSYM/Contents/Resources/DWARF/CelesteJITEverest").read_bytes()
    d0, d1 = uuid_range(dwarf)
    if executable[start:end] != dwarf[d0:d1]:
        raise RuntimeError("Executable and dSYM identities differ")
    changed_uuid = executable[:start] + bytes(16) + executable[end:]
    if reproduce_uuid(changed_uuid, meta["executable_identity"]) != executable:
        raise RuntimeError("UUID-only reproduction failed")
    changed_code = bytearray(executable)
    changed_code[8192] ^= 1
    try:
        reproduce_uuid(bytes(changed_code), meta["executable_identity"])
    except ValueError:
        pass
    else:
        raise RuntimeError("Changed executable code was accepted")
    receipt = dict(status="PASS_EXACT_PACKAGE_AND_UUID_CONTROLS", ipa_sha256=digest, bytes=ipa.stat().st_size, entries=len(expected_names), executable_uuid=executable[start:end].hex(), unsigned=True, symbols_outside_ipa=True, altered_code_rejected=True)
    (directory / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
