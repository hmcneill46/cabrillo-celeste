#!/usr/bin/env python3
"""Cross-assemble emitter instructions and check bytes; no device execution."""
import json
import os
from pathlib import Path
import struct
import subprocess

root = Path(__file__).resolve().parents[4]
output = root / ".build/ios-jit/native-probe/arm64-encodings"
output.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode-26.6.app/Contents/Developer")

def run(args):
    return subprocess.check_output(args, env=env, text=True)

assembly = output / "encodings.s"
assembly.write_text(""".text
.p2align 2
.globl _CJEncodingCheck
_CJEncodingCheck:
movz w0, #12345
ret
add w0, w0, #7
ret
ldr x16, 1f
br x16
1: .quad 0x120010000
""")
obj = output / "encodings.o"
sdk = run(["xcrun", "--sdk", "iphoneos", "--show-sdk-path"]).strip()
run(["xcrun", "clang", "-target", "arm64-apple-ios26.0", "-isysroot", sdk, "-c", str(assembly), "-o", str(obj)])
data = obj.read_bytes()
magic, _, _, _, count, _, _, _ = struct.unpack_from("<8I", data)
assert magic == 0xfeedfacf
cursor = 32
section = None
for _ in range(count):
    command, length = struct.unpack_from("<II", data, cursor)
    if command == 0x19:
        sections = struct.unpack_from("<I", data, cursor + 64)[0]
        for index in range(sections):
            offset = cursor + 72 + index * 80
            name, segment, _, size, file_offset = struct.unpack_from("<16s16sQQI", data, offset)
            if name.rstrip(b"\0") == b"__text" and segment.rstrip(b"\0") == b"__TEXT":
                section = data[file_offset:file_offset + size]
    cursor += length
expected = struct.pack("<6IQ", 0x52800000 | (12345 << 5), 0xd65f03c0,
                       0x11001c00, 0xd65f03c0, 0x58000050, 0xd61f0200, 0x120010000)
assert section == expected, (section, expected)
disassembly = run(["xcrun", "otool", "-tvV", str(obj)])
(output / "disassembly.txt").write_text(disassembly)
receipt = {"status": "PASS_CROSS_ASSEMBLER_BYTES", "bytes": expected.hex(),
           "instructions": ["movz w0,#12345", "ret", "add w0,w0,#7", "ret", "ldr x16,PC+8", "br x16"],
           "device_execution": "NOT TESTED"}
(output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
