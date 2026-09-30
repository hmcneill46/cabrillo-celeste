#!/usr/bin/env python3
"""Build release51 from this checkout, fresh public dependencies and your FMOD SDK.

The SDK is a licensed build input, never an uploadable output. This recipe does
not accept previously compiled Cabrillo libraries, an IPA, or a Celeste game ZIP.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from compile_owned_game import ROOT, sha
from fetch_fmod_sdk import ARCHIVE_BYTES, ARCHIVE_SHA256, LICENSE_SHA256, validate_sdk
from verify_release_shortcuts import verify as verify_shortcuts


def json_read(path):
    return json.loads(path.read_text())


def validate_download(receipt, sdk):
    expected = validate_sdk(sdk)
    if (receipt.get('status') != 'PASS_OFFICIAL_FMOD_SDK'
            or receipt.get('origin') != 'https://www.fmod.com'
            or receipt.get('temporary_session_closed') is not True
            or receipt.get('archive_sha256') != ARCHIVE_SHA256
            or receipt.get('archive_bytes') != ARCHIVE_BYTES
            or receipt.get('device_archives_sha256') != expected
            or receipt.get('license_sha256') != LICENSE_SHA256
            or ROOT / receipt.get('sdk_path', '') != sdk):
        raise ValueError('FMOD acquisition receipt does not match the staged SDK')


def build(work, output, sdk, download=None):
    config = json_read(ROOT / 'release/public.json')
    permission = config['fmod_distribution']
    if config['public_ipa_ready'] is not True or permission['approved'] is not True:
        raise ValueError('Public runtime distribution is not approved')
    if not permission['permission_reference']:
        raise ValueError('Missing FMOD runtime permission reference')
    for path in [work, output]:
        if path.resolve() != path.absolute() or ROOT / '.build' not in path.parents or path.exists():
            raise ValueError('Use fresh unaliased work/output paths under .build')
    sdk_hashes = validate_sdk(sdk)
    if download:
        validate_download(json_read(download), sdk)
    elif os.environ.get('GITHUB_ACTIONS') == 'true':
        raise ValueError('Hosted builds require a fresh official FMOD acquisition receipt')
    shortcuts = verify_shortcuts(ROOT / 'release/shortcuts49')
    work.mkdir(parents=True)

    def run(tool, *arguments):
        print('Building: ' + tool, flush=True)
        try:
            subprocess.run([sys.executable, '-u', str(ROOT / 'tools' / tool), *map(str, arguments)],
                           cwd=ROOT, check=True)
        except subprocess.CalledProcessError:
            # These are compiler logs from public source stages, after the SDK
            # acquisition step's credentials have left the environment. Never
            # inspect .private, the FMOD stage or arbitrary files for diagnostics.
            folder = {'build_owned_managed.py': work / 'managed',
                      'build_owned_native.py': work / 'native'}.get(tool)
            if folder and folder.is_dir():
                logs = sorted(folder.glob('*.log'), key=lambda p: p.stat().st_mtime)
                if logs:
                    print('Last public-source compiler diagnostics (' + logs[-1].name + '):', flush=True)
                    print('\n'.join(logs[-1].read_text(errors='replace').splitlines()[-100:]), flush=True)
            raise

    inputs, managed, native, fmod, cache = [work / n for n in ['inputs', 'managed', 'native', 'fmod', 'downloads']]
    run('prepare_owned_public.py', '--work', inputs, '--cache', cache)
    run('build_owned_managed.py', '--inputs', inputs, '--work', managed)
    run('build_owned_native.py', '--inputs', inputs, '--work', native)
    run('prepare_owned_fmod.py', '--sdk', sdk, '--native', native / 'receipt.json', '--work', fmod)
    artifacts = ROOT / 'artifacts' / ('release51-' + work.name)
    run('compile_release51.py', '--managed', managed / 'receipt.json', '--native', native / 'receipt.json',
        '--fmod', fmod / 'receipt.json', '--shortcuts', ROOT / 'release/shortcuts49/manifest.json',
        '--work', work / 'app', '--output', artifacts)
    receipt = json_read(artifacts / 'build-receipt.json')
    output.mkdir(parents=True)
    shutil.copyfile(artifacts / receipt['ipa'], output / 'Cabrillo.ipa')
    shutil.copyfile(artifacts / 'verification.json', output / 'PACKAGE_AUDIT.json')
    dependencies = []
    for name, row in json_read(inputs / 'receipt.json')['dependencies'].items():
        kind = 'binary' if name.startswith(('sdk', 'mono-')) else 'source'
        if name == 'Everest-libs':
            kind = 'mixed'
        dependencies.append(dict(name=name, kind=kind, url=row['url'],
            sha256=sha(cache / (name + '.archive')), license=row['license'],
            pinned_digest={k: row[k] for k in ['sha256', 'sha512'] if k in row}))
    for name, digest in json_read(managed / 'receipt.json')['nuget_packages'].items():
        package, version, _ = name.split('/')
        dependencies.append(dict(name=package + '/' + version, kind='binary',
            url='https://api.nuget.org/v3-flatcontainer/' + name, sha256=digest,
            license='Exact package license expressions and available texts are in licenses/nuget-packages.json.'))
    for kind, digest in sdk_hashes.items():
        dependencies.append(dict(name='FMOD 1.10.09/' + kind, kind='licensed-binary',
            url='https://www.fmod.com/download', sha256=digest,
            license=permission['permission_reference'], sdk_redistribution_permitted=False))
    for variant, digest in shortcuts['assets_sha256'].items():
        dependencies.append(dict(name='Shortcut49/' + variant, kind='signed-document', sha256=digest,
            url='https://github.com/hmcneill46/cabrillo-celeste/blob/' +
                subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() +
                '/release/shortcuts49/' + variant + '/Cabrillo.shortcut',
            license='Cabrillo MIT; pre-signed with Apple Shortcuts. Signature and generated actions verified.'))
    provenance = dict(schema=2,
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        game_inputs_used=False, private_capsule_used=False, prebuilt_app_used=False,
        licensed_inputs_used=['FMOD Engine iOS 1.10.09'],
        fmod_acquisition='official-authenticated-download' if download else 'developer-supplied-sdk',
        fmod_installer_sha256=ARCHIVE_SHA256 if download else None,
        dependencies=dependencies, shortcut_verification=shortcuts,
        toolchain=dict(xcode='26.6', xcode_build='17F113', iphoneos_sdk='26.5', minimum_ios='15.0'),
        physical_device_tested=False, bit_reproducibility_claimed=False,
        package_receipt_sha256=sha(artifacts / 'build-receipt.json'),
        payload_audit_sha256=sha(artifacts / 'payload-audit.json'),
        package_audit_sha256=sha(output / 'PACKAGE_AUDIT.json'),
        source_files=receipt['source_sha256'])
    (output / 'BUILD_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (output / 'RELEASE_NOTES.md').write_text(
        '# Cabrillo ' + config['version'] + ' · build ' + config['build_number'] + '\n\n'
        'Unsigned iPhone/iPad IPA built from the tagged or selected public source on GitHub Actions. '
        'Install with a compatible sideloading/LiveContainer or TrollStore setup; iOS 15 or later and JIT are required.\n\n'
        'Import your own original Celeste FNA 1.4.0.0 game ZIP. The first game launch prepares your copy; '
        'later launches reuse its verified cache. No Celeste game code or assets are bundled.\n\n'
        'FMOD runtime code is included with Firelight permission. Players do not need an FMOD account. '
        'Developers must obtain their own SDK from fmod.com; SDK components are not distributed.\n\n'
        'The launcher uses the accepted build50 source and shortcut49 templates. This newly compiled '
        'build has passed package checks; physical-device acceptance is separate and has not been claimed.\n\n'
        'BUILD_PROVENANCE.json records source, dependency hashes and binary inputs. GitHub attestations '
        'bind each download to its workflow and commit. They do not promise bit-for-bit reproducibility '
        'or make proprietary dependencies open source. See docs/RELEASING.md and docs/BUILDING.md.\n')
    print('PASS_FRESH_RELEASE_SOURCE_BUILD', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--fmod-sdk', required=True)
    parser.add_argument('--fmod-download', type=Path)
    args = parser.parse_args()
    build((ROOT / args.work).absolute(), (ROOT / args.output).absolute(),
          (ROOT / args.fmod_sdk).absolute(), args.fmod_download)
