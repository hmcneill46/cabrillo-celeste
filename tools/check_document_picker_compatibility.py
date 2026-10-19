#!/usr/bin/env python3
"""Check signing-picker policy/runtime chaining and compile the iOS module.

Host stubs do not establish a physical-device File Provider pass. The receipt
records the actual Xcode version and distinguishes all compilation targets.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/launcher-signing-picker'
XCODE = 'Xcode 26.6\nBuild version 17F113'


def snapshot(inputs):
    result = {}
    for path in inputs:
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError('Expected an unaliased source file: ' + str(path))
        result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    work = args.work.absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    work.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    pinned = Path('/Applications/Xcode-26.6.app/Contents/Developer')
    if 'DEVELOPER_DIR' not in env and pinned.exists():
        env['DEVELOPER_DIR'] = str(pinned)
    version = subprocess.check_output(['xcodebuild', '-version'], text=True, env=env).strip()
    if version != XCODE:
        raise SystemExit('Xcode 26.6 / 17F113 is required; actual version: ' + version)
    module = SOURCE / 'src/CJDocumentPickerCompatibility.m'
    tests = SOURCE / 'tests/DocumentPickerCompatibilityTests.m'
    inputs = [module, module.with_suffix('.h'), tests, Path(__file__).resolve()]
    before = snapshot(inputs)
    common = ['xcrun', 'clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror', '-I' + str(SOURCE / 'src')]
    commands = []

    def run(command):
        commands.append([str(value) for value in command])
        return subprocess.check_output(command, env=env, text=True, stderr=subprocess.STDOUT)

    run(common + ['-DCJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING=1', str(module), str(tests),
                  '-framework', 'Foundation', '-framework', 'Security', '-o', str(work / 'test')])
    scenarios = ['normal', 'missing-class', 'missing-method', 'bad-return', 'bad-argument', 'bad-arity',
                 'inherited', 'already-matched', 'invalid-entitlement', 'missing-bundle', 'livecontainer', 'real-entitlement']
    results = {scenario: run([work / 'test', scenario]).strip() for scenario in scenarios}
    targets = [('iphoneos', 'arm64-apple-ios15.0'), ('iphonesimulator', 'arm64-apple-ios15.0-simulator')]
    for sdk, target in targets:
        sdk_path = subprocess.check_output(['xcrun', '--sdk', sdk, '--show-sdk-path'], env=env, text=True).strip()
        run(common + ['-target', target, '-isysroot', sdk_path, '-c', str(module), '-o', str(work / (sdk + '.o'))])
    if snapshot(inputs) != before:
        raise RuntimeError('Source inputs changed while the compatibility check was running')
    receipt = dict(status='PASS_HOST_DOCUMENT_PICKER_COMPATIBILITY_CONTROLS', xcode=version,
                   scenarios=results, targets=[target for _, target in targets], physical_device_tested=False,
                   commands=commands, source_inputs_unchanged=True, source_sha256=before)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    for result in results.values():
        print(result)
    print('PASS production iOS and Simulator object compilation')


if __name__ == '__main__':
    main()
