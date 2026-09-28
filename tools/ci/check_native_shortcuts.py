#!/usr/bin/env python3
"""Check the accepted build50 coordinator from a public checkout.

No signed Shortcuts files, Apple account, game, FMOD SDK or device are needed.
The actual signed-template import/device evidence remains in the build49/50 reports.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
XCODE = 'Xcode 26.6\nBuild version 17F113'
sys.path.insert(0, str(ROOT / 'tools'))
import check_shortcut_files49 as workflows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/native-shortcuts')
    parser.add_argument('--developer-dir', default=os.environ.get(
        'DEVELOPER_DIR', '/Applications/Xcode-26.6.app/Contents/Developer'))
    args = parser.parse_args()
    work = ROOT / args.work
    if work.resolve() != work.absolute() or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    env = dict(os.environ, DEVELOPER_DIR=args.developer_dir)
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('The public shortcut checks require Xcode 26.6 / 17F113')
    work.mkdir(parents=True)
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios',
                 ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    sandbox = work / 'tests.sb'
    sandbox.write_text(policy)
    inputs = {Path(__file__)}

    def run_suite(name, test, implementation, expected, negative=False):
        files = [SOURCE / 'tests' / test, *implementation]
        inputs.update(files)
        for source in implementation:
            if source.with_suffix('.h').exists():
                inputs.add(source.with_suffix('.h'))
        binary = work / name
        command = ['xcrun', 'clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror',
                   '-Wno-deprecated-declarations', '-I' + str(SOURCE / 'src'),
                   *map(str, files), '-framework', 'Foundation', '-o', str(binary)]
        with (work / (name + '-compile.log')).open('w') as log:
            subprocess.run(command, env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        result = subprocess.run(['sandbox-exec', '-f', str(sandbox), str(binary), str(work / (name + '-journals'))],
                                env=env, cwd=ROOT, capture_output=True, text=True)
        (work / (name + '.log')).write_text(result.stdout + result.stderr)
        code = 1 if negative else 0
        if result.returncode != code or expected not in (result.stdout + result.stderr):
            raise RuntimeError(name + ' failed; inspect ' + str(work / (name + '.log')))
        return result.stdout.strip() if not negative else expected

    session = SOURCE / 'src/CJShortcutSession.m'
    platform = SOURCE / 'src/CJShortcutPlatform.m'
    options = SOURCE / 'src/CJPlatformOptions.m'
    route = SOURCE / 'src/CJShortcutRouteProbe.m'
    native = run_suite('session', 'ShortcutSessionTests.m', [session, platform, options],
                       'PASS 132 shortcut launch controls')
    cellular = run_suite('cellular', 'ShortcutCellularTests.m', [session, route],
                         'PASS 53 cellular route and ordering controls')
    original43 = ROOT / 'experiments/ios-jit/launcher-shortcut-guests/src/CJShortcutSession.m'
    original49 = ROOT / 'experiments/ios-jit/launcher-shortcut-import/src/CJShortcutSession.m'
    run_suite('original43', 'ShortcutSessionTests.m', [original43, platform, options],
              'FAIL native success completes without shortcut receipt', negative=True)
    run_suite('original49', 'ShortcutCellularTests.m', [original49, route],
              'FAIL cellular route reaches isolation without developer service', negative=True)
    branches = workflows.shortcut_checks()
    broken = workflows.url_connection_controls()
    if len(branches) != 36 or broken != 15:
        raise RuntimeError('Unexpected shortcut workflow coverage')
    for module in list(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if file:
            path = Path(file).resolve()
            if ROOT / 'tools' in path.parents and path.suffix == '.py':
                inputs.add(path)
    receipt = dict(status='PASS_PUBLIC_NATIVE_SHORTCUT_CHECKS', build=50, shortcut_revision=49,
                   native_checks=132, cellular_checks=53, shortcut_branches=36,
                   rejected_broken_url_connections=broken, original43_failure_reproduced=True,
                   original49_failure_reproduced=True, xcode=XCODE, native=native, cellular=cellular,
                   private_dependencies_used=False, signed_assets_used=False, physical_device_tested=False,
                   source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(inputs)})
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], '185 native checks, 36 branches, 15 broken URL controls')


if __name__ == '__main__':
    main()
