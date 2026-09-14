#!/usr/bin/env python3
"""Compile and inspect the JIT26 arm64 call ABI; never run it or enable JIT."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    source = Path(__file__).resolve().with_name("jit26_protocol_abi.c")
    repo = source.parents[3]
    output = repo / ".build/ios-jit/audit/protocol-abi"
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("DEVELOPER_DIR", "/Applications/Xcode-26.6.app/Contents/Developer")

    def run(*args):
        return subprocess.run(args, env=env, check=True, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

    xcode = run("xcodebuild", "-version")
    sdk = run("xcrun", "--sdk", "iphoneos", "--show-sdk-path")
    sdk_version = run("xcrun", "--sdk", "iphoneos", "--show-sdk-version")
    obj = output / "jit26_protocol_abi.o"
    run("xcrun", "--sdk", "iphoneos", "clang", "-target", "arm64-apple-ios26.0",
        "-isysroot", sdk, "-O2", "-Wall", "-Wextra", "-Werror",
        "-c", str(source), "-o", str(obj))
    disassembly = run("xcrun", "otool", "-tvV", str(obj))
    (output / "disassembly.txt").write_text(disassembly + "\n")

    for name, command in (("CelesteJit26PrepareRegion", 1), ("CelesteJit26Detach", 0)):
        match = re.search(r"_" + name + r":\n(.*?)(?=\n_\w+:|\Z)", disassembly, re.S)
        if not match:
            raise RuntimeError(f"Missing disassembly for {name}")
        instructions = []
        for line in match.group(1).splitlines():
            decoded = re.match(r"^[0-9a-f]+\s+(.*)", line.strip())
            if decoded:
                instructions.append(re.sub(r"\s+", "", decoded.group(1)).lower())
        wanted = [f"movx16,#0x{command:x}", "brk#0xf00d", "ret"]
        if instructions[:3] != wanted or any(i != "nop" for i in instructions[3:]):
            raise RuntimeError(f"Unexpected ABI in {name}: {instructions}")

    receipt = {
        "schemaVersion": 1,
        "result": "PASS_COMPILE_AND_DISASSEMBLY_ONLY",
        "xcode": xcode.splitlines(),
        "sdk": sdk_version,
        "target": "arm64-apple-ios26.0",
        "source": source.relative_to(repo).as_posix(),
        "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "objectSha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
        "verified": ["x16 command selector", "brk immediate 0xf00d",
                     "no prologue or argument-register clobber", "ret instruction"],
        "deviceExecution": False,
        "jitAllocatorImplemented": False,
        "managedRuntimeBuilt": False,
        "ipaProduced": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
