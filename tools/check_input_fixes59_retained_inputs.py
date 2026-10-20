#!/usr/bin/env python3
"""Exercise native saved-game detection using BuildInfo and recipe from an IPA.

Only synthetic source/asset markers are written. The control uses actual
CJGameInputsAvailable, never user game code or assets. --expect-rejection records
the first faulty integration IPA as a negative control, not as an accepted build.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-input-fixes59'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ipa', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--expect-rejection', action='store_true')
    args = parser.parse_args()
    work, ipa = args.work.absolute(), args.ipa.absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased .build work directory')
    if ipa.resolve() != ipa or not ipa.is_file():
        raise ValueError('Choose an existing unaliased IPA')
    sources = [LANE / 'src/CJGameInputState.m', LANE / 'tests/RetainedPackageInputTests.m']
    inputs = sources + [LANE / 'src/CJGameInputState.h', Path(__file__).resolve()]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    ipa_hash = sha(ipa)
    work.mkdir()
    prefix = 'Payload/CelesteJITEverest.app/'
    with zipfile.ZipFile(ipa) as archive:
        for name in ['BuildInfo.json', 'OwnedGameRecipe.json']:
            (work / name).write_bytes(archive.read(prefix + name))
    env = dict(os.environ)
    env.setdefault('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer')
    version = subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip()
    if version != 'Xcode 26.6\nBuild version 17F113':
        raise ValueError('Expected Xcode26.6 /17F113')
    command = ['xcrun', 'clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror', '-I' + str(LANE / 'src'),
               *map(str, sources), '-framework', 'Foundation', '-o', str(work / 'check')]
    with (work / 'compile.log').open('w') as log:
        subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    run_command = [str(work / 'check'), str(work / 'BuildInfo.json'), str(work / 'OwnedGameRecipe.json'), str(work / 'fixtures')]
    with (work / 'run.log').open('w') as log:
        result = subprocess.run(run_command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=30)
    report = json.loads((work / 'fixtures/results.json').read_text())
    expected = 'REJECTED_PACKAGE_NATIVE_GAME_INPUT_METADATA' if args.expect_rejection else 'PASS_PACKAGED_NATIVE_RETAINED_INPUTS'
    if result.returncode != (3 if args.expect_rejection else 0) or report.get('status') != expected:
        raise ValueError('Packaged retained-input control failed: ' + str(work / 'run.log'))
    if hashes != {str(p.relative_to(ROOT)): sha(p) for p in inputs} or sha(ipa) != ipa_hash:
        raise ValueError('Inputs changed during package controls')
    receipt = dict(status='PASS_NEGATIVE_RETAINED_INPUT_REGRESSION' if args.expect_rejection else expected,
                   ipa=str(ipa.relative_to(ROOT)), ipa_sha256=ipa_hash, source_sha256=hashes,
                   packaged_metadata_sha256={name:sha(work / name) for name in ['BuildInfo.json', 'OwnedGameRecipe.json']},
                   xcode=version, commands=[command, run_command], report=report,
                   actual_production_function_used=True, game_files_used=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], len(report['checks']), flush=True)


if __name__ == '__main__':
    main()
