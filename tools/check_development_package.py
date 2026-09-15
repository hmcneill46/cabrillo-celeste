#!/usr/bin/env python3
"""Run negative controls against an actual freshly built development IPA."""
import argparse
import json
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path

from build_development import ROOT, fresh_output, sha, write_json
from verify_development_build import APP_NAME, digest, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    verify(package)
    output = fresh_output(args.output, ".build")
    output.mkdir(parents=True)
    original = json.loads((package / "build-receipt.json").read_text())
    checks = {}
    prefix = "Payload/" + APP_NAME + ".app/"
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        temporary = Path(temporary)
        for mode, message in [
            ("historical_build_info", "Stale BuildInfo: build_number"),
            ("changed_managed_assembly", "Accepted managed payload changed"),
            ("changed_compiled_protocol", "Compiled protocol differs from BuildInfo"),
            ("mismatched_symbols", "dSYM does not match the executable"),
        ]:
            trial = temporary / mode
            trial.mkdir()
            receipt = json.loads(json.dumps(original))
            shutil.copyfile(package / "native-receipt.json", trial / "native-receipt.json")
            with zipfile.ZipFile(package / original["ipa"]) as source, zipfile.ZipFile(trial / original["ipa"], "w", zipfile.ZIP_DEFLATED) as target:
                for name in source.namelist():
                    data = source.read(name)
                    if mode == "historical_build_info" and name == prefix + "BuildInfo.json":
                        info = json.loads(data)
                        info["build_number"] = "28"
                        data = json.dumps(info).encode()
                    elif mode == "changed_managed_assembly" and name == prefix + "Managed/CelesteJITEverest.dll":
                        data = data[:-1] + bytes([data[-1] ^ 1])
                    elif mode == "changed_compiled_protocol" and name == prefix + APP_NAME:
                        data = bytearray(data)
                        marker = data.index(b"CJITM1\0\0")
                        struct.pack_into("<Q", data, marker + 8, 2)
                        data = bytes(data)
                        receipt["executable_sha256"] = digest(data)
                    target.writestr(name, data)
                    receipt["app_files"][name[len(prefix):]] = digest(data)
            receipt["ipa_sha256"] = sha(trial / receipt["ipa"])
            receipt["bytes"] = (trial / receipt["ipa"]).stat().st_size
            write_json(trial / "build-receipt.json", receipt)
            if mode == "mismatched_symbols":
                relative = APP_NAME + ".app.dSYM/Contents/Resources/DWARF/" + APP_NAME
                data = bytearray((package / relative).read_bytes())
                cursor = 32
                for _ in range(struct.unpack_from("<I", data, 16)[0]):
                    command, size = struct.unpack_from("<II", data, cursor)
                    if command == 0x1b:
                        data[cursor + 8] ^= 1
                        break
                    cursor += size
                dwarf = trial / relative
                dwarf.parent.mkdir(parents=True)
                dwarf.write_bytes(data)
            try:
                verify(trial)
            except ValueError as error:
                if str(error) != message:
                    raise RuntimeError(f"Wrong rejection for {mode}: {error}") from error
                checks[mode] = dict(status="PASS_REJECTED", reason=str(error), mutated_ipa_sha256=receipt["ipa_sha256"])
            else:
                raise RuntimeError("Accepted invalid package: " + mode)
    report = dict(status="PASS_DEVELOPMENT_PACKAGE_NEGATIVE_CONTROLS", checks=checks,
                  original_ipa_sha256=original["ipa_sha256"], source_sha256={str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__))})
    write_json(output / "results.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
