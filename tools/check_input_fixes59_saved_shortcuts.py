#!/usr/bin/env python3
"""Run119 save/transfer and185 shortcut controls against actual59 source copies.

These are host fixtures using synthetic files and socketpairs. They do not
install an app, contact a device, execute JIT or modify the signed Shortcuts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import compile_release59 as build

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-input-fixes59'
PREVIOUS = ROOT / 'experiments/ios-jit/launcher-unified58'
XCODE = 'Xcode 26.6\nBuild version 17F113'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(paths):
    rows = {}
    for path in sorted(set(paths)):
        if path.is_symlink() or not path.is_file() or path.resolve() != path:
            raise ValueError('Missing or aliased retained-control input: ' + str(path))
        rows[str(path.relative_to(ROOT))] = sha(path)
    return rows


def retained_parity():
    names = ['native/' + name for name in ['ProfileBackup.swift', 'ProfileSlots.swift',
             'SaveTransfers.swift', 'ModLibrary.swift', 'DependencyInstaller.swift',
             'DependencyPlan.swift', 'RuntimeIdentity.swift', 'XXHash64.swift']]
    names += ['src/' + name + suffix for name in ['CJShortcutSession', 'CJShortcutPlatform',
              'CJShortcutRouteProbe', 'CJPlatformOptions'] for suffix in ['.h', '.m']]
    names += ['tests/' + name for name in ['ProfileBackupTests.swift', 'SaveTransferTests.swift',
              'ShortcutSessionTests.m', 'ShortcutCellularTests.m']]
    for name in names:
        if (LANE / name).read_bytes() != (PREVIOUS / name).read_bytes():
            raise ValueError('Retained59 saved-data/shortcut function differs from58: ' + name)
    return {name: sha(LANE / name) for name in names}


def sandbox(work):
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios',
                 ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    path = work / 'tests.sb'
    path.write_text(policy)
    return path


def profiles(work, env):
    work.mkdir()
    native = work / 'native'
    native.mkdir()
    excluded = {'PlatformViews.swift', 'ShortcutViews.swift', 'IntegratedJITViews.swift'}
    sources = [p for p in build.selected_swift_sources() if p.name not in excluded]
    if any(p.parent != LANE / 'native' for p in sources):
        raise ValueError('Profile controls must compile the selected59 Swift')
    sources += [LANE / 'tests/ProfileBackupTests.swift', LANE / 'tests/SaveTransferTests.swift']
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c_sources = sorted((yaml / 'src').glob('*.c'))
    inputs = sources + vendor + [p for p in yaml.rglob('*') if p.is_file()]
    inputs += [Path(__file__).resolve(), ROOT / 'tools/compile_release59.py',
               build.IDENTITY / 'Dependencies.json']
    hashes = snapshot(inputs)
    commands = []
    env = dict(env, CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'),
               SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))

    def run(command, label):
        command = list(map(str, command))
        commands.append(command)
        with (work / (label + '.log')).open('w') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=240)
        if result.returncode:
            raise RuntimeError(label + ' failed; see ' + str(work / (label + '.log')))

    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-module-name', 'ZIPFoundation',
         '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule',
         '-o', native / 'libZIPFoundation.a', *vendor], 'compile-zip')
    objects = []
    for source in c_sources:
        obj = native / (source.stem + '.o')
        objects.append(obj)
        run(['xcrun', 'clang', '-DYAML_DECLARE_STATIC', '-O2', '-I' + str(yaml / 'include'),
             '-c', source, '-o', obj], 'compile-' + source.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *objects], 'archive-yaml')
    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', native, '-I', yaml / 'include',
         *sources, native / 'libZIPFoundation.a', native / 'libCYaml.a', '-o', work / 'tests'], 'compile-profiles')
    run(['sandbox-exec', '-f', sandbox(work), work / 'tests', work / 'results'], 'run-profiles')
    report = work / 'results/results.json'
    result = json.loads(report.read_text())
    if result.get('status') != 'PASS_PROFILE_BACKUPS' or len(result.get('checks', [])) != 119:
        raise ValueError('Expected all119 actual59 profile/transfer controls')
    if snapshot(inputs) != hashes:
        raise ValueError('Profile sources changed during controls')
    receipt = dict(status='PASS_INPUT_FIXES59_PROFILE_CONTROLS', checks=119, source_sha256=hashes,
                   results_sha256=sha(report), commands=commands, network_denied=True,
                   presentation_files_excluded=sorted(excluded), physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def shortcuts(work, env):
    # The retained runner stays byte-identical. Rebind its source constant only
    # in this isolated child interpreter; it compiles59 implementations/fixtures.
    script = ROOT / 'tools/ci/check_native_shortcuts.py'
    code = ('import importlib.util,pathlib,sys; '
            'p=pathlib.Path(sys.argv[1]); '
            's=importlib.util.spec_from_file_location("retained_shortcuts59",p); '
            'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
            'm.SOURCE=pathlib.Path(sys.argv[2]); '
            'sys.argv=[str(p),"--work",sys.argv[3]]; m.main()')
    command = [sys.executable, '-c', code, str(script), str(LANE), str(work)]
    with work.with_suffix('.log').open('w') as stream:
        subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                       check=True, timeout=180)
    receipt = json.loads((work / 'receipt.json').read_text())
    if (receipt.get('status') != 'PASS_PUBLIC_NATIVE_SHORTCUT_CHECKS'
            or receipt.get('native_checks') != 132 or receipt.get('cellular_checks') != 53
            or receipt.get('shortcut_branches') != 36 or receipt.get('rejected_broken_url_connections') != 15
            or not receipt.get('original43_failure_reproduced') or not receipt.get('original49_failure_reproduced')):
        raise ValueError('Missing actual59 shortcut regression or original failure controls')
    required = [LANE / 'src' / name for name in ['CJShortcutSession.m', 'CJShortcutPlatform.m',
                'CJPlatformOptions.m', 'CJShortcutRouteProbe.m']]
    if any(receipt['source_sha256'].get(str(p.relative_to(ROOT))) != sha(p) for p in required):
        raise ValueError('Shortcut runner did not compile actual59 implementations')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh unaliased work path under .build')
    env = dict(os.environ, DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'),
               PYTHONDONTWRITEBYTECODE='1')
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('Retained controls require Xcode26.6/17F113')
    build.validate_overlay(build.read_json(build.IDENTITY / 'Dependencies.json'))
    parity = retained_parity()
    inputs = [Path(__file__).resolve(), ROOT / 'tools/ci/check_native_shortcuts.py']
    inputs += [base / name for base in [LANE, PREVIOUS] for name in parity]
    hashes = snapshot(inputs)
    work.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = {'profiles': executor.submit(profiles, work / 'profiles', env),
                'shortcuts': executor.submit(shortcuts, work / 'shortcuts', env)}
        reports = {name: future.result() for name, future in jobs.items()}
    if retained_parity() != parity or snapshot(inputs) != hashes:
        raise ValueError('Retained implementation, fixture or wrapper changed during controls')
    receipt = dict(status='PASS_INPUT_FIXES59_SAVES_AND_SHORTCUTS', build_number='59',
                   created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), xcode=XCODE,
                   profile_checks=119, shortcut_native_checks=185, shortcut_branches=36, broken_url_controls=15,
                   retained58_functions_and_fixtures_exact=parity, source_sha256=hashes,
                   receipts={name: dict(path=str((work / name / 'receipt.json').relative_to(ROOT)),
                                        sha256=sha(work / name / 'receipt.json')) for name in reports},
                   reports=reports, actual59_sources_compiled=True, game_or_jit_executed=False,
                   private_dependencies_used=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], '119 profiles;185 shortcut native;36 branches;15 broken URLs')


if __name__ == '__main__':
    main()
