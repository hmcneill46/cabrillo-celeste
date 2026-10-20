#!/usr/bin/env python3
"""Compile build54's production iOS launcher without runtime or licensed inputs.

Builds the actual ZIPFoundation/CYaml and launcher Swift sources, generates the
Objective-C bridge header, then compiles the production Objective-C overlay for
arm64/iOS15. This does not link an app, build an IPA, enable JIT, or use a device.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
OVERLAY = ROOT / 'experiments/ios-jit/launcher-copy-picker'
XCODE = 'Xcode 26.6\nBuild version 17F113'
TARGET = 'arm64-apple-ios15.0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/copy-picker-compile')
    parser.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR'))
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    env = dict(os.environ)
    if args.developer_dir:
        env['DEVELOPER_DIR'] = args.developer_dir
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('The launcher compile check requires Xcode26.6 /17F113')
    sdk = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'],
                                  env=env, text=True).strip()
    sdk_version = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-version'],
                                          env=env, text=True).strip()
    if sdk_version != '26.5':
        raise ValueError('The launcher compile check requires iPhoneOS SDK26.5')
    native_sources = [OVERLAY / 'src/main.m', OVERLAY / 'src/CJDocumentPickerCompatibility.m']
    zip_sources = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    yaml_sources = sorted((yaml / 'src').glob('*.c'))
    swift_sources = sorted((BASE / 'native').glob('*.swift'))
    inputs = {Path(__file__).resolve(), *native_sources, *zip_sources, *yaml_sources, *swift_sources}
    for folder in [BASE / 'src', OVERLAY / 'src', yaml / 'include', yaml / 'src',
                   ROOT / 'experiments/ios-jit/managed-canary/src']:
        inputs.update(path for path in folder.rglob('*') if path.is_file()
                      and path.suffix in {'.h', '.modulemap'})
    if not zip_sources or not yaml_sources or not swift_sources:
        raise ValueError('Production Swift/vendor source files are missing')
    for path in inputs:
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError('Missing or aliased production input: ' + str(path))
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in sorted(inputs)}
    work.mkdir(parents=True)
    native = work / 'native'
    native.mkdir()
    env.update(CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'),
               SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    commands = []

    def run(command, name):
        command = list(map(str, command))
        commands.append(command)
        with (work / (name + '.log')).open('w') as log:
            subprocess.run(command, env=env, cwd=ROOT, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        print('PASS ' + name, flush=True)

    swift_flags = ['-swift-version', '5', '-O', '-g', '-target', TARGET, '-sdk', sdk,
                   '-module-cache-path', work / 'module-cache']
    run(['xcrun', 'swiftc', *swift_flags, '-module-name', 'ZIPFoundation',
         '-emit-library', '-static', '-emit-module', '-emit-module-path',
         native / 'ZIPFoundation.swiftmodule', '-o', native / 'libZIPFoundation.a',
         *zip_sources], 'compile-zipfoundation')
    yaml_objects = []
    for source in yaml_sources:
        obj = native / (source.stem + '.o')
        run(['xcrun', 'clang', '-target', TARGET, '-isysroot', sdk,
             '-DYAML_DECLARE_STATIC', '-O2', '-g', '-I' + str(yaml / 'include'),
             '-c', source, '-o', obj], 'compile-cyaml-' + source.stem)
        yaml_objects.append(obj)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *yaml_objects],
        'archive-cyaml')
    run(['xcrun', 'swiftc', *swift_flags, '-module-name', 'CJLauncher',
         '-I', native, '-I', yaml / 'include', '-emit-library', '-static',
         '-emit-module', '-emit-module-path', native / 'CJLauncher.swiftmodule',
         '-emit-objc-header-path', native / 'CJLauncher-Swift.h',
         '-o', native / 'libCJLauncher.a', *swift_sources], 'compile-launcher-swift')
    includes = [OVERLAY / 'src', BASE / 'src', native,
                ROOT / 'experiments/ios-jit/managed-canary/src']
    for source in native_sources:
        run(['xcrun', 'clang', '-target', TARGET, '-isysroot', sdk,
             '-O2', '-g', '-Wall', '-Wextra', '-Werror', '-Wno-deprecated-declarations',
             '-fobjc-arc', *(['-fno-omit-frame-pointer'] if source.name == 'main.m' else []),
             *('-I' + str(path) for path in includes), '-c', source,
             '-o', native / (source.stem + '.o')], 'compile-' + source.stem)
    symbol_command = ['xcrun', 'nm', '-g', str(native / 'CJDocumentPickerCompatibility.o')]
    symbols = subprocess.check_output(symbol_command, env=env, text=True)
    commands.append(symbol_command)
    if 'CJDocumentPickerCompatibilityTestEnvironment' in symbols:
        raise RuntimeError('The production object contains the test-only entitlement seam')
    if '_CJDocumentPickerCompatibilityPrepare' not in symbols:
        raise RuntimeError('The production compatibility entry point is missing')
    (work / 'production-symbols.log').write_text(symbols)
    for name, digest in hashes.items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('Production input changed during compilation: ' + name)
    outputs = {str(path.relative_to(work)): sha(path) for path in sorted(native.rglob('*'))
               if path.is_file()}
    receipt = dict(status='PASS_PRODUCTION_IOS_LAUNCHER_COMPILE', build_number='54',
                   created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   target=TARGET, xcode=XCODE, sdk_version=sdk_version,
                   source_sha256=hashes, output_sha256=outputs, commands=commands,
                   compiled_swift_sources=len(zip_sources) + len(swift_sources),
                   compiled_c_sources=len(yaml_sources), compiled_objc_sources=len(native_sources),
                   production_test_seam_absent=True,
                   app_linked=False, ipa_built=False, runtime_dependencies_used=False,
                   fmod_sdk_used=False, game_files_used=False, signing_credentials_used=False,
                   jit_executed=False, physical_device_tested=False,
                   scope='Production arm64/iOS15 source compilation and Swift bridge integration only.')
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__':
    main()
