#!/usr/bin/env python3
"""Build the pinned Mono on this Intel Mac for real cooperative-GC embedding regressions."""
import hashlib
import base64
import json
import os
from pathlib import Path
import platform
import subprocess
import urllib.request
import zipfile

source = Path(__file__).resolve().parents[1]
root = source.parents[2]
base = root / '.build/ios-jit/managed-runtime'
runtime = base / 'runtime-v8.0.28'
build = base / 'mono-build-host-coop'
assert platform.machine() == 'x86_64', 'This regression host is deliberately macOS x64.'
pin = json.loads((source / 'runtime-pin.json').read_text())
host_pin = json.loads((source / 'tests/host-runtime-pin.json').read_text())
package = base / 'downloads' / host_pin['url'].rsplit('/', 1)[1]
if not package.exists():
    package.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(host_pin['url'], timeout=30) as response:
        package.write_bytes(response.read())
assert base64.b64encode(hashlib.sha512(package.read_bytes()).digest()).decode() == host_pin['sha512_base64']
host_pack = base / 'pack-osx-8.0.28'
with zipfile.ZipFile(package) as archive:
    assert all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in archive.namelist())
    archive.extractall(host_pack)
assert host_pin['repository_commit'] == pin['runtime_commit']
assert subprocess.check_output(['git', '-C', str(runtime), 'rev-parse', 'HEAD'], text=True).strip() == pin['runtime_commit']
patch = json.loads((base / 'runtime-patch-receipt.json').read_text())
for name, hashes in patch['files'].items():
    assert hashlib.sha256((runtime / name).read_bytes()).hexdigest() == hashes['patched_sha256']
build.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=env, text=True).strip()
compiler = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--find', 'clang'], env=env, text=True).strip()
# The alias macro falls back to ordinary writes without CJ_MONO_IOS_JIT. This
# tests the same Mono lifecycle implementation, not iOS ARM64 JIT memory.
flags = '-I' + str(source / 'src')
args = ['cmake', '-S', str(runtime / 'src/mono'), '-B', str(build), '-G', 'Unix Makefiles',
        '-DCMAKE_SYSTEM_NAME=Darwin', '-DCMAKE_SYSTEM_PROCESSOR=x86_64', '-DCMAKE_OSX_ARCHITECTURES=x86_64',
        '-DCMAKE_OSX_SYSROOT=' + sdk, '-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0',
        '-DCMAKE_C_COMPILER=' + compiler, '-DCMAKE_CXX_COMPILER=' + compiler + '++',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX=' + str(build / 'out'), '-DCMAKE_INSTALL_LIBDIR=lib',
        '-DCLR_CMAKE_HOST_ARCH=x64', '-DCLR_CMAKE_TARGET_ARCH=x64', '-DCLR_CMAKE_TARGET_OS=darwin',
        '-DDISABLE_JIT=OFF', '-DDISABLE_INTERPRETER=ON', '-DDISABLE_AOT=ON', '-DDISABLE_EXECUTABLES=ON', '-DDISABLE_SHARED_LIBS=ON',
        '-DDISABLE_EVENTPIPE=ON', '-DENABLE_PERFTRACING=OFF', '-DDISABLE_DEBUGGER_AGENT=ON', '-DSTATIC_COMPONENTS=ON',
        '-DDISABLE_LLDB=ON', '-DGC_SUSPEND=coop', '-DENABLE_WERROR=OFF', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
        '-DVERSION_HEADER_PATH=' + str(base / 'mono-build-ios/version.h'),
        '-DVERSION_FILE_PATH=' + str(base / 'mono-build-ios/version.c'),
        '-DRUNTIME_VERSION_HEADER_PATH=' + str(base / 'mono-build-ios/runtime_version.h'),
        '-DCMAKE_C_FLAGS=' + flags, '-DCMAKE_CXX_FLAGS=' + flags, '-DCLR_CMAKE_KEEP_NATIVE_SYMBOLS=ON']
commands = [args, ['cmake', '--build', str(build), '--target', 'monosgen-static', 'mono-component-marshal-ilgen-static',
    'mono-component-debugger-stub-static', 'mono-component-hot_reload-stub-static', 'mono-component-diagnostics_tracing-stub-static', '--parallel', '4']]
(build / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
for label, command in zip(('configure', 'build'), commands):
    with (build / (label + '.log')).open('w') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print((build / (label + '.log')).read_text()[-6000:])
        raise SystemExit(result.returncode)
    print('HOST_MONO_' + label.upper() + '_PASS', flush=True)
