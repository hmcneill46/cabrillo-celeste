#!/usr/bin/env python3
"""Compile the actual build58 SwiftUI host and Objective-C integration for iOS15.

Use the production source selectors, real ZIPFoundation/CYaml and generated
Swift bridge header. SDL/Mono graphics implementation files require separately
built dependencies and remain covered by the full IPA build; this source-only
check records them but does not compile them. No game, SDK licence, signing,
linking, helper execution or device is needed.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess

import compile_release58 as build
from check_integrated57_compile import require_expected_identity, sha

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-unified58'
XCODE = 'Xcode 26.6\nBuild version 17F113'
TARGET = 'arm64-apple-ios15.0'
EXTERNAL_DEPENDENCY_SOURCES = {'CJGraphicsManaged.m', 'CJGraphicsPlatform.m'}


def selected_production_sources(lock):
    if build.ROOT != ROOT or build.SOURCE != LANE or build.IDENTITY != ROOT / 'release/app58':
        raise ValueError('Unexpected combined production compiler source roots')
    build.validate_overlay(lock)
    build.validate_download_metadata()
    native = list(build.selected_native_sources(lock))
    swift = list(build.selected_swift_sources())
    expected_native = {LANE / 'src' / name for name in [
        'main.m', 'CJPlatformOptions.m', 'CJIntegratedJITCoordinator.m',
        'CJIntegratedJITLaunch.m', 'CJDocumentPickerCompatibility.m', 'CJGameInputState.m']}
    expected_swift = {LANE / 'native' / name for name in [
        'LauncherUI.swift', 'TouchEditor.swift', 'TouchProfile.swift', 'GameFilesHelpView.swift',
        'IntegratedJITViews.swift', 'DependencyInstaller.swift', 'DependencyPlan.swift',
        'ModLibrary.swift', 'RuntimeIdentity.swift']}
    if (not expected_native.issubset(native) or not expected_swift.issubset(swift)
            or any(p.parent != LANE / 'src' for p in native)
            or any(p.parent != LANE / 'native' for p in swift)
            or len({p.stem for p in native}) != len(native)
            or len({p.stem for p in swift}) != len(swift)):
        raise ValueError('Production source selectors omit or substitute merged58 features')
    objc = [p for p in native if p.suffix == '.m' and p.name not in EXTERNAL_DEPENDENCY_SOURCES]
    return native, swift, objc


def snapshot(paths):
    result = {}
    for path in sorted(set(paths)):
        if not path.is_file() or path.is_symlink() or path.resolve() != path or ROOT not in path.parents:
            raise ValueError('Missing or aliased source input: ' + str(path))
        result[str(path.relative_to(ROOT))] = sha(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/unified58-compile')
    parser.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode-26.6.app/Contents/Developer'))
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    env = dict(os.environ, DEVELOPER_DIR=args.developer_dir, PYTHONDONTWRITEBYTECODE='1')
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('The launcher compile check requires Xcode26.6 /17F113')
    sdk = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'], env=env, text=True).strip()
    sdk_version = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-version'], env=env, text=True).strip()
    if sdk_version != '26.5':
        raise ValueError('The launcher compile check requires iPhoneOS SDK26.5')
    lock_path = build.IDENTITY / 'Dependencies.json'
    lock = json.loads(lock_path.read_text())
    identity = require_expected_identity(build.validate_runtime_identity())
    selected_native, swift_sources, objc_sources = selected_production_sources(lock)
    build_identity = json.loads((build.IDENTITY / 'BuildIdentity.json').read_text())
    if (str(build_identity.get('build_number')), build_identity.get('version')) != ('58', '0.29.0'):
        raise ValueError('Expected Cabrillo0.29.0/build58')
    zip_sources = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    yaml_sources = sorted((yaml / 'src').glob('*.c'))
    if not zip_sources or not yaml_sources:
        raise ValueError('Production vendor source files are missing')
    inputs = {Path(__file__).resolve(), Path(build.__file__).resolve(), lock_path,
              ROOT / 'tools/check_integrated57_compile.py',
              *selected_native, *swift_sources, *zip_sources, *yaml_sources}
    inputs.update(p for p in build.IDENTITY.iterdir() if p.is_file())
    inputs.update(LANE / name for name in ['CompatibilityDownloads.json', 'BuildContract.json',
                                         'RuntimeIdentity.json', 'managed/RuntimeIdentity.cs'])
    # The selected compiler validates the published historical pin maps too.
    for number in range(53, 58):
        inputs.add(ROOT / 'tools' / ('compile_release' + str(number) + '.py'))
        inputs.add(ROOT / 'release' / ('app' + str(number)) / 'Dependencies.json')
    for folder in [LANE / 'src', yaml / 'include', yaml / 'src',
                   ROOT / 'experiments/ios-jit/managed-canary/src']:
        inputs.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.h', '.modulemap'})
    hashes = snapshot(inputs)
    work.mkdir(parents=True)
    native = work / 'native'; native.mkdir()
    env.update(CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'), SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    commands = []

    def run(command, name):
        command = list(map(str, command)); commands.append(command)
        with (work / (name + '.log')).open('w') as log:
            subprocess.run(command, env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('PASS ' + name, flush=True)

    swift_flags = ['-swift-version', '5', '-O', '-g', '-target', TARGET, '-sdk', sdk,
                   '-module-cache-path', work / 'module-cache']
    run(['xcrun', 'swiftc', *swift_flags, '-module-name', 'ZIPFoundation', '-emit-library', '-static',
         '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule',
         '-o', native / 'libZIPFoundation.a', *zip_sources], 'compile-zipfoundation')
    yaml_objects = []
    for source in yaml_sources:
        obj = native / (source.stem + '.o')
        run(['xcrun', 'clang', '-target', TARGET, '-isysroot', sdk, '-DYAML_DECLARE_STATIC',
             '-O2', '-g', '-I' + str(yaml / 'include'), '-c', source, '-o', obj], 'compile-cyaml-' + source.stem)
        yaml_objects.append(obj)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *yaml_objects], 'archive-cyaml')
    run(['xcrun', 'swiftc', *swift_flags, '-module-name', 'CJLauncher', '-I', native, '-I', yaml / 'include',
         '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'CJLauncher.swiftmodule',
         '-emit-objc-header-path', native / 'CJLauncher-Swift.h', '-o', native / 'libCJLauncher.a',
         *swift_sources], 'compile-launcher-swift')
    header = (native / 'CJLauncher-Swift.h').read_text()
    if any(name not in header for name in ['CJTouchStore', 'CJTouchEditorBridge', 'CJLauncherBridge']):
        raise RuntimeError('The real Swift bridge does not expose the merged launcher/editor')
    includes = [LANE / 'src', native, ROOT / 'experiments/ios-jit/managed-canary/src']
    for source in objc_sources:
        run(['xcrun', 'clang', '-target', TARGET, '-isysroot', sdk, '-O2', '-g', '-Wall', '-Wextra',
             '-Werror', '-Wno-deprecated-declarations', '-fobjc-arc',
             *(['-fno-omit-frame-pointer'] if source.name == 'main.m' else []),
             *('-I' + str(path) for path in includes), '-c', source,
             '-o', native / (source.stem + '.o')], 'compile-' + source.stem)
    symbol_command = ['xcrun', 'nm', '-g', str(native / 'CJDocumentPickerCompatibility.o')]
    symbols = subprocess.check_output(symbol_command, env=env, text=True); commands.append(symbol_command)
    if 'CJDocumentPickerCompatibilityTestEnvironment' in symbols or '_CJDocumentPickerCompatibilityPrepare' not in symbols:
        raise RuntimeError('Picker production entry point is missing or its test seam is present')
    (work / 'production-symbols.log').write_text(symbols)
    selected_production_sources(lock)
    require_expected_identity(build.validate_runtime_identity())
    if snapshot(inputs) != hashes:
        raise RuntimeError('Production inputs changed during compilation')
    outputs = {str(p.relative_to(work)): sha(p) for p in sorted(native.rglob('*')) if p.is_file()}
    receipt = dict(status='PASS_UNIFIED58_PRODUCTION_IOS_LAUNCHER_COMPILE', build_number='58', version='0.29.0',
                   runtime_identity=identity, runtime_identity_manifest_sha256=sha(LANE / 'RuntimeIdentity.json'),
                   selected_native_sources=[str(p.relative_to(ROOT)) for p in selected_native],
                   compiled_objc_sources_paths=[str(p.relative_to(ROOT)) for p in objc_sources],
                   selected_swift_sources=[str(p.relative_to(ROOT)) for p in swift_sources],
                   created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   target=TARGET, xcode=XCODE, sdk_version=sdk_version, source_sha256=hashes,
                   output_sha256=outputs, commands=commands, compiled_swift_sources=len(zip_sources) + len(swift_sources),
                   compiled_c_sources=len(yaml_sources), compiled_objc_sources=len(objc_sources),
                   production_test_seam_absent=True, app_linked=False, ipa_built=False,
                   runtime_dependencies_used=False, fmod_sdk_used=False, game_files_used=False,
                   signing_credentials_used=False, jit_executed=False, physical_device_tested=False,
                   managed_runtime_identity_validated=True, managed_payload_compiled=False,
                   dependency_metadata_validated=True, historical_overlays_validated=True,
                   external_dependency_sources_not_compiled=sorted(EXTERNAL_DEPENDENCY_SOURCES),
                   broader_selected_native_sources_compiled=False,
                   scope='Production58 Swift and Objective-C host integration for arm64/iOS15 with real Swift bridge. SDL/Mono implementation, helper and full IPA builds are separate.')
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__':
    main()
