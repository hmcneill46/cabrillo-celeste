#!/usr/bin/env python3
"""Recompile explicit, hash-locked native inputs for iOS15; never read a legacy checkout."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = '/Applications/Xcode-26.6.app/Contents/Developer'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--work', required=True)
    args = parser.parse_args()
    inputs = (ROOT / args.inputs).resolve()
    work = (ROOT / args.work).resolve()
    assert ROOT / '.private' in inputs.parents and ROOT / '.build' in work.parents and not work.exists()
    manifest = inputs / 'manifest.json'
    assert sha(manifest) == args.manifest_sha256
    data = json.loads(manifest.read_text())
    for name, row in data['files'].items():
        assert sha(inputs / name) == row['sha256'], name
    work.mkdir(parents=True)
    for part in ['work', 'stage', 'logs']:
        (work / part).mkdir()
    checked_sources = [Path(__file__), ROOT / 'experiments/ios-jit/managed-canary/src/cjit-mono-bridge.h',
                       ROOT / 'experiments/ios-jit/launcher-platforms/src/cjit-bfi-policy.h',
                       ROOT / 'scripts/finalize-apple-archive.py']
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in checked_sources}
    (work / 'source-state.json').write_text(json.dumps(dict(input_manifest_sha256=sha(manifest),
                                                          public_source_sha256=source_hashes), indent=2) + '\n')
    env = dict(os.environ, DEVELOPER_DIR=DEVELOPER, CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'))
    commands = []
    def run(cmd, label):
        cmd = list(map(str, cmd)); commands.append(cmd)
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(cmd, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(label + ' failed: ' + str(work / (label + '.log')))
        print('PASS ' + label, flush=True)
    assert subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() == 'Xcode 26.6\nBuild version 17F113'
    sdk = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--show-sdk-path'], env=env, text=True).strip()
    compiler = subprocess.check_output(['xcrun', '--sdk', 'iphoneos', '--find', 'clang'], env=env, text=True).strip()
    runtime = work / 'runtime'
    run(['cp', '-cR', inputs / 'runtime', runtime], 'copy-runtime')
    build = work / 'mono'; build.mkdir()
    (build / 'version.h').write_text('#define VER_PRODUCTVERSION_STR "8.0.28.0"\n')
    (build / 'version.c').write_text('static char sccsid[] __attribute__((used)) = "@(#)Version 8.0.28.0 @Commit: ' + data['runtime_commit'] + '";\n')
    (build / 'runtime_version.h').write_text('#define RuntimeProductMajorVersion 8\n#define RuntimeProductMinorVersion 0\n#define RuntimeProductPatchVersion 28\n')
    generated = runtime / 'artifacts/obj'; generated.mkdir(parents=True, exist_ok=True)
    for name, dest in [('version.h', '_version.h'), ('version.c', '_version.c'), ('runtime_version.h', 'runtime_version.h')]:
        shutil.copyfile(build / name, generated / dest)
    bridge = ROOT / 'experiments/ios-jit/managed-canary/src'
    policy = ROOT / 'experiments/ios-jit/launcher-platforms/src'
    flags = '-DCJ_MONO_IOS_JIT=1 -I' + str(bridge) + ' -I' + str(policy)
    run(['cmake', '-S', runtime / 'src/mono', '-B', build, '-G', 'Unix Makefiles',
         '-DCMAKE_SYSTEM_NAME=iOS', '-DCMAKE_SYSTEM_PROCESSOR=arm64', '-DCMAKE_OSX_ARCHITECTURES=arm64',
         '-DCMAKE_OSX_SYSROOT=' + sdk, '-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0',
         '-DCMAKE_C_COMPILER=' + compiler, '-DCMAKE_CXX_COMPILER=' + compiler + '++',
         '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX=' + str(build / 'out'), '-DCMAKE_INSTALL_LIBDIR=lib',
         '-DCLR_CMAKE_HOST_ARCH=arm64', '-DCLR_CMAKE_TARGET_ARCH=arm64', '-DCLR_CMAKE_TARGET_OS=ios',
         '-DDISABLE_JIT=OFF', '-DDISABLE_INTERPRETER=ON', '-DDISABLE_AOT=ON', '-DDISABLE_EXECUTABLES=ON',
         '-DDISABLE_SHARED_LIBS=ON', '-DDISABLE_EVENTPIPE=ON', '-DENABLE_PERFTRACING=OFF',
         '-DDISABLE_DEBUGGER_AGENT=ON', '-DSTATIC_COMPONENTS=ON', '-DDISABLE_LLDB=ON', '-DGC_SUSPEND=coop',
         '-DENABLE_WERROR=OFF', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON', '-DCLR_CMAKE_KEEP_NATIVE_SYMBOLS=ON',
         '-DVERSION_HEADER_PATH=' + str(build / 'version.h'), '-DVERSION_FILE_PATH=' + str(build / 'version.c'),
         '-DRUNTIME_VERSION_HEADER_PATH=' + str(build / 'runtime_version.h'),
         '-DCMAKE_C_FLAGS=' + flags, '-DCMAKE_CXX_FLAGS=' + flags], 'mono-configure')
    run(['cmake', '--build', build, '--target', 'monosgen-static', 'mono-component-marshal-ilgen-static',
         'mono-component-debugger-stub-static', 'mono-component-hot_reload-stub-static',
         'mono-component-diagnostics_tracing-stub-static', '--parallel', '6'], 'mono-build')
    renderer = work / 'renderer'
    run(['cp', '-cR', inputs / 'renderer', renderer], 'copy-renderer')
    run(['xcodebuild', 'build', '-project', renderer / 'FNA3D/Xcode-iOS/FNA3D.xcodeproj', '-target', 'FNA3D',
         '-configuration', 'Release', '-sdk', 'iphoneos', 'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=NO',
         'IPHONEOS_DEPLOYMENT_TARGET=15.0', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO',
         'GCC_GENERATE_DEBUGGING_SYMBOLS=YES', 'DEBUG_INFORMATION_FORMAT=dwarf',
         'OBJROOT=' + str(work / 'renderer-obj'), 'SYMROOT=' + str(work / 'renderer-sym'),
         'CONFIGURATION_BUILD_DIR=' + str(work / 'work/renderer-products')], 'renderer-build')
    libraries = work / 'stage/libraries'; libraries.mkdir()
    run(['python3', ROOT / 'scripts/finalize-apple-archive.py', '--build-root', work,
         '--input', work / 'work/renderer-products/libFNA3D.a', '--output', libraries / 'libFNA3D.a',
         '--report', work / 'logs/renderer-archive.json'], 'renderer-archive')
    lua = work / 'lua'; lua.mkdir()
    objects = []
    for source in sorted((inputs / 'lua').glob('*.c')):
        if source.name in {'lua.c', 'luac.c'}: continue
        obj = lua / (source.stem + '.o'); objects.append(obj)
        run(['xcrun', '--sdk', 'iphoneos', 'clang', '-target', 'arm64-apple-ios15.0', '-isysroot', sdk,
             '-O2', '-g', '-fPIC', '-DCJIT_IOS=1', '-c', source, '-o', obj], 'lua-' + source.stem)
    run(['xcrun', 'libtool', '-static', '-o', libraries / 'liblua54.a', *objects], 'lua-archive')
    for name in ['libmonosgen-2.0.a', 'libmono-component-marshal-ilgen-static.a',
                 'libmono-component-debugger-stub-static.a', 'libmono-component-hot_reload-stub-static.a',
                 'libmono-component-diagnostics_tracing-stub-static.a']:
        matches = list(build.rglob(name)); assert len(matches) == 1, matches
        shutil.copyfile(matches[0], libraries / name)
    assert source_hashes == {str(p.relative_to(ROOT)): sha(p) for p in checked_sources}, 'Public input changed during compilation'
    assert sha(manifest) == args.manifest_sha256, 'Private manifest changed during compilation'
    receipt = dict(schema=1, status='PASS_NATIVE_IOS15_REBUILD', created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   deployment_target='15.0', input_manifest=str(manifest.relative_to(ROOT)), input_manifest_sha256=sha(manifest),
                   source_sha256=source_hashes,
                   libraries={p.name: dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in libraries.glob('*.a')},
                   commands=commands, runtime_commit=data['runtime_commit'], legacy_read_during_build=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__': main()
