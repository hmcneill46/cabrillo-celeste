#!/usr/bin/env python3
"""Build pinned StikJIT and Cabrillo's separate, unsigned iOS helper.

StikJIT's Swift code is compiled here. Its upstream archive contains a prebuilt
idevice FFI static library; the lock and receipt disclose that binary input.
Nothing is linked into the iOS15 host app. No pairing/device data is consumed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-integrated-jit'
LOCK = ROOT / 'release/stikjit57.json'
COMMIT = '32287268fa5824f9edce4cb359f5833ce0cf7b00'
ARCHIVE_SHA256 = 'ed38ff2e296b1de00b7b664f8ff10b2e10c843375b9422e5cef7fb1d6b42e3d0'
XCODE = 'Xcode 26.6\nBuild version 17F113'
TARGET = 'arm64-apple-ios17.4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def lock_value():
    value = json.loads(LOCK.read_text())
    if (value.get('commit') != COMMIT or value.get('archive_sha256') != ARCHIVE_SHA256
            or value.get('archive_bytes') != 8733311
            or value.get('url') != 'https://codeload.github.com/StikDebug/StikJIT/tar.gz/' + COMMIT
            or value.get('minimum_helper_ios') != '17.4'
            or len(value.get('source_files', {})) != 25):
        raise ValueError('Unexpected StikJIT57 public dependency lock')
    return value


def validate_source(source, value):
    rows = {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
    if rows != value['source_files'] or any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('StikJIT source/archive contents differ from the reviewed pin')
    ffi = value['bundled_idevice_ffi']
    if (ffi['kind'] != 'upstream_prebuilt_static_library'
            or ffi['source_revision_disclosed_by_upstream'] is not False
            or (source / ffi['path']).stat().st_size != ffi['bytes']
            or sha(source / ffi['path']) != ffi['sha256']):
        raise ValueError('Upstream idevice binary input differs')
    return rows


def fetch_source(work, archive=None):
    value = lock_value()
    target = work / 'StikJIT.tar.gz'
    if archive:
        shutil.copyfile(archive, target)
    else:
        with urllib.request.urlopen(value['url'], timeout=90) as response, target.open('xb') as output:
            if response.geturl() != value['url']:
                raise ValueError('Unexpected StikJIT download redirect')
            total = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > value['archive_bytes']:
                    raise ValueError('StikJIT archive exceeds its pinned size')
                output.write(block)
    if target.stat().st_size != value['archive_bytes'] or sha(target) != ARCHIVE_SHA256:
        raise ValueError('StikJIT archive hash/size differs')
    prefix = 'StikJIT-' + COMMIT
    with tarfile.open(target) as archive_file:
        members = archive_file.getmembers()
        if len(members) > 100 or sum(m.size for m in members) > 64 * 1024 * 1024:
            raise ValueError('Unexpected StikJIT archive expansion')
        names = set()
        for member in members:
            path = Path(member.name)
            if (not path.parts or path.is_absolute() or path.parts[0] != prefix
                    or '..' in path.parts or member.issym() or member.islnk()
                    or not (member.isfile() or member.isdir()) or member.name in names):
                raise ValueError('Unsafe StikJIT archive entry')
            names.add(member.name)
        archive_file.extractall(work)
    source = work / prefix
    validate_source(source, value)
    return source, value


def safe_work(path):
    path = (ROOT / path).absolute()
    if ROOT / '.build' not in path.parents or path.resolve() != path or path.exists():
        raise ValueError('Use a fresh unaliased work directory under .build')
    return path


def macho_details(path):
    return macho_details_data(path.read_bytes(), path.name)


def macho_details_data(data, label='component'):
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xfeedfacf:
        raise ValueError('Expected a thin arm64 Mach-O: ' + label)
    _, cpu, _, kind, count, command_bytes, _, _ = struct.unpack_from('<8I', data)
    if cpu != 0x100000c or count > 200 or command_bytes > len(data) - 32:
        raise ValueError('Unexpected Mach-O architecture/load commands')
    offset = 32
    linked = []
    rpaths = []
    platforms = []
    install_name = None
    for _ in range(count):
        command, length = struct.unpack_from('<II', data, offset)
        if length < 8 or offset + length > 32 + command_bytes:
            raise ValueError('Invalid Mach-O load command')
        plain = command & 0x7fffffff
        if plain == 0x1d:
            raise ValueError('Unsigned development output contains a code signature')
        if plain in {0xc, 0xd, 0x18, 0x1f, 0x23}:
            start = struct.unpack_from('<I', data, offset + 8)[0]
            if start < 24 or start >= length:
                raise ValueError('Invalid dynamic-library load name')
            name = data[offset + start:offset + length].split(b'\0', 1)[0].decode('utf-8')
            if plain == 0xd:
                install_name = name
            else:
                linked.append(name)
        if plain == 0x32:
            platform, minimum, sdk = struct.unpack_from('<III', data, offset + 8)
            platforms.append(dict(platform=platform, minimum=minimum, sdk=sdk))
        if plain == 0x1c:
            start = struct.unpack_from('<I', data, offset + 8)[0]
            if start < 12 or start >= length:
                raise ValueError('Invalid Mach-O run path')
            rpaths.append(data[offset + start:offset + length].split(b'\0', 1)[0].decode('utf-8'))
        offset += length
    if offset != 32 + command_bytes:
        raise ValueError('Mach-O command size differs')
    return dict(kind=kind, linked=linked, platforms=platforms, install_name=install_name, rpaths=rpaths)


def validate_receipt(receipt_path):
    receipt_path = Path(receipt_path).absolute()
    if (ROOT / '.build' not in receipt_path.parents or receipt_path.resolve() != receipt_path
            or not receipt_path.is_file()):
        raise ValueError('Expected an unaliased local StikJIT build receipt')
    value = json.loads(receipt_path.read_text())
    lock = lock_value()
    if (value.get('status') != 'PASS_PINNED_STIKJIT_HELPER_BUILD'
            or value.get('source_commit') != COMMIT or value.get('archive_sha256') != ARCHIVE_SHA256
            or value.get('upstream_source_sha256') != lock['source_files']
            or value.get('bundled_idevice_ffi') != lock['bundled_idevice_ffi']
            or value.get('target') != TARGET or value.get('framework_linked_into_host') is not False
            or any(value.get(k) is not False for k in ['signing_performed', 'pairing_data_used', 'device_tested'])):
        raise ValueError('Missing or incompatible StikJIT helper provenance')
    work = receipt_path.parent
    for name, digest in value['source_sha256'].items():
        path = ROOT / name
        if path.resolve() != path or ROOT not in path.parents or sha(path) != digest:
            raise ValueError('StikJIT helper public source changed: ' + name)
    framework = work / 'StikJIT.framework'
    helper = work / 'CabrilloJITHelper.appex'
    if value.get('framework') != str(framework.relative_to(ROOT)) or value.get('helper') != str(helper.relative_to(ROOT)):
        raise ValueError('StikJIT helper artifact paths differ')
    rows = {str(p.relative_to(work)): sha(p) for folder in [framework, helper]
            for p in sorted(folder.rglob('*')) if p.is_file()}
    expected_files = {'StikJIT.framework/' + name for name in ['StikJIT', 'Info.plist', 'universal.js', 'legacy.js']}
    expected_files |= {'CabrilloJITHelper.appex/' + name for name in ['CabrilloJITHelper', 'Info.plist']}
    if set(rows) != expected_files:
        raise ValueError('Runtime components contain missing or unapproved files')
    if rows != value.get('files') or any(p.is_symlink() for folder in [framework, helper] for p in folder.rglob('*')):
        raise ValueError('StikJIT helper files changed')
    for folder, executable, kind in [(framework, 'StikJIT', 6), (helper, 'CabrilloJITHelper', 2)]:
        details = macho_details(folder / executable)
        if details['kind'] != kind or len(details['platforms']) != 1 or details['platforms'][0] != dict(platform=2, minimum=0x110400, sdk=0x1a0500):
            raise ValueError('StikJIT component platform/minimum OS differs')
        if folder == helper and '@rpath/StikJIT.framework/StikJIT' not in details['linked']:
            raise ValueError('Helper does not load its embedded StikJIT framework')
        if folder == helper and '@executable_path/../../Frameworks' not in details['rpaths']:
            raise ValueError('Helper cannot resolve its containing app framework')
        if folder == framework and details['install_name'] != '@rpath/StikJIT.framework/StikJIT':
            raise ValueError('StikJIT framework install name differs')
        settings = plistlib.loads((folder / 'Info.plist').read_bytes())
        if settings.get('MinimumOSVersion') != '17.4' or settings.get('CFBundleExecutable') != executable:
            raise ValueError('StikJIT component bundle metadata differs')
        if settings.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
            raise ValueError('StikJIT component installation platform differs')
    return value


def build(work, archive=None, framework_only=False):
    work = safe_work(work)
    work.mkdir(parents=True)
    source, value = fetch_source(work, archive)
    env = dict(os.environ, DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'),
               CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'), SWIFT_MODULECACHE_PATH=str(work / 'module-cache'))
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != XCODE:
        raise ValueError('StikJIT57 requires Xcode26.6 /17F113')
    if subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-version'], env=env, text=True).strip() != '26.5':
        raise ValueError('StikJIT57 requires iPhoneOS SDK26.5')
    sdk = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'], env=env, text=True).strip()
    env['SDKROOT'] = sdk
    framework = work / 'StikJIT.framework'
    framework.mkdir()
    modules = framework / 'Modules/StikJIT.swiftmodule'
    modules.mkdir(parents=True)
    commands = []

    def run(command, name):
        command = list(map(str, command))
        commands.append(command)
        with (work / (name + '.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        print('PASS ' + name, flush=True)

    flags = ['-swift-version', '5', '-O', '-g', '-target', TARGET, '-sdk', sdk,
             '-module-cache-path', work / 'module-cache']
    frameworks = ['JavaScriptCore', 'Network', 'Security', 'CFNetwork', 'SystemConfiguration', 'IOKit']
    # Both targets use this exact compiler. A binary module avoids Swift6.3's
    # textual-interface collision between module StikJIT and enum StikJIT;
    # this embedded implementation framework is not a distributed SDK.
    run(['xcrun', 'swiftc', *flags, '-module-name', 'StikJIT', '-enable-library-evolution',
         '-emit-library', '-emit-module', '-emit-module-path', modules / 'arm64-apple-ios.swiftmodule',
         '-I', source / 'idevice', '-I', source / 'iokit', '-L', source / 'idevice',
         '-Xlinker', '-hidden-lidevice_ffi', '-Xlinker', '-dead_strip',
         '-Xlinker', '-install_name', '-Xlinker', '@rpath/StikJIT.framework/StikJIT',
         '-Xlinker', '-no_adhoc_codesign',
         *(arg for name in frameworks for arg in ['-framework', name]),
         '-o', framework / 'StikJIT', *sorted((source / 'Sources').glob('*.swift'))], 'framework')
    for resource in sorted((source / 'Resources').iterdir()):
        shutil.copyfile(resource, framework / resource.name)
    settings = dict(CFBundleIdentifier='com.stik.StikJIT', CFBundleExecutable='StikJIT',
                    CFBundleName='StikJIT', CFBundlePackageType='FMWK',
                    CFBundleShortVersionString=value['framework_version'], CFBundleVersion=value['framework_build'],
                    MinimumOSVersion='17.4', CFBundleSupportedPlatforms=['iPhoneOS'])
    (framework / 'Info.plist').write_bytes(plistlib.dumps(settings, fmt=plistlib.FMT_BINARY))
    run(['xcrun', 'dsymutil', framework / 'StikJIT', '-o', work / 'StikJIT.framework.dSYM'], 'framework-symbols')
    # swiftc -g may independently emit a sibling dSYM beside its output. Keep
    # symbols in work only; they are never part of either runtime bundle.
    shutil.rmtree(framework / 'StikJIT.dSYM', ignore_errors=True)
    run(['xcrun', 'strip', '-S', framework / 'StikJIT'], 'framework-strip')
    source_hashes = {str(LOCK.relative_to(ROOT)): sha(LOCK), str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))}
    receipt = dict(schema=1, status='PASS_PINNED_STIKJIT_FRAMEWORK', target=TARGET,
                   source_commit=COMMIT, archive_sha256=ARCHIVE_SHA256,
                   upstream_source_sha256=value['source_files'], bundled_idevice_ffi=value['bundled_idevice_ffi'],
                   framework=str(framework.relative_to(ROOT)), helper=None, commands=commands,
                   source_sha256=source_hashes, signing_performed=False, pairing_data_used=False,
                   device_tested=False, framework_linked_into_host=False)
    if not framework_only:
        helper_source = LANE / 'helper'
        helper = work / 'CabrilloJITHelper.appex'
        helper.mkdir()
        helper_files = sorted(helper_source.glob('*.swift'))
        if not helper_files:
            raise ValueError('Cabrillo helper sources are missing')
        for path in [*helper_files, helper_source / 'main.m', helper_source / 'Info.plist']:
            source_hashes[str(path.relative_to(ROOT))] = sha(path)
        run(['xcrun', 'clang', '-target', TARGET, '-isysroot', sdk, '-O2', '-g',
             '-fobjc-arc', '-fapplication-extension', '-Wall', '-Wextra', '-Werror',
             '-c', helper_source / 'main.m', '-o', work / 'helper-main.o'], 'helper-entry')
        run(['xcrun', 'swiftc', *flags, '-module-name', 'CabrilloJITHelper', '-parse-as-library',
             '-application-extension', '-F', work, '-framework', 'StikJIT',
             '-framework', 'Foundation', work / 'helper-main.o',
             '-Xlinker', '-rpath', '-Xlinker', '@executable_path/../../Frameworks',
             '-Xlinker', '-no_adhoc_codesign', '-o', helper / 'CabrilloJITHelper', *helper_files], 'helper')
        helper_settings = plistlib.loads((helper_source / 'Info.plist').read_bytes())
        if (helper_settings.get('MinimumOSVersion') != '17.4'
                or helper_settings.get('NSExtension', {}).get('NSExtensionPointIdentifier') != 'com.apple.ar.viewer'):
            raise ValueError('Unexpected helper extension identity/availability')
        helper_settings.update(CFBundleSupportedPlatforms=['iPhoneOS'], UIDeviceFamily=[1, 2], LSRequiresIPhoneOS=True)
        (helper / 'Info.plist').write_bytes(plistlib.dumps(helper_settings, fmt=plistlib.FMT_BINARY))
        run(['xcrun', 'dsymutil', helper / 'CabrilloJITHelper', '-o', work / 'CabrilloJITHelper.appex.dSYM'], 'helper-symbols')
        shutil.rmtree(helper / 'CabrilloJITHelper.dSYM', ignore_errors=True)
        run(['xcrun', 'strip', '-S', helper / 'CabrilloJITHelper'], 'helper-strip')
        shutil.rmtree(framework / 'Modules')
        receipt.update(status='PASS_PINNED_STIKJIT_HELPER_BUILD', helper=str(helper.relative_to(ROOT)))
    receipt['files'] = {str(p.relative_to(work)): sha(p) for folder in [framework] + ([helper] if not framework_only else [])
                        for p in sorted(folder.rglob('*')) if p.is_file()}
    write_json(work / 'receipt.json', receipt)
    if not framework_only:
        validate_receipt(work / 'receipt.json')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    parser.add_argument('--archive', type=Path, help='Optional locally cached archive; its exact pinned hash is required')
    parser.add_argument('--framework-only', action='store_true', help='Compile only the framework for isolated development checks')
    args = parser.parse_args()
    result = build(args.work, args.archive, args.framework_only)
    print(result['status'], flush=True)
