#!/usr/bin/env python3
"""Compile build55's selected production launcher and new Everest identity.

Builds the actual ZIPFoundation/CYaml and launcher Swift sources, generates the
Objective-C bridge header, then compiles the retained production Objective-C overlay for arm64/iOS15. Other native sources are hash-checked,
not compiled here. This does not link an app, build an IPA, enable JIT, or use
a device.
"""
import argparse
import datetime
import hashlib
import importlib
import json
import os
import re
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
OVERLAY = ROOT / 'experiments/ios-jit/launcher-copy-picker'
EVEREST = ROOT / 'experiments/ios-jit/launcher-everest6642'
EVEREST_VERSION = '1.6642.0'
EVEREST_COMMIT = '5abd7876821223c20711c1844a5187321d6e904c'
RETAINED54_MAP_SHA256 = '4cf32f28d39208363d79f5039c2181585ce6cf37c56ae2ef8960610fdc9518ac'
XCODE = 'Xcode 26.6\nBuild version 17F113'
TARGET = 'arm64-apple-ios15.0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def map_sha256(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_retained_build54(lock, root=ROOT, expected_count=253,
                              expected_map_sha256=RETAINED54_MAP_SHA256):
    """Check the published54 map itself, then every retained public input."""
    rows = lock.get('retained_build54_source_sha256')
    if not isinstance(rows, dict) or len(rows) != expected_count:
        raise ValueError('Expected all253 published build54 app-input pins')
    if map_sha256(rows) != expected_map_sha256:
        raise ValueError('Published build54 source-pin map differs')
    for name, expected in rows.items():
        if not isinstance(name, str) or not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('Malformed retained build54 source pin')
        relative = Path(name)
        path = (root / relative).absolute()
        if not relative.parts or relative.is_absolute() or '..' in relative.parts or relative.parts[0] in {'.private', '.build', 'artifacts', 'dist'}:
            raise ValueError('Retained build54 input is not a public repository path: ' + name)
        if root not in path.parents or path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError('Missing or aliased retained build54 source: ' + name)
        if sha(path) != expected:
            raise ValueError('Retained build54 source differs: ' + name)
    return dict(rows)


def require_expected_identity(identity):
    expected = {'Celeste': '1.4.0.0', 'CelesteIOS': '1.0.0',
                'Everest': EVEREST_VERSION, 'EverestCore': EVEREST_VERSION}
    if (not isinstance(identity, dict) or identity.get('schema') != 1 or
            identity.get('everestSourceCommit') != EVEREST_COMMIT or
            identity.get('compatibilityPolicy') != 1 or identity.get('builtins') != expected):
        raise ValueError('Expected actual build55 Everest1.6642 source/runtime identity')
    return identity


def selected_production_sources(build, lock):
    """Use the real compiler selectors and reject an old identity or picker main."""
    native = list(build.selected_native_sources(lock))
    swift = list(build.selected_swift_sources())
    expected_native = sorted([build.OVERLAY / 'src/main.m' if path.name == 'main.m' else path
                              for path in (build.SOURCE / 'src').iterdir() if path.suffix in {'.c', '.m'}] +
                             [build.OVERLAY / 'src/CJDocumentPickerCompatibility.m'])
    expected_swift = sorted([build.EVEREST_OVERLAY / 'native/RuntimeIdentity.swift'
                             if path.name == 'RuntimeIdentity.swift' else path
                             for path in (build.SOURCE / 'native').glob('*.swift')])
    if sorted(native) != expected_native or len({path.stem for path in native}) != len(native):
        raise ValueError('Compiler must retain the exact54 native source selection')
    if sorted(swift) != expected_swift or build.SOURCE / 'native/RuntimeIdentity.swift' in swift:
        raise ValueError('Compiler must select the actual55 RuntimeIdentity.swift')
    compiled_objc = [build.OVERLAY / 'src/main.m', build.OVERLAY / 'src/CJDocumentPickerCompatibility.m']
    return native, swift, compiled_objc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/everest6642-compile')
    parser.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'))
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
    build = importlib.import_module('compile_release55')
    if build.ROOT != ROOT or build.SOURCE != BASE or build.OVERLAY != OVERLAY or build.EVEREST_OVERLAY != EVEREST:
        raise ValueError('Unexpected production55 compiler source roots')
    lock_path = build.IDENTITY / 'Dependencies.json'
    lock = json.loads(lock_path.read_text())
    retained54 = validate_retained_build54(lock)
    identity = require_expected_identity(build.validate_runtime_identity())
    selected_native, swift_sources, native_sources = selected_production_sources(build, lock)
    build_identity = json.loads((build.IDENTITY / 'BuildIdentity.json').read_text())
    if str(build_identity.get('build_number')) != '55' or build_identity.get('version') != '0.25.0':
        raise ValueError('Expected Cabrillo0.25.0/build55')
    zip_sources = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    yaml_sources = sorted((yaml / 'src').glob('*.c'))
    inputs = {Path(__file__).resolve(), Path(build.__file__).resolve(), lock_path,
              *selected_native, *native_sources, *zip_sources, *yaml_sources, *swift_sources}
    inputs.update(ROOT / name for name in retained54)
    inputs.update(path for path in build.IDENTITY.iterdir() if path.is_file())
    inputs.update([EVEREST / 'RuntimeIdentity.json', EVEREST / 'managed/RuntimeIdentity.cs'])
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
    validate_retained_build54(lock)
    require_expected_identity(build.validate_runtime_identity())
    for name, digest in hashes.items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('Production input changed during compilation: ' + name)
    outputs = {str(path.relative_to(work)): sha(path) for path in sorted(native.rglob('*'))
               if path.is_file()}
    receipt = dict(status='PASS_PRODUCTION_IOS_LAUNCHER_COMPILE', build_number='55', version='0.25.0',
                   everest_version=EVEREST_VERSION, everest_source_commit=EVEREST_COMMIT,
                   runtime_identity=identity, runtime_identity_manifest_sha256=sha(EVEREST / 'RuntimeIdentity.json'),
                   retained_build54_app_input_count=len(retained54),
                   retained_build54_source_pin_map_sha256=map_sha256(retained54),
                   retained_build54_app_inputs_preserved=True,
                   selected_native_sources=[str(path.relative_to(ROOT)) for path in selected_native],
                   compiled_objc_sources_paths=[str(path.relative_to(ROOT)) for path in native_sources],
                   selected_swift_sources=[str(path.relative_to(ROOT)) for path in swift_sources],
                   created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   target=TARGET, xcode=XCODE, sdk_version=sdk_version,
                   source_sha256=hashes, output_sha256=outputs, commands=commands,
                   compiled_swift_sources=len(zip_sources) + len(swift_sources),
                   compiled_c_sources=len(yaml_sources), compiled_objc_sources=len(native_sources),
                   production_test_seam_absent=True,
                   app_linked=False, ipa_built=False, runtime_dependencies_used=False,
                   fmod_sdk_used=False, game_files_used=False, signing_credentials_used=False,
                   jit_executed=False, physical_device_tested=False,
                   managed_runtime_identity_validated=True, managed_payload_compiled=False,
                   broader_selected_native_sources_compiled=False,
                   scope='Selected production55 Swift/new runtime identity and retained54 main/helper arm64/iOS15 compilation with real Swift bridge; other selected native sources are hash-checked only. No managed/runtime/IPA or device test.')
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__':
    main()
