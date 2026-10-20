#!/usr/bin/env python3
"""Run production build56 dependency transport/runtime controls on an isolated host.

Compiles the selected production Swift and public ZIP/YAML dependencies. Each
standalone harness exercises real filesystem/ZIP/planner/installer code. Network
and private/legacy/game inputs are denied during these controls. No game or JIT
is executed.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-dependency-downloads'
XCODE = 'Xcode 26.6\nBuild version 17F113'
HARNESSES = {'mirrors': ('DependencyMirrorTests.swift', 'PASS_DEPENDENCY56_MIRRORS'),
             'runtime': ('DependencyRuntimeTests.swift', 'PASS_DEPENDENCY56_RUNTIME'),
             'relocation': ('DependencyRelocationTests.swift', 'PASS_DEPENDENCY56_RELOCATION')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/dependency56-controls')
    parser.add_argument('--test', choices=['all', *HARNESSES], default='all')
    parser.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'))
    args = parser.parse_args()
    from compile_release56 import selected_swift_sources, validate_overlay, IDENTITY
    validate_overlay(json.loads((IDENTITY / 'Dependencies.json').read_text()))
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh unaliased control directory under .build')
    env = dict(os.environ, DEVELOPER_DIR=args.developer_dir,
               CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'), SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('Expected Xcode26.6 /17F113')
    names = list(HARNESSES) if args.test == 'all' else [args.test]
    sources = [p for p in selected_swift_sources() if p.name not in {'PlatformViews.swift', 'ShortcutViews.swift'}]
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c_sources = sorted((yaml / 'src').glob('*.c'))
    inputs = set(sources + vendor + c_sources + [Path(__file__).resolve(), ROOT / 'tools/compile_release56.py', IDENTITY / 'Dependencies.json'])
    inputs.update(LANE / 'tests' / HARNESSES[name][0] for name in names)
    inputs.update(LANE / name for name in ['CompatibilityDownloads.json', 'BuildContract.json'])
    inputs.update(p for p in yaml.rglob('*') if p.is_file())
    for path in inputs:
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError('Missing or aliased production control input: ' + str(path))
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in sorted(inputs)}
    work.mkdir(parents=True)
    native = work / 'native'; native.mkdir()
    commands = []

    def run(command, name):
        command = list(map(str, command)); commands.append(command)
        with (work / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((work / (name + '.log')).read_text(errors='replace')[-15000:])
            raise RuntimeError(name + ' failed')
        print('PASS ' + name, flush=True)

    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-module-name', 'ZIPFoundation', '-emit-library', '-static',
         '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule', '-o', native / 'libZIPFoundation.a', *vendor], 'compile-zip')
    objects = []
    for path in c_sources:
        obj = native / (path.stem + '.o'); objects.append(obj)
        run(['xcrun', 'clang', '-DYAML_DECLARE_STATIC', '-O2', '-I' + str(yaml / 'include'), '-c', path, '-o', obj], 'compile-' + path.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *objects], 'archive-yaml')
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios', ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    sandbox = work / 'controls.sb'; sandbox.write_text(policy)
    results = {}
    for name in names:
        harness, expected = HARNESSES[name]
        folder = work / name; folder.mkdir()
        binary = folder / 'tests'
        run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', native, '-I', yaml / 'include',
             *sources, LANE / 'tests' / harness, native / 'libZIPFoundation.a', native / 'libCYaml.a', '-o', binary], 'compile-' + name)
        run(['sandbox-exec', '-f', sandbox, binary, folder / 'results'], 'run-' + name)
        report = folder / 'results/results.json'
        value = json.loads(report.read_text())
        if value.get('status') != expected or not isinstance(value.get('checks'), list) or not value['checks']:
            raise ValueError('Expected actual ' + name + ' controls with individual checks')
        results[name] = dict(status=value['status'], checks=len(value['checks']), results_sha256=sha(report), results=str(report.relative_to(ROOT)))
    if hashes != {str(path.relative_to(ROOT)): sha(path) for path in sorted(inputs)}:
        raise ValueError('Production source changed during controls')
    validate_overlay(json.loads((IDENTITY / 'Dependencies.json').read_text()))
    receipt = dict(status='PASS_DEPENDENCY56_NATIVE_CONTROLS', created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   build_number='56', everest_version='1.6642.0', tests=results, checks=sum(r['checks'] for r in results.values()),
                   source_sha256=hashes, commands=commands, xcode=XCODE, network_denied=True, private_dependencies_used=False,
                   game_executed=False, jit_executed=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], receipt['checks'], flush=True)


if __name__ == '__main__':
    main()
