#!/usr/bin/env python3
"""Run retained native regressions against the actual merged build58 sources.

The unchanged JIT and picker harnesses accept a source-directory override through
their module constants. Each runs in a separate process with LANE/SOURCE set to
unified58. Their status names identify the retained harness, not an old app.
Dependency controls select sources through compile_release58, preserving its
identity/overlay checks. No real pairing data, network service or JIT is used.
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

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-unified58'
XCODE = 'Xcode 26.6\nBuild version 17F113'
HARNESSES = {
    'mirrors': ('DependencyMirrorTests.swift', 'PASS_DEPENDENCY56_MIRRORS'),
    'runtime': ('DependencyRuntimeTests.swift', 'PASS_DEPENDENCY56_RUNTIME'),
    'relocation': ('DependencyRelocationTests.swift', 'PASS_DEPENDENCY56_RELOCATION'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(paths):
    result = {}
    for path in sorted(set(paths)):
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError('Missing or aliased regression input: ' + str(path))
        result[str(path.relative_to(ROOT))] = sha(path)
    return result


def dependency_controls(work, env):
    from compile_release58 import selected_swift_sources, validate_overlay, validate_download_metadata, IDENTITY
    lock = json.loads((IDENTITY / 'Dependencies.json').read_text())
    validate_overlay(lock)
    validate_download_metadata()
    # These unguarded SwiftUI presentation files need UIKit's companion views.
    # The device compile and simulator UI suites cover them; this is the same
    # Foundation-only planner/installer execution boundary as the retained test.
    host_excluded = {'PlatformViews.swift', 'ShortcutViews.swift', 'IntegratedJITViews.swift'}
    sources = [p for p in selected_swift_sources() if p.name not in host_excluded]
    if any(p.parent != LANE / 'native' for p in sources):
        raise ValueError('All selected launcher Swift must come from unified58')
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c_sources = sorted((yaml / 'src').glob('*.c'))
    inputs = sources + vendor + [p for p in yaml.rglob('*') if p.is_file()]
    inputs += [Path(__file__).resolve(), ROOT / 'tools/compile_release58.py', IDENTITY / 'Dependencies.json']
    inputs += [LANE / 'tests' / harness for harness, _ in HARNESSES.values()]
    inputs += [LANE / name for name in ['RuntimeIdentity.json', 'CompatibilityDownloads.json', 'BuildContract.json']]
    hashes = snapshot(inputs)
    work.mkdir()
    native = work / 'native'
    native.mkdir()
    env = dict(env, CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'), SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    commands = []

    def run(command, label):
        command = list(map(str, command))
        commands.append(command)
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(label + ' failed; see ' + str(work / (label + '.log')))

    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-module-name', 'ZIPFoundation',
         '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule',
         '-o', native / 'libZIPFoundation.a', *vendor], 'compile-zip')
    objects = []
    for path in c_sources:
        obj = native / (path.stem + '.o')
        objects.append(obj)
        run(['xcrun', 'clang', '-DYAML_DECLARE_STATIC', '-O2', '-I' + str(yaml / 'include'),
             '-c', path, '-o', obj], 'compile-' + path.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *objects], 'archive-yaml')
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios',
                 ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    sandbox = work / 'controls.sb'
    sandbox.write_text(policy)
    reports = {}
    for name, (harness, expected) in HARNESSES.items():
        folder = work / name
        folder.mkdir()
        binary = folder / 'tests'
        run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', native, '-I', yaml / 'include',
             *sources, LANE / 'tests' / harness, native / 'libZIPFoundation.a', native / 'libCYaml.a',
             '-o', binary], 'compile-' + name)
        run(['sandbox-exec', '-f', sandbox, binary, folder / 'results'], 'run-' + name)
        report = folder / 'results/results.json'
        value = json.loads(report.read_text())
        if value.get('status') != expected or not isinstance(value.get('checks'), list) or not value['checks']:
            raise ValueError('Missing actual ' + name + ' controls')
        reports[name] = dict(status=expected, checks=len(value['checks']), results_sha256=sha(report),
                             results=str(report.relative_to(ROOT)))
        print(expected, len(value['checks']), flush=True)
    if snapshot(inputs) != hashes:
        raise ValueError('Merged source changed during dependency controls')
    validate_overlay(lock)
    receipt = dict(status='PASS_UNIFIED58_DEPENDENCY_NATIVE_CONTROLS', build_number='58',
                   everest_version='1.6642.0', tests=reports, checks=sum(r['checks'] for r in reports.values()),
                   source_sha256=hashes, commands=commands, xcode=XCODE, network_denied=True,
                   presentation_files_excluded=sorted(host_excluded),
                   private_dependencies_used=False, game_or_jit_executed=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def retained_controls(work, env, module, constant):
    # Use isolated interpreters so overriding these source selectors cannot affect
    # other tests or mutate the frozen modules on disk.
    code = ('import importlib, pathlib, sys; '
            'sys.path.insert(0, str(pathlib.Path.cwd()/"tools")); '
            'm=importlib.import_module(sys.argv[1]); '
            'setattr(m,sys.argv[2],pathlib.Path(sys.argv[3])); '
            'sys.argv=[m.__file__,"--work",sys.argv[4]]; m.main()')
    command = [sys.executable, '-c', code, module, constant, str(LANE), str(work)]
    with work.with_suffix('.log').open('w') as log:
        subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    receipt = json.loads((work / 'receipt.json').read_text())
    for command in receipt['commands']:
        # The JIT controller fixture deliberately includes the old implementation
        # as a comparison oracle; directly compiled production inputs must be58.
        for value in command:
            if Path(str(value)).suffix in {'.m', '.swift'} and '/experiments/ios-jit/' in str(value):
                if not str(value).startswith(str(LANE) + '/'):
                    raise ValueError('Retained harness compiled a different lane: ' + str(value))
    return receipt


def game_input_controls(work, env):
    work.mkdir()
    sources = [LANE / 'src/CJGameInputState.m', LANE / 'tests/GameInputStateTests.m']
    inputs = sources + [LANE / 'src/CJGameInputState.h', Path(__file__).resolve()]
    hashes = snapshot(inputs)
    command = ['xcrun', 'clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror',
               '-I' + str(LANE / 'src'), *map(str, sources), '-framework', 'Foundation', '-o', str(work / 'check')]
    with (work / 'compile.log').open('w') as log:
        subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    output = subprocess.check_output([str(work / 'check'), str(work / 'Documents')], cwd=ROOT, env=env, text=True)
    (work / 'run.log').write_text(output)
    if 'PASS_NATIVE_GAME_INPUT_STATE checks=14' not in output or snapshot(inputs) != hashes:
        raise ValueError('Merged game-input state controls did not pass')
    receipt = dict(status='PASS_NATIVE_GAME_INPUT_STATE', checks=14, source_sha256=hashes,
                   commands=[command], physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Use a fresh unaliased work directory under .build')
    env = dict(os.environ)
    env.setdefault('DEVELOPER_DIR', '/Applications/Xcode-26.6.app/Contents/Developer')
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('Native controls require Xcode26.6 /17F113')
    work.mkdir()
    wrapper_hash = sha(Path(__file__).resolve())
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = {
            'jit': executor.submit(retained_controls, work / 'jit', env, 'check_integrated57_native', 'LANE'),
            'picker': executor.submit(retained_controls, work / 'picker', env, 'check_document_picker_compatibility', 'SOURCE'),
            'dependencies': executor.submit(dependency_controls, work / 'dependencies', env),
            'game_inputs': executor.submit(game_input_controls, work / 'game-inputs', env),
        }
        reports = {name: future.result() for name, future in jobs.items()}
    if sha(Path(__file__).resolve()) != wrapper_hash:
        raise ValueError('Regression wrapper changed during checks')
    receipts = {name: work / ('game-inputs' if name == 'game_inputs' else name) / 'receipt.json'
                for name in reports}
    result = dict(status='PASS_UNIFIED58_NATIVE_CONTROLS', build_number='58',
                  source_selector=str(LANE.relative_to(ROOT)),
                  created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  wrapper_sha256=wrapper_hash,
                  receipts={name: dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
                            for name, path in receipts.items()},
                  reports=reports, game_or_jit_executed=False, actual_helper_launched=False,
                  physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
