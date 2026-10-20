#!/usr/bin/env python3
"""Compile actual56 native code; reproduce old MirrorName404 and test isolated fixes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
LANE = ROOT / 'experiments/ios-jit/launcher-dependency-downloads'
BASE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
XCODE = 'Xcode 26.6\nBuild version 17F113'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', required=True)
    p.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR'))
    args = p.parse_args()
    work = ROOT / args.work
    if work.resolve() != work.absolute() or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh unaliased .build directory')
    sys.path.insert(0, str(ROOT / 'tools'))
    from compile_release56 import selected_swift_sources
    selected = selected_swift_sources()
    expected = {LANE / 'native/DependencyPlan.swift', LANE / 'native/DependencyInstaller.swift'}
    if not expected.issubset(selected):
        raise ValueError('The production56 compiler must select both new native files')
    sources = [s for s in selected if s.name not in {'PlatformViews.swift', 'ShortcutViews.swift'}]
    original = [BASE / 'native' / s.name if s.name in {'DependencyPlan.swift', 'DependencyInstaller.swift'} else s for s in sources]
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c_sources = sorted((yaml / 'src').glob('*.c'))
    tests = [LANE / 'tests' / name for name in ['DependencyMirrorTests.swift', 'DependencyMirrorOriginalControl.swift']]
    paths = sorted(set(sources + original + vendor + c_sources + tests + [Path(__file__), ROOT / 'tools/compile_release56.py']))
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    hashes = {str(s.relative_to(ROOT)): digest(s) for s in paths}
    developer = args.developer_dir or subprocess.check_output(['xcode-select', '-p'], text=True).strip()
    env = dict(os.environ, DEVELOPER_DIR=developer,
               CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'), SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('Xcode26.6/17F113 is required')
    work.mkdir(parents=True)
    native = work / 'native'; native.mkdir()
    result = work / 'results'; result.mkdir()
    commands = []

    def run(command, name):
        command = list(map(str, command)); commands.append(command)
        with (work / (name + '.log')).open('w') as log:
            run_result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        if run_result.returncode:
            print((work / (name + '.log')).read_text()[-14000:])
            raise RuntimeError(name + ' failed')

    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-module-name', 'ZIPFoundation', '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule', '-o', native / 'libZIPFoundation.a', *vendor], 'zip')
    for source in c_sources:
        run(['xcrun', 'clang', '-DYAML_DECLARE_STATIC', '-O2', '-I' + str(yaml / 'include'), '-c', source, '-o', native / (source.stem + '.o')], source.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *[native / (s.stem + '.o') for s in c_sources]], 'yaml')
    flags = ['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', native, '-I', yaml / 'include']
    libraries = [native / 'libZIPFoundation.a', native / 'libCYaml.a']
    run([*flags, *original, tests[1], *libraries, '-o', work / 'original-control'], 'compile-original')
    run([*flags, *sources, tests[0], *libraries, '-o', work / 'tests'], 'compile56')
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios', ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    sandbox = work / 'tests.sb'; sandbox.write_text(policy)
    run(['sandbox-exec', '-f', sandbox, work / 'original-control', result], 'original-control')
    run(['sandbox-exec', '-f', sandbox, work / 'tests', result], 'tests')
    baseline = json.loads((result / 'original-control.json').read_text())
    actual = json.loads((result / 'results.json').read_text())
    if baseline['status'] != 'PASS_ORIGINAL_MIRRORNAME_404_REPRODUCED' or actual['status'] != 'PASS_DEPENDENCY56_MIRRORS':
        raise ValueError('Unexpected native control result')
    if hashes != {str(s.relative_to(ROOT)): digest(s) for s in paths}:
        raise ValueError('Inputs changed during the control run')
    receipt = dict(status=actual['status'], verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   checks=len(actual['checks']), original_failure_control=baseline['status'],
                   xcode=XCODE, source_sha256=hashes, results_sha256=digest(result / 'results.json'),
                   original_control_sha256=digest(result / 'original-control.json'), network_denied=True,
                   private_or_legacy_inputs_used=False, game_or_adapter_executed=False,
                   physical_device_tested=False, commands=commands)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], receipt['checks'])


if __name__ == '__main__':
    main()
