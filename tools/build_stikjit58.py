#!/usr/bin/env python3
"""Build the pinned helper, then bind its version to the combined build58 host."""
import argparse
import json
from pathlib import Path
import plistlib

import build_stikjit57 as retained

ROOT = retained.ROOT
IDENTITY = ROOT / 'release/app58/BuildIdentity.json'


def validate_receipt(path):
    value = retained.validate_receipt(path)
    identity = json.loads(IDENTITY.read_text())
    settings = plistlib.loads((ROOT / value['helper'] / 'Info.plist').read_bytes())
    if (settings.get('CFBundleVersion') != identity['build_number']
            or settings.get('CFBundleShortVersionString') != identity['version']
            or value.get('host_identity_sha256') != retained.sha(IDENTITY)
            or value['source_sha256'].get(str(Path(__file__).relative_to(ROOT))) != retained.sha(Path(__file__))):
        raise ValueError('Helper does not match the build58 host')
    return value


def build(work, archive=None):
    retained.build(work, archive)
    receipt = work / 'receipt.json'
    value = retained.validate_receipt(receipt)
    identity = json.loads(IDENTITY.read_text())
    settings_path = ROOT / value['helper'] / 'Info.plist'
    settings = plistlib.loads(settings_path.read_bytes())
    settings.update(CFBundleVersion=identity['build_number'],
                    CFBundleShortVersionString=identity['version'])
    settings_path.write_bytes(plistlib.dumps(settings, fmt=plistlib.FMT_BINARY))
    value['files']['CabrilloJITHelper.appex/Info.plist'] = retained.sha(settings_path)
    value['source_sha256'].update({str(p.relative_to(ROOT)): retained.sha(p)
                                  for p in [IDENTITY, Path(__file__)]})
    value['host_identity_sha256'] = retained.sha(IDENTITY)
    retained.write_json(receipt, value)
    validate_receipt(receipt)
    print('PASS_BUILD58_HELPER_IDENTITY', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    build(retained.safe_work(args.work), args.archive)
