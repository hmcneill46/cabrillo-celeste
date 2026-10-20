#!/usr/bin/env python3
"""Build and audit public release candidates; only exact version tags may publish."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from release import ROOT, public_path, sha, validate_ref, verify_ipa
from fetch_fmod_sdk import ARCHIVE_SHA256

CONFIG = 'release/public57.json'
BUILD_BRANCHES = {'refs/heads/main', 'refs/heads/codex/actions-release'}


def readiness(root):
    config = json.loads((root / CONFIG).read_text())
    if config.get('schema') != 2:
        raise ValueError('Unsupported public release manifest')
    identity = json.loads(public_path(root, config['lane'] + '/BuildIdentity.json').read_text())
    if any(config[k] != identity[k] for k in ['version', 'build_number']):
        raise ValueError('Release manifest differs from its app identity')
    if config.get('public_build_script') != 'tools/build_release57.py':
        raise ValueError('Only the fresh public source recipe is eligible')
    public_path(root, config['public_build_script'])
    public_path(root, config['shortcuts'])
    permission = config.get('fmod_distribution', {})
    blockers = list(config.get('blockers', []))
    if (config.get('public_ipa_ready') is not True or permission.get('approved') is not True
            or not permission.get('permission_reference')
            or permission.get('sdk_source') != 'https://www.fmod.com/download'
            or permission.get('sdk_archive_sha256') != ARCHIVE_SHA256):
        blockers.append('FMOD runtime permission or official pinned SDK acquisition is missing.')
    return config, dict(status='READY' if not blockers else 'BLOCKED', blockers=blockers,
                        version=config['version'], build_number=config['build_number'],
                        physical_device_tested=config.get('physical_device_tested', False))


def release_ref(ref, version, publish):
    if ref in BUILD_BRANCHES and not publish:
        return ''
    return validate_ref(ref, version)


def preflight(root, ref, publish=False):
    config, report = readiness(root)
    tag = release_ref(ref, config['version'], publish)
    if report['blockers']:
        raise ValueError('Release build blocked: ' + '; '.join(report['blockers']))
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip():
        raise ValueError('Release builds require a clean public checkout')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    selected_ref = ref
    if ref in BUILD_BRANCHES and os.environ.get('GITHUB_ACTIONS') == 'true':
        selected_ref = ref.replace('refs/heads/', 'refs/remotes/origin/', 1)
    selected = subprocess.check_output(['git', 'rev-parse', '--verify', selected_ref + '^{commit}'], cwd=root, text=True).strip()
    if revision != selected:
        raise ValueError('Checkout differs from the selected source ref')
    if os.environ.get('GITHUB_SHA') and os.environ['GITHUB_SHA'] != revision:
        raise ValueError('Workflow source identity differs from checkout')
    return config, dict(report, tag=tag, source_commit=revision, source_ref=ref,
                        publish='true' if publish else 'false')


def verify_provenance(value, revision, hosted=False):
    if (value.get('schema') != 2 or value.get('source_commit') != revision
            or any(value.get(k) is not False for k in
                   ['game_inputs_used', 'private_capsule_used', 'prebuilt_app_used', 'bit_reproducibility_claimed'])
            or value.get('licensed_inputs_used') != ['FMOD Engine iOS 1.10.09']):
        raise ValueError('Missing or incompatible source build provenance')
    if hosted and (value.get('fmod_acquisition') != 'official-authenticated-download'
                   or value.get('fmod_installer_sha256') != ARCHIVE_SHA256):
        raise ValueError('Hosted provenance requires official FMOD acquisition')
    deps = value.get('dependencies')
    if not isinstance(deps, list) or not deps:
        raise ValueError('Dependencies must be disclosed')
    names = set()
    for dep in deps:
        if (not isinstance(dep, dict) or dep.get('kind') not in
                {'source', 'binary', 'mixed', 'licensed-binary', 'signed-document'}
                or not dep.get('name') or dep['name'] in names or not dep.get('license')
                or not re.fullmatch('[0-9a-f]{64}', dep.get('sha256', ''))
                or not str(dep.get('url', '')).startswith('https://')
                or '?' in dep['url'] or '@' in dep['url']):
            raise ValueError('Undisclosed dependency or unsafe public origin')
        names.add(dep['name'])
    for name in ['FMOD 1.10.09/lowLevel', 'FMOD 1.10.09/studio']:
        dep = next((d for d in deps if d['name'] == name), {})
        if (dep.get('kind') != 'licensed-binary' or dep.get('url') != 'https://www.fmod.com/download'
                or dep.get('sdk_redistribution_permitted') is not False):
            raise ValueError('FMOD must remain a declared licensed binary input')
    shortcuts = value.get('shortcut_verification', {})
    if (shortcuts.get('status') != 'PASS_SIGNED_SHORTCUT_SOURCE_MATCH'
            or shortcuts.get('signatures_verified') is not True
            or shortcuts.get('actions_match_generated_source') is not True):
        raise ValueError('Signed Shortcut content verification is missing')
    if 'integrated_jit' in value:
        verify_integrated_provenance(value)


def verify_integrated_provenance(value):
    from build_stikjit57 import lock_value
    lock = lock_value()
    feature = value.get('integrated_jit', {})
    if (feature.get('upstream_commit') != lock['commit'] or feature.get('archive_sha256') != lock['archive_sha256']
            or feature.get('bundled_idevice_ffi') != lock['bundled_idevice_ffi']
            or feature.get('framework_linked_into_host') is not False or feature.get('helper_minimum_ios') != '17.4'
            or feature.get('physical_device_tested') is not False or not feature.get('helper_files')):
        raise ValueError('Missing integrated JIT helper/source/binary disclosure')
    expected_files = {'StikJIT.framework/' + name for name in ['StikJIT', 'Info.plist', 'universal.js', 'legacy.js']}
    expected_files |= {'CabrilloJITHelper.appex/' + name for name in ['CabrilloJITHelper', 'Info.plist']}
    if set(feature['helper_files']) != expected_files or any(not re.fullmatch('[0-9a-f]{64}', v) for v in feature['helper_files'].values()):
        raise ValueError('Helper disclosure must contain exactly its runtime files, without build products')
    expected = [('StikJIT/' + lock['commit'], 'mixed', lock['archive_sha256']),
                ('StikJIT/idevice-ffi', 'binary', lock['bundled_idevice_ffi']['sha256'])]
    for name, kind, digest in expected:
        row = next((d for d in value.get('dependencies', []) if d.get('name') == name), {})
        if row.get('kind') != kind or row.get('sha256') != digest:
            raise ValueError('StikJIT and its upstream prebuilt idevice library must be disclosed separately')


def verify_integrated_kit(directory, version):
    """Inspect sealed helper bytes again on the independent verification host."""
    from verify_integrated_jit57 import verify_parts
    import plistlib
    provenance = json.loads((directory / 'BUILD_PROVENANCE.json').read_text())
    verify_integrated_provenance(provenance)
    ipa = directory / ('Cabrillo-' + version + '-unsigned.ipa')
    verify_ipa(ipa, version, '57')
    prefix = 'Payload/CelesteJITEverest.app/'
    with zipfile.ZipFile(ipa) as archive:
        read = lambda name: archive.read(prefix + name)
        verify_parts(plistlib.loads(read('Info.plist')), json.loads(read('BuildInfo.json')), read('CelesteJITEverest'),
                     plistlib.loads(read('PlugIns/CabrilloJITHelper.appex/Info.plist')), read('PlugIns/CabrilloJITHelper.appex/CabrilloJITHelper'),
                     plistlib.loads(read('Frameworks/StikJIT.framework/Info.plist')), read('Frameworks/StikJIT.framework/StikJIT'),
                     json.loads(read('licenses/StikJIT/UPSTREAM.json')))
        for name, digest in provenance['integrated_jit']['helper_files'].items():
            if (not isinstance(name, str) or '..' in Path(name).parts or name.startswith('/')
                    or not name.startswith(('StikJIT.framework/', 'CabrilloJITHelper.appex/'))):
                raise ValueError('Unsafe helper provenance path')
            packaged = ('Frameworks/' if name.startswith('StikJIT.framework/') else 'PlugIns/') + name
            if __import__('hashlib').sha256(read(packaged)).hexdigest() != digest:
                raise ValueError('Sealed StikJIT helper bytes differ')


def kit_names(version):
    return {'Cabrillo-' + version + '-unsigned.ipa', 'BUILD_PROVENANCE.json',
            'PACKAGE_AUDIT.json', 'RELEASE_NOTES.md', 'SHA256SUMS'}


def verify_kit(directory, version):
    if {p.name for p in directory.iterdir()} != kit_names(version):
        raise ValueError('Release kit contains missing or unapproved files')
    for path in directory.iterdir():
        if not path.is_file() or path.resolve() != path.absolute():
            raise ValueError('Release kit contains a directory or aliased file')
    rows = (directory / 'SHA256SUMS').read_text().splitlines()
    expected = kit_names(version) - {'SHA256SUMS'}
    found = set()
    for row in rows:
        if '  ' not in row:
            raise ValueError('Invalid release checksum row')
        digest, name = row.split('  ', 1)
        if name not in expected or name in found or digest != sha(directory / name):
            raise ValueError('Release checksum mismatch or unexpected file')
        found.add(name)
    if found != expected:
        raise ValueError('Incomplete release checksums')


def build(root, ref, publish, sdk, download):
    config, result = preflight(root, ref, publish)
    work, kit = root / '.build/public-release-build', root / '.build/public-release-kit'
    if any(p.exists() or p.resolve() != p.absolute() for p in [work, kit]):
        raise ValueError('Release work and kit directories must be fresh')
    script = public_path(root, config['public_build_script'])
    command = [sys.executable, '-u', str(script), '--work', str(work), '--output', str(work / 'output'), '--fmod-sdk', sdk]
    if download:
        command += ['--fmod-download', download]
    subprocess.run(command, cwd=root, check=True)
    out = work / 'output'
    expected = {'Cabrillo.ipa', 'BUILD_PROVENANCE.json', 'PACKAGE_AUDIT.json', 'RELEASE_NOTES.md'}
    if {p.name for p in out.iterdir()} != expected or any(p.is_symlink() or not p.is_file() for p in out.iterdir()):
        raise ValueError('Builder output contains missing or unapproved files')
    verify_ipa(out / 'Cabrillo.ipa', config['version'], config['build_number'])
    provenance = json.loads((out / 'BUILD_PROVENANCE.json').read_text())
    verify_provenance(provenance, result['source_commit'], os.environ.get('GITHUB_ACTIONS') == 'true')
    if config['build_number'] == '57':
        verify_integrated_provenance(provenance)
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root).strip():
        raise ValueError('Build changed public source')
    kit.mkdir(parents=True)
    ipa_name = 'Cabrillo-' + config['version'] + '-unsigned.ipa'
    shutil.copyfile(out / 'Cabrillo.ipa', kit / ipa_name)
    for name in ['PACKAGE_AUDIT.json', 'RELEASE_NOTES.md']:
        shutil.copyfile(out / name, kit / name)
    provenance.update(version=config['version'], build_number=config['build_number'], tag=result['tag'],
        source_ref=ref, ipa_sha256=sha(kit / ipa_name), public_builder_sha256=sha(script),
        public_inventory_sha256=sha(root / 'docs/MIGRATION_FILE_INVENTORY.json'),
        workflow_run_id=os.environ.get('GITHUB_RUN_ID'), workflow_run_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))
    (kit / 'BUILD_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (kit / 'SHA256SUMS').write_text(''.join(sha(kit / n) + '  ' + n + '\n' for n in sorted(kit_names(config['version']) - {'SHA256SUMS'})))
    verify_kit(kit, config['version'])
    return dict(result, status='PASS_RELEASE_KIT', ipa=ipa_name, ipa_sha256=sha(kit / ipa_name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['readiness', 'preflight', 'build', 'verify-kit'])
    parser.add_argument('--ref', default=os.environ.get('GITHUB_REF'))
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--fmod-sdk')
    parser.add_argument('--fmod-download')
    parser.add_argument('--kit', type=Path, default=ROOT / '.build/public-release-kit')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'readiness':
            _, result = readiness(ROOT)
        elif args.command == 'preflight':
            _, result = preflight(ROOT, args.ref, args.publish)
        elif args.command == 'verify-kit':
            config, _ = readiness(ROOT)
            verify_kit(args.kit.absolute(), config['version'])
            if config['build_number'] == '57':
                verify_integrated_kit(args.kit.absolute(), config['version'])
            result = dict(status='PASS_RELEASE_KIT_ALLOWLIST')
        else:
            if not args.fmod_sdk:
                raise ValueError('An explicit FMOD SDK path is required')
            result = build(ROOT, args.ref, args.publish, args.fmod_sdk, args.fmod_download)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        if args.command == 'preflight' and os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
                for key in ['tag', 'source_commit', 'source_ref', 'publish']:
                    stream.write(key + '=' + result[key] + '\n')
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
