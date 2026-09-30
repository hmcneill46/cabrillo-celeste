#!/usr/bin/env python3
"""Verify public, pre-signed Shortcut documents against the deterministic generator.

Signing needs an iCloud account; verification needs only macOS's archive tools.
No Apple account, private key or keychain access is used here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import subprocess
import tempfile

from build_shortcut_files49 import generate

ROOT = Path(__file__).resolve().parents[1]
# Apple Root CA - G3, also present in the macOS system trust store.
APPLE_ROOT_SHA256 = '63343abfb89a6a03ebb57e9b3f5fa7be7c4f5c756f3017b3a8c488c3653e9179'


def run(*args, data=None):
    return subprocess.run(args, input=data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True, timeout=30).stdout


def check_contents(decoded, generated):
    # Observed changes made by Apple's signing tool. No action or connection is
    # normalized: every one must equal the generator's output.
    expected = dict(generated)
    expected.pop('WFWorkflowName')
    expected['WFWorkflowClientVersion'] = '4711'
    if decoded != expected:
        raise ValueError('Signed Shortcut contents differ from the public generator')


def check_members(members):
    if (len(members) != 2 or members[0].get('TYP') != 'D'
            or members[0].get('PAT') != '' or members[1].get('TYP') != 'F'
            or members[1].get('PAT') != 'Shortcut.wflow'
            or not 0 < members[1].get('DAT', 0) < 100000):
        raise ValueError('Unexpected signed Shortcut archive members')


def verify(assets):
    manifest = json.loads((assets / 'manifest.json').read_text())
    if (manifest.get('schema') != 1 or manifest.get('build') != 49
            or manifest.get('signed') is not True or manifest.get('app_minimum_build') != 48
            or manifest.get('callback_protocol') != 'cabrillo-39'
            or set(manifest['files']) != {'Standalone', 'LiveContainer'}):
        raise ValueError('Unexpected Shortcut manifest')
    results = {}
    for variant, host in [('Standalone', ''), ('LiveContainer', 'livecontainer')]:
        rows = manifest['files'][variant]
        if set(rows) != {'Cabrillo.shortcut', 'Cabrillo-unsigned.shortcut', 'Cabrillo.actions.json'}:
            raise ValueError('Unexpected Shortcut asset list')
        for name, row in rows.items():
            path = assets / variant / name
            if path.is_symlink() or path.resolve() != path.absolute():
                raise ValueError('Aliased Shortcut asset')
            data = path.read_bytes()
            if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('Shortcut document differs from its reviewed hash')
        expected = generate(host)
        if plistlib.loads((assets / variant / 'Cabrillo-unsigned.shortcut').read_bytes()) != expected:
            raise ValueError('Unsigned Shortcut differs from the public generator')
        signed = assets / variant / 'Cabrillo.shortcut'
        data = signed.read_bytes()
        if len(data) < 12 or data[:8] != b'AEA1\0\0\0\0':
            raise ValueError('Expected Apple signature-only archive profile')
        length = struct.unpack_from('<I', data, 8)[0]
        if not 0 < length < min(len(data) - 12, 16384):
            raise ValueError('Invalid Shortcut certificate header')
        auth = plistlib.loads(data[12:12 + length])
        certs = auth['SigningCertificateChain']
        if (set(auth) != {'SigningCertificateChain'} or len(certs) != 3
                or hashlib.sha256(certs[2]).hexdigest() != APPLE_ROOT_SHA256):
            raise ValueError('Unexpected Apple certificate chain')
        with tempfile.TemporaryDirectory(prefix='cabrillo-shortcut-') as directory:
            work = Path(directory)
            for index, cert in enumerate(certs):
                (work / f'{index}.pem').write_bytes(run('openssl', 'x509', '-inform', 'DER',
                    '-outform', 'PEM', data=cert))
            run('openssl', 'verify', '-CAfile', str(work / '2.pem'), '-untrusted',
                str(work / '1.pem'), str(work / '0.pem'))
            public_key = run('openssl', 'x509', '-inform', 'DER', '-pubkey', '-noout', data=certs[0])
            (work / 'public.pem').write_bytes(public_key)
            run('/usr/bin/aea', 'decrypt', '-i', str(signed), '-o', str(work / 'document.aar'),
                '-sign-pub', str(work / 'public.pem'))
            members = json.loads(run('/usr/bin/aa', 'list', '-i', str(work / 'document.aar'),
                                     '-list-format', 'json'))
            check_members(members)
            run('/usr/bin/aa', 'extract', '-i', str(work / 'document.aar'), '-d', str(work / 'decoded'))
            check_contents(plistlib.loads((work / 'decoded/Shortcut.wflow').read_bytes()), expected)
        results[variant] = rows['Cabrillo.shortcut']['sha256']
    return dict(status='PASS_SIGNED_SHORTCUT_SOURCE_MATCH', revision=49,
                signatures_verified=True, actions_match_generated_source=True,
                apple_account_required=False, assets_sha256=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(ROOT / 'release/shortcuts49')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
