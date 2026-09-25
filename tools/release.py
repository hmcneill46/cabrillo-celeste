#!/usr/bin/env python3
"""Gate and package a public source build; the current private IPA is not eligible."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import stat
import struct
import subprocess
import sys
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'release/current.json'
BUNDLE_ID = 'io.github.hmcneill46.celeste.everest.jit.everest'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_path(root, name):
    if not isinstance(name, str) or not name or PurePosixPath(name).is_absolute():
        raise ValueError('Expected a relative public source path')
    path = root / name
    if (any(p in {'.private', '.build', 'artifacts', 'dist', '..'} for p in PurePosixPath(name).parts)
            or path.resolve() != path.absolute() or not path.is_file()):
        raise ValueError('Missing, private or aliased public source path: ' + name)
    return path


def readiness(root):
    config = json.loads((root / CONFIG).read_text())
    if config.get('schema') != 1:
        raise ValueError('Unsupported release manifest schema')
    identity = json.loads(public_path(root, config['lane'] + '/BuildIdentity.json').read_text())
    if any(config[k] != identity[k] for k in ['version', 'build_number']):
        raise ValueError('Release manifest differs from its app identity')
    blockers = list(config.get('blockers', []))
    if not all(isinstance(b, str) and b.strip() for b in blockers):
        raise ValueError('Every release blocker must have an explanation')
    if config.get('public_ipa_ready') is not True:
        blockers.append('This app version has not been approved as a publicly distributable IPA.')
    script = config.get('public_build_script')
    if script != 'tools/build_public_release.py':
        blockers.append('A public build recipe is not configured; private/reproduction builders are ineligible.')
    else:
        public_path(root, script)
    report = dict(status='READY' if not blockers else 'BLOCKED',
                  version=config['version'], build_number=config['build_number'], blockers=blockers,
                  public_build_script=script, public_ipa_publishing_allowed=not blockers)
    return config, report


def validate_ref(ref, version):
    match = re.fullmatch(r'refs/tags/v(\d+\.\d+\.\d+)(?:-rc\.\d+)?', ref or '')
    if not match:
        raise ValueError('Release from an existing version tag, for example refs/tags/v0.21.0; branch pushes only run CI.')
    tag = ref.removeprefix('refs/tags/')
    if match[1] != version:
        raise ValueError('Tag version differs from the release manifest')
    return tag


def preflight(root, ref):
    config, report = readiness(root)
    tag = validate_ref(ref, config['version'])
    if report['blockers']:
        raise ValueError('Public IPA release is blocked:\n- ' + '\n- '.join(report['blockers']))
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip():
        raise ValueError('Release builds require a clean public checkout')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    tagged = subprocess.check_output(['git', 'rev-parse', '--verify', ref + '^{commit}'], cwd=root, text=True).strip()
    if revision != tagged:
        raise ValueError('Checked out commit differs from the version tag')
    return config, dict(report, tag=tag, source_commit=revision)


def verify_ipa(path, version, build_number):
    """Reject known private package contents and signing material before upload."""
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if not infos or len(infos) > 10000 or sum(i.file_size for i in infos) > 1024**3:
            raise ValueError('Unexpected IPA size or member count')
        names, folded = set(), set()
        for i in infos:
            name = i.filename
            parts = PurePosixPath(name).parts
            if (name in names or name.startswith('/') or '\\' in name or '..' in parts
                    or not parts or parts[0] != 'Payload'
                    or stat.S_ISLNK(i.external_attr >> 16)):
                raise ValueError('Unsafe or duplicate IPA member: ' + name)
            names.add(name)
            normalized = unicodedata.normalize('NFC', name.rstrip('/')).casefold()
            if normalized in folded:
                raise ValueError('Case/Unicode collision in IPA: ' + name)
            folded.add(normalized)
            lower = name.lower()
            if (PurePosixPath(lower).name in {'celeste.dll', 'celeste.exe', 'celeste.content.dll'}
                    or PurePosixPath(lower).suffix in {'.bank', '.xnb', '.p12', '.p8', '.mobileprovision', '.a'}
                    or '_CodeSignature' in parts):
                raise ValueError('Game payload, SDK archive or signing material in public IPA: ' + name)
        plists = [n for n in names if re.fullmatch(r'Payload/[^/]+\.app/Info\.plist', n)]
        if len(plists) != 1:
            raise ValueError('Expected one main app in the IPA')
        info = plistlib.loads(z.read(plists[0]))
        if (info.get('CFBundleShortVersionString') != version
                or info.get('CFBundleVersion') != build_number or info.get('CFBundleIdentifier') != BUNDLE_ID):
            raise ValueError('IPA identity differs from the approved release')
        executable = info['CFBundleExecutable']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', executable):
            raise ValueError('Invalid app executable name')
        data = z.read(plists[0].rsplit('/', 1)[0] + '/' + executable)
        if (len(data) < 32 or struct.unpack_from('<II', data) != (0xfeedfacf, 0x100000c)
                or struct.unpack_from('<I', data, 12)[0] != 2):
            raise ValueError('Expected an arm64 Mach-O app executable')
        count, size = struct.unpack_from('<II', data, 16)
        if 32 + size > len(data):
            raise ValueError('Truncated Mach-O load commands')
        offset, uuids, platforms = 32, 0, []
        for _ in range(count):
            if offset + 8 > 32 + size:
                raise ValueError('Truncated Mach-O load command')
            command, length = struct.unpack_from('<II', data, offset)
            if length < 8 or offset + length > 32 + size or command == 0x1d:
                raise ValueError('Malformed or signed executable; publish an unsigned IPA')
            if command == 0x1b:
                if length != 24 or data[offset + 8:offset + 24] == bytes(16):
                    raise ValueError('Missing executable UUID')
                uuids += 1
            if command == 0x32:
                if length < 24:
                    raise ValueError('Truncated platform command')
                platforms.append(struct.unpack_from('<I', data, offset + 8)[0])
            offset += length
        if offset != 32 + size or uuids != 1 or platforms != [2] or z.testzip() is not None:
            raise ValueError('Invalid executable command table or ZIP checksum')


def verify_provenance(value, revision):
    if (value.get('schema') != 1 or value.get('source_commit') != revision
            or value.get('private_inputs_used') is not False):
        raise ValueError('Public build provenance is missing or identifies other/private inputs')
    deps = value.get('dependencies')
    if not isinstance(deps, list) or not deps:
        raise ValueError('The public builder must disclose its dependency inputs')
    for dep in deps:
        if (not isinstance(dep, dict) or dep.get('kind') not in {'source', 'binary'}
                or not dep.get('name') or not dep.get('license')
                or not re.fullmatch('[0-9a-f]{64}', dep.get('sha256', ''))
                or not str(dep.get('url', '')).startswith('https://')):
            raise ValueError('A dependency lacks its source/binary classification, origin, hash or license')


def build(root, ref):
    config, result = preflight(root, ref)
    script = public_path(root, config['public_build_script'])
    work, kit = root / '.build/public-release-build', root / '.build/public-release-kit'
    if (work.exists() or kit.exists() or work.resolve() != work.absolute()
            or kit.resolve() != kit.absolute()):
        raise ValueError('Release work and kit directories must be fresh')
    # A future public recipe must build from this checkout and publicly available,
    # licensed inputs. Never hydrate .private or accept a prebuilt private IPA.
    subprocess.run([sys.executable, str(script), '--work', str(work),
                    '--output', str(work / 'output')], cwd=root, check=True)
    out = work / 'output'
    expected = ['Cabrillo.ipa', 'BUILD_PROVENANCE.json', 'RELEASE_NOTES.md']
    for name in expected:
        p = out / name
        if not p.is_file() or p.resolve() != p.absolute():
            raise ValueError('Public builder did not produce a regular ' + name)
    verify_ipa(out / 'Cabrillo.ipa', config['version'], config['build_number'])
    provenance = json.loads((out / 'BUILD_PROVENANCE.json').read_text())
    verify_provenance(provenance, result['source_commit'])
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip():
        raise ValueError('Builder changed public source during the release')
    kit.mkdir(parents=True)
    ipa_name = 'Cabrillo-' + config['version'] + '-unsigned.ipa'
    shutil.copyfile(out / 'Cabrillo.ipa', kit / ipa_name)
    shutil.copyfile(out / 'RELEASE_NOTES.md', kit / 'RELEASE_NOTES.md')
    provenance.update(version=config['version'], build_number=config['build_number'],
                      tag=result['tag'], ipa_sha256=sha(kit / ipa_name),
                      public_builder_sha256=sha(script),
                      public_inventory_sha256=sha(root / 'docs/MIGRATION_FILE_INVENTORY.json'))
    (kit / 'BUILD_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (kit / 'SHA256SUMS').write_text(''.join(sha(kit / n) + '  ' + n + '\n'
        for n in [ipa_name, 'BUILD_PROVENANCE.json', 'RELEASE_NOTES.md']))
    return dict(result, ipa=ipa_name, ipa_sha256=sha(kit / ipa_name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['readiness', 'preflight', 'build'])
    parser.add_argument('--ref', default=os.environ.get('GITHUB_REF'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'readiness':
            _, result = readiness(ROOT)
        elif args.command == 'preflight':
            _, result = preflight(ROOT, args.ref)
        else:
            result = build(ROOT, args.ref)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        if args.command == 'preflight' and os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                for key in ['tag', 'source_commit']:
                    f.write(key + '=' + result[key] + '\n')
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
