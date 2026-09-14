#!/usr/bin/env python3
"""Check the actual resolver against the matching host System.Native exports."""
import json
import os
from pathlib import Path
import subprocess

source = Path(__file__).resolve().parents[1]
root = source.parents[2]
stage = root / '.build/ios-jit/managed-canary/host-tests'
stage.mkdir(parents=True, exist_ok=True)
library = root / '.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422/shared/Microsoft.NETCore.App/8.0.28/libSystem.Native.dylib'
binary = stage / 'native-resolver-test'
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',
           UBSAN_OPTIONS='halt_on_error=1', ASAN_OPTIONS='halt_on_error=1')
command = ['xcrun', 'clang', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
           '-I' + str(source / 'src'), str(source / 'tests/native_resolver_test.c'),
           str(source / 'src/CJNativeResolver.c'), str(source / 'src/CanaryNative.c'), '-o', str(binary)]
subprocess.run(command, env=env, check=True)
result = subprocess.run([binary, library], env=env, text=True, capture_output=True)
(stage / 'native-resolver.log').write_text(result.stdout + result.stderr)
assert result.returncode == 0, result.stdout + result.stderr
print(result.stdout, end='')
(stage / 'native-resolver.json').write_text(json.dumps({'result': 'PASS_NATIVE_LIBRARY_RESOLVER_HOST',
    'host_native_library': str(library.relative_to(root)), 'device_execution': False,
    'checks': ['three observed imports under three library aliases', 'native GetEnv round trip', 'fixture callback', 'unknown/null rejection'],
    'sanitizers': ['address', 'undefined'], 'command': command}, indent=2) + '\n')
