#!/usr/bin/env python3
"""Build release59 from this checkout, fresh public dependencies and your FMOD SDK.

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
from verify_release_nuget import verify_packages


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
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    from compile_release59 import validate_overlay, IDENTITY
    validate_overlay(json_read(IDENTITY / 'Dependencies.json'))
    if not shutil.which('sn') or not shutil.which('mono'):
        raise ValueError('Mono 6.14.1, including its sn tool, is required to preserve NLua strong-name signing. Install Mono before building.')
    mono_version = subprocess.check_output(['mono', '--version'], text=True).splitlines()[0]
    if not mono_version.startswith('Mono JIT compiler version 6.14.1 '):
        raise ValueError('The release build uses Mono 6.14.1 for NLua strong-name signing')
    config = json_read(ROOT / 'release/public59.json')
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
            folder = {'build_input_fixes59_managed.py': work / 'managed',
                      'check_input_fixes59_managed.py': work / 'everest-audit',
                      'build_stikjit59.py': work / 'stikjit',
                      'build_owned_native.py': work / 'native'}.get(tool)
            if folder and folder.is_dir():
                logs = sorted(folder.glob('*.log'), key=lambda p: p.stat().st_mtime)
                if logs:
                    print('Last public-source compiler diagnostics (' + logs[-1].name + '):', flush=True)
                    print('\n'.join(logs[-1].read_text(errors='replace').splitlines()[-100:]), flush=True)
            raise

    inputs, managed, native, fmod, cache = [work / n for n in ['inputs', 'managed', 'native', 'fmod', 'downloads']]
    run('prepare_everest55_public.py', '--work', inputs, '--cache', cache)
    run('build_input_fixes59_managed.py', '--inputs', inputs, '--work', managed)
    verify_packages(json_read(managed / 'receipt.json')['nuget_packages'], json_read(inputs / 'receipt.json')['sdk_arch'])
    run('check_input_fixes59_managed.py', '--managed', managed / 'receipt.json', '--work', work / 'everest-audit')
    run('build_owned_native.py', '--inputs', inputs, '--work', native)
    run('prepare_owned_fmod.py', '--sdk', sdk, '--native', native / 'receipt.json', '--work', fmod)
    artifacts = ROOT / 'artifacts' / ('release59-' + work.name)
    run('build_stikjit59.py', '--work', work / 'stikjit')
    run('compile_release59.py', '--managed', managed / 'receipt.json', '--native', native / 'receipt.json',
        '--fmod', fmod / 'receipt.json', '--stikjit', work / 'stikjit/receipt.json', '--shortcuts', ROOT / 'release/shortcuts49/manifest.json',
        '--work', work / 'app', '--output', artifacts)
    receipt = json_read(artifacts / 'build-receipt.json')
    run('check_input_fixes59_retained_inputs.py', '--ipa', artifacts / receipt['ipa'],
        '--work', work / 'retained-input-audit')
    retained_input_audit = json_read(work / 'retained-input-audit/receipt.json')
    output.mkdir(parents=True)
    shutil.copyfile(artifacts / receipt['ipa'], output / 'Cabrillo.ipa')
    shutil.copyfile(artifacts / 'verification.json', output / 'PACKAGE_AUDIT.json')
    dependencies = []
    stikjit = json_read(work / 'stikjit/receipt.json')
    stikjit_lock = json_read(ROOT / 'release/stikjit57.json')
    dependencies.append(dict(name='StikJIT/' + stikjit['source_commit'], kind='mixed',
        url=stikjit_lock['url'], sha256=stikjit['archive_sha256'], license=stikjit_lock['license']))
    dependencies.append(dict(name='StikJIT/idevice-ffi', kind='binary',
        url='https://raw.githubusercontent.com/StikDebug/StikJIT/' + stikjit['source_commit'] + '/idevice/libidevice_ffi.a',
        sha256=stikjit['bundled_idevice_ffi']['sha256'], license='MIT; included idevice notice. Upstream binary source revision undisclosed.'))
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
        integrated_jit=dict(upstream_commit=stikjit['source_commit'], archive_sha256=stikjit['archive_sha256'],
            bundled_idevice_ffi=stikjit['bundled_idevice_ffi'], framework_linked_into_host=False,
            helper_minimum_ios='17.4', helper_files=stikjit['files'], physical_device_tested=False),
        everest_release=json_read(ROOT / 'release/everest55-dependencies.json')['everest_release'],
        managed_runtime_audit=json_read(work / 'everest-audit/receipt.json'),
        native_retained_inputs=dict(status=retained_input_audit['status'],
            checks=len(retained_input_audit['report']['checks']),
            ipa_sha256=retained_input_audit['ipa_sha256'],
            actual_production_function_used=True),
        toolchain=dict(xcode='26.6', xcode_build='17F113', iphoneos_sdk='26.5', minimum_ios='15.0',
            mono_build_tool=mono_version, strong_name_tool_sha256=sha(Path(shutil.which('sn'))),
            cmake=subprocess.check_output(['cmake', '--version'], text=True).splitlines()[0],
            python=sys.version.split()[0]),
        physical_device_tested=False, bit_reproducibility_claimed=False,
        package_receipt_sha256=sha(artifacts / 'build-receipt.json'),
        payload_audit_sha256=sha(artifacts / 'payload-audit.json'),
        package_audit_sha256=sha(output / 'PACKAGE_AUDIT.json'),
        source_files=receipt['source_sha256'])
    (output / 'BUILD_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    build_location = 'on GitHub Actions' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'locally'
    (output / 'RELEASE_NOTES.md').write_text(
        '# Cabrillo ' + config['version'] + ' · build ' + config['build_number'] + '\n\n'
        'Fixes touch-editor edge resizing and Save validation, and controller light-colour replay after native suspend/resume. '
        'Keeps the accepted full-display editor, live feather/grab/controller preferences, game-input compatibility and stable Everest1.6642.0. '
        'Preserves Built-in StikJIT and existing providers, native JIT/detach gates, dependency recovery, Feather copy imports, bundle ID, save/profile paths and signed Shortcut49.\n\n'
        'Built-in StikJIT needs a Development-signed installation preserving get-task-allow and the helper extension, '
        'Developer Mode, a valid pairing file and LocalDevVPN or a compatible tunnel at10.7.0.1:49152. '
        'It is unavailable inside LiveContainer; use one of the retained JIT methods there. '
        'Current iLoader versions use a fixed app list and do not list Cabrillo; '
        'export a pairing file and import it in Cabrillo instead. No iLoader changes are required. '
        'Helper launch/signing and physical JIT/gameplay require device acceptance.\n\n'
        'Existing verified game preparation can be reused while its identity remains valid. '
        'Existing saves and original imported files are preserved. '
        'No new physical-device gameplay or JIT test is claimed by this build.\n\n'
        'Unsigned iPhone/iPad IPA built from the tagged or selected public source ' + build_location + '. '
        'Install with a compatible sideloading/LiveContainer or TrollStore setup; iOS 15 or later and JIT are required.\n\n'
        'Import your own original Celeste FNA 1.4.0.0 game ZIP. The first game launch prepares your copy; '
        'later launches reuse its verified cache. No Celeste game code or assets are bundled.\n\n'
        'FMOD runtime code is included with Firelight permission. Players do not need an FMOD account. '
        'Developers must obtain their own SDK from fmod.com; SDK components are not distributed.\n\n'
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
