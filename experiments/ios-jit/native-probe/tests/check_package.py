#!/usr/bin/env python3
"""Check corrected IPA packaging against the real archive that triggered signing errors."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

source = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(source))
from build import validate_payload_members

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--previous-ipa', type=Path, required=True)
parser.add_argument('--ipa', type=Path, required=True)
args = parser.parse_args()


def members(path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        return [(name, archive.read(name)) for name in archive.namelist()]


def text_section(binary):
    assert binary[:4] == b'\xcf\xfa\xed\xfe'
    command = 32
    for _ in range(struct.unpack_from('<I', binary, 16)[0]):
        kind, length = struct.unpack_from('<II', binary, command)
        assert length >= 8 and command + length <= len(binary)
        if kind == 0x19:
            for index in range(struct.unpack_from('<I', binary, command + 64)[0]):
                section = command + 72 + index * 80
                name = binary[section:section + 16].rstrip(b'\0')
                segment = binary[section + 16:section + 32].rstrip(b'\0')
                if name == b'__text' and segment == b'__TEXT':
                    _, size, offset = struct.unpack_from('<QQI', binary, section + 32)
                    assert offset + size <= len(binary)
                    return binary[offset:offset + size]
        command += length
    raise AssertionError('Executable has no __TEXT,__text section')


previous = members(args.previous_ipa)
current = members(args.ipa)
try:
    validate_payload_members(previous)
except ValueError as error:
    assert 'Debug-symbol bundle' in str(error)
else:
    raise AssertionError('Guard failed to reject the known-bad IPA')

# Renaming the directory must not hide the actual debug-only Mach-O file.
dwarf = next(data for name, data in previous if '.dSYM/Contents/Resources/DWARF/' in name)
try:
    validate_payload_members([('Resources/renamed-symbol-file', dwarf)])
except ValueError as error:
    assert 'MH_DSYM' in str(error)
else:
    raise AssertionError('Guard failed to reject renamed debug symbols')

validate_payload_members(current)
executable = 'Payload/CelesteJITProbe.app/CelesteJITProbe'
macho = [(name, struct.unpack_from('<I', data, 12)[0]) for name, data in current
         if data[:4] == b'\xcf\xfa\xed\xfe']
assert macho == [(executable, 2)], macho
assert not any('_CodeSignature' in name or name.endswith('embedded.mobileprovision') for name, _ in current)
old_text = text_section(dict(previous)[executable])
new_text = text_section(dict(current)[executable])
assert old_text == new_text, 'Packaging correction unexpectedly changed executable instructions'
result = {'status': 'PASS_PACKAGING_REGRESSION', 'known_bad_ipa_rejected': True,
          'renamed_mh_dsym_rejected': True, 'corrected_ipa_accepted': True,
          'payload_macho_files': [{'path': n, 'filetype': t} for n, t in macho],
          'native_text_matches_previous_build': True,
          'native_text_sha256': hashlib.sha256(new_text).hexdigest(),
          'previous_ipa_sha256': hashlib.sha256(args.previous_ipa.read_bytes()).hexdigest(),
          'corrected_ipa_sha256': hashlib.sha256(args.ipa.read_bytes()).hexdigest(),
          'physical_installation_of_corrected_ipa': 'NOT_TESTED'}
print(json.dumps(result, indent=2))
