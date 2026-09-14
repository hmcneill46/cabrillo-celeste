#!/usr/bin/env python3
"""Reproduce the actual Mono detach abort, then test the shared correction and thread reuse."""
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess

source = Path(__file__).resolve().parents[1]
root = source.parents[2]
base = root / '.build/ios-jit/managed-runtime'
build = base / 'mono-build-host-coop'
stage = root / '.build/ios-jit/managed-canary/host-tests/lifecycle'
stage.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
native = base / 'pack-ios-8.0.28/runtimes/ios-arm64/native'
# Use framework IL from the matching macOS Mono pack for this host architecture,
# and the exact physically tested canary DLL. Nothing here replaces iOS inputs.
framework = stage / 'Managed'
framework.mkdir(exist_ok=True)
pack = base / 'pack-osx-8.0.28/runtimes/osx-x64'
for file in list((pack / 'lib/net8.0').glob('*.dll')) + [pack / 'native/System.Private.CoreLib.dll']:
    shutil.copy2(file, framework / file.name)
fixture = root / 'artifacts/ios-jit/managed-canary-20260911-05/Canary-v0.2.1.dll'
env['CJIT_TEST_TPA'] = ':'.join(str(p) for p in sorted(framework.glob('*.dll')))
system_native = pack / 'native/libSystem.Native.dylib'
libraries = [build / 'mono/mini/libmonosgen-2.0.a']
libraries += [build / ('mono/mini/libmono-component-' + name + '-static.a') for name in
              ('marshal-ilgen', 'debugger-stub', 'hot_reload-stub', 'diagnostics_tracing-stub')]
config = (build / 'config.h').read_text()
assert '#define ENABLE_COOP_SUSPEND 1' in config
assert '#define DISABLE_INTERPRETER 1' in config and '#define DISABLE_AOT 1' in config
binary = stage / 'mono-lifecycle-test'
command = ['xcrun', 'clang', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
    '-I' + str(source / 'src'), '-I' + str(native / 'include/mono-2.0'),
    str(source / 'tests/mono_lifecycle_test.c'), str(source / 'src/CJMonoThread.c'),
    str(source / 'src/CJNativeResolver.c'), str(source / 'src/CanaryNative.c'), *map(str, libraries),
    '-lc++', '-liconv', '-lz', '-framework', 'CoreFoundation', '-framework', 'Foundation', '-framework', 'Security', '-o', str(binary)]
subprocess.run(command, env=env, check=True)
results = {}
for mode in ('old', 'fixed'):
    result = subprocess.run([binary, system_native, framework, fixture, mode], env=env, cwd=stage,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)
    (stage / (mode + '.log')).write_text(result.stdout)
    if mode == 'old':
        assert result.returncode == -signal.SIGABRT, (result.returncode, result.stdout[-5000:])
        assert 'HOST_MONO_EIGHT_STAGES_PASS' in result.stdout
        assert 'from STATE_BLOCKING with DO_BLOCKING' in result.stdout, result.stdout[-5000:]
        print('PASS: old detach reproduces the exact STATE_BLOCKING / DO_BLOCKING abort after all eight managed stages.')
    else:
        assert result.returncode == 0, (result.returncode, result.stdout[-6000:])
        assert '160 attach/invoke/detach cycles' in result.stdout
        print(result.stdout[-1300:], end='')
    results[mode] = {'returncode': result.returncode, 'log_sha256': hashlib.sha256(result.stdout.encode()).hexdigest()}
receipt = {'status': 'PASS_ACTUAL_PINNED_MONO_COOP_LIFECYCLE_REGRESSION', 'runtime': 'Mono 8.0.28 macOS x64',
           'runtime_commit': json.loads((source / 'runtime-pin.json').read_text())['runtime_commit'],
           'gc_suspend': 'coop', 'negative_control': 'Build 5 detach aborts after all eight stages with the exact physical diagnostic',
           'fixed_bootstrap_detach': True, 'reattach_invoke_detach_cycles': 160, 'native_threads': 5,
           'entry_states_tested': ['GC safe', 'GC unsafe'], 'results': results,
           'shared_detach_source_sha256': hashlib.sha256((source / 'src/CJMonoThread.c').read_bytes()).hexdigest(),
           'host_framework_pin': json.loads((source / 'tests/host-runtime-pin.json').read_text()),
           'device_execution': False, 'aot_and_interpreter_disabled': True, 'command': command}
(stage / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
