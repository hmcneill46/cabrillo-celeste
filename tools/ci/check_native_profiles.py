#!/usr/bin/env python3
"""Run current production save/backup tests using only files in a public checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/ios-jit/launcher-everest6580'
XCODE = 'Xcode 26.6\nBuild version 17F113'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', default='.build/ci/native-profiles')
    p.add_argument('--developer-dir', default=os.environ.get(
        'DEVELOPER_DIR', '/Applications/Xcode-26.6.app/Contents/Developer'))
    args = p.parse_args()
    work = ROOT / args.work
    if work.resolve() != work.absolute() or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    env = dict(os.environ, DEVELOPER_DIR=args.developer_dir,
               CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'),
               SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('The public host checks require Xcode 26.6 / 17F113')
    work.mkdir(parents=True)
    native = work / 'native'
    native.mkdir()
    sources = sorted(f for f in (SOURCE / 'native').glob('*.swift') if f.name != 'PlatformViews.swift')
    sources += [SOURCE / 'tests/ProfileBackupTests.swift', SOURCE / 'tests/SaveTransferTests.swift']
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c_sources = sorted((yaml / 'src').glob('*.c'))
    digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    inputs = sources + vendor + c_sources + [Path(__file__)]
    hashes = {str(f.relative_to(ROOT)): digest(f) for f in inputs}

    def run(command, name):
        with (work / (name + '.log')).open('w') as log:
            result = subprocess.run(list(map(str, command)), cwd=ROOT, env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((work / (name + '.log')).read_text()[-12000:])
            raise RuntimeError(name + ' failed')

    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-module-name', 'ZIPFoundation',
         '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule',
         '-o', native / 'libZIPFoundation.a', *vendor], 'zip')
    for f in c_sources:
        run(['xcrun', 'clang', '-DYAML_DECLARE_STATIC', '-O2', '-I' + str(yaml / 'include'),
             '-c', f, '-o', native / (f.stem + '.o')], f.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a',
         *[native / (f.stem + '.o') for f in c_sources]], 'yaml')
    run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-g', '-I', native,
         '-I', yaml / 'include', *sources, native / 'libZIPFoundation.a', native / 'libCYaml.a',
         '-o', work / 'tests'], 'compile')
    # Fresh Actions runners have none of these inputs. Also deny private input access locally.
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios',
                 ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    (work / 'tests.sb').write_text(policy)
    run(['sandbox-exec', '-f', work / 'tests.sb', work / 'tests', work / 'results'], 'tests')
    result = json.loads((work / 'results/results.json').read_text())
    if result['status'] != 'PASS_PROFILE_BACKUPS' or len(result['checks']) != 119:
        raise ValueError('Expected all 119 current profile/transfer checks')
    if hashes != {str(f.relative_to(ROOT)): digest(f) for f in inputs}:
        raise ValueError('Source changed during testing')
    receipt = dict(status='PASS_PUBLIC_NATIVE_PROFILE_CHECKS', checks=len(result['checks']),
                   xcode=XCODE, source_sha256=hashes, results_sha256=digest(work / 'results/results.json'),
                   private_dependencies_used=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], receipt['checks'])


if __name__ == '__main__':
    main()
