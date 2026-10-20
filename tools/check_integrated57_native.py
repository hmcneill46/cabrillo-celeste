#!/usr/bin/env python3
"""Run actual57 JIT launch/provider and protected pairing/coordinator controls.

Uses synthetic plist data, in-memory preferences and a stubbed service boundary.
No debugger/helper, real VPN service, signing identity or game is used.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess

from build_stikjit57 import ROOT, LANE, sha, XCODE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/integrated57-native')
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Use a fresh unaliased work directory under .build')
    env = dict(os.environ, DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'))
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('Native controls require Xcode26.6 /17F113')
    sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=env, text=True).strip()
    work.mkdir(parents=True)
    commands = []
    reports = {}
    sources = {Path(__file__).resolve(), ROOT/'tools/build_stikjit57.py',
               ROOT/'experiments/ios-jit/launcher-shortcut-cellular/src/CJPlatformOptions.m',
               ROOT/'experiments/ios-jit/launcher-shortcut-cellular/src/CJPlatformOptions.h',
               ROOT/'experiments/ios-jit/launcher-shortcut-cellular/src/CJShortcutPlatform.h'}
    cases = [
            ('controller', ['tests/IntegratedJITControllerTests.m', 'src/CJPlatformOptions.m', 'src/CJIntegratedJITLaunch.m']),
            ('coordinator', ['tests/IntegratedJITCoordinatorTests.m', 'src/CJIntegratedJITCoordinator.m'])]
    for _, files in cases:
        sources.update(LANE/path for path in files)
    sources.update(LANE/'src'/p for p in ['CJPlatformOptions.h', 'CJIntegratedJITLaunch.h', 'CJIntegratedJITCoordinator.h'])
    hashes = {str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
    for name, files in cases:
        inputs = [LANE/path for path in files]
        binary = work/name
        command = ['xcrun', 'clang', '-isysroot', sdk, '-fobjc-arc', '-O2', '-g',
                   '-Wall', '-Wextra', '-Werror', '-Wno-deprecated-declarations',
                   '-I'+str(LANE/'src'), '-I'+str(ROOT/'experiments/ios-jit/launcher-shortcut-cellular/src'),
                   '-framework', 'Foundation', '-framework', 'Security', *map(str, inputs), '-o', str(binary)]
        commands.append(command)
        with (work/(name+'-compile.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        results = work/(name+'-results')
        results.mkdir()
        argument = results/'results.json' if name=='controller' else results
        command = [str(binary), str(argument)]
        commands.append(command)
        with (work/(name+'-run.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
        report = json.loads((results/'results.json').read_text())
        expected = 'PASS_INTEGRATED_JIT_CONTROLLER_POLICY' if name=='controller' else 'PASS_INTEGRATED_JIT_COORDINATOR_CONTROLS'
        if report.get('status') != expected:
            raise ValueError('Unexpected native result for '+name)
        reports[name] = report
        print(expected, flush=True)
    if any(sha(ROOT/name) != digest for name, digest in hashes.items()):
        raise ValueError('A production or fixture input changed during native controls')
    receipt = dict(status='PASS_INTEGRATED_JIT57_NATIVE_CONTROLS',
                   created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   source_sha256=hashes,
                   reports=reports, commands=commands, game_or_jit_executed=False,
                   actual_helper_launched=False, physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__':
    main()
