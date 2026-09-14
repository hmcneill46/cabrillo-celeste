#!/usr/bin/env python3
"""Fresh native catalogue/installer regression, using only Cabrillo inputs and Xcode."""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".build/catalogue-check")
    parser.add_argument("--live", action="store_true", help="Also exercise live services and install two small mods into an isolated host fixture")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if ROOT not in output.parents or output.exists():
        raise RuntimeError("Choose a new --output directory inside Cabrillo")
    fixtures = ROOT / ".private/test-inputs"
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    for name, row in json.loads((fixtures / "inputs.json").read_text()).items():
        if digest(ROOT / name) != row["sha256"]:
            raise RuntimeError("Changed test input: " + name)
    output.mkdir(parents=True)
    native = output / "native"
    native.mkdir()
    results = output / "results"
    results.mkdir()
    env = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode-26.6.app/Contents/Developer", CLANG_MODULE_CACHE_PATH=str(output / "module-cache"))
    commands = []

    def run(command):
        command = list(map(str, command))
        commands.append(command)
        with (output / "check.log").open("a") as log:
            log.write(repr(command) + "\n"); log.flush()
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        if result.returncode:
            raise RuntimeError("Check failed; see " + str(output / "check.log"))

    zip_sources = sorted((ROOT / "vendor/ZIPFoundation/Sources/ZIPFoundation").glob("*.swift"))
    run(["xcrun", "swiftc", "-swift-version", "5", "-O", "-module-name", "ZIPFoundation", "-emit-library", "-static", "-emit-module", "-emit-module-path", native / "ZIPFoundation.swiftmodule", "-o", native / "libZIPFoundation.a", *zip_sources])
    yaml = ROOT / "vendor/Yams/Sources/CYaml"
    yaml_sources = sorted((yaml / "src").glob("*.c"))
    objects = []
    for source in yaml_sources:
        obj = native / (source.stem + ".o")
        run(["xcrun", "clang", "-DYAML_DECLARE_STATIC", "-O2", "-I" + str(yaml / "include"), "-c", source, "-o", obj])
        objects.append(obj)
    run(["xcrun", "libtool", "-static", "-o", native / "libCYaml.a", *objects])
    source = ROOT / "experiments/ios-jit/launcher-catalogue"
    swift = sorted((source / "native").glob("*.swift")) + [source / "tests/CatalogueTests.swift"]
    run(["xcrun", "swiftc", "-swift-version", "5", "-O", "-g", "-I", native, "-I", yaml / "include", *swift, native / "libZIPFoundation.a", native / "libCYaml.a", "-o", output / "catalogue-tests"])
    run([output / "catalogue-tests", results, fixtures / "catalogue", fixtures / "install", *(["--live"] if args.live else [])])
    result = json.loads((results / "results.json").read_text())
    if result["status"] != "PASS_NATIVE_CATALOGUE_CONTRACT_CACHE_INSTALLS":
        raise RuntimeError("Unexpected test result")
    receipt = dict(status=result["status"], actual_created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), check_count=len(result["checks"]), live=args.live, source_sha256={str(p.relative_to(ROOT)):digest(p) for p in zip_sources + yaml_sources + swift + [Path(__file__)]}, results_sha256=digest(results / "results.json"), commands=commands)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(receipt["status"], receipt["check_count"], "checks")


if __name__ == "__main__":
    main()
