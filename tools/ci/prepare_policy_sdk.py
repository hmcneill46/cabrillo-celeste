#!/usr/bin/env python3
"""Fetch only the hash-pinned .NET8 SDK needed by native CI's touch policy test."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def prepare(destination):
    destination = (ROOT / destination).absolute()
    if (destination.resolve() != destination or ROOT / '.build' not in destination.parents
            or destination.exists()):
        raise ValueError('Choose a fresh unaliased SDK directory under .build')
    arch = 'arm64' if platform.machine() == 'arm64' else 'x64'
    name = 'sdk8.0-osx-' + arch
    row = json.loads((ROOT / 'release/everest55-dependencies.json').read_text())['dependencies'][name]
    destination.parent.mkdir(parents=True, exist_ok=True)
    archive = destination.with_suffix('.tar.gz')
    with urllib.request.urlopen(row['url'], timeout=120) as response, archive.open('xb') as output:
        shutil.copyfileobj(response, output)
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha512').hexdigest() != row['sha512']:
            raise ValueError('Policy SDK download differs from its public pin')
    destination.mkdir()
    with tarfile.open(archive) as bundle:
        bundle.extractall(destination, filter='data')
    print('PASS_PINNED_POLICY_SDK', name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    prepare(parser.parse_args().output)
