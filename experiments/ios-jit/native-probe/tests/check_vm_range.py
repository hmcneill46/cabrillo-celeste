#!/usr/bin/env python3
"""Host regression tests for multi-entry VM range coverage, with ASan/UBSan."""
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[4]
source = Path(__file__).resolve().parents[1]
out = root / ".build/ios-jit/native-probe/vm-range-tests"
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode-26.6.app/Contents/Developer")
exe = out / "vm_range_test"
command = ["xcrun", "--sdk", "macosx", "clang", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
           "-fsanitize=address,undefined", "-fno-omit-frame-pointer", str(source / "tests/vm_range_test.c"),
           str(source / "src/VMRange.c"), str(source / "src/VMRangeDarwin.c"), "-o", str(exe)]
subprocess.run(command, env=env, check=True)
result = subprocess.run([str(exe)], env=env, check=True, text=True, capture_output=True)
print(result.stdout, end="")
(out / "test.log").write_text(result.stdout + result.stderr)
receipt = json.loads(result.stdout.splitlines()[-1])
receipt.update({"status": "PASS_HOST_VM_RANGE_REGRESSION", "sanitizers": ["address", "undefined"], "includes_real_darwin_fragmented_map": True})
(out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
