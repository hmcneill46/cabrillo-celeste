#!/usr/bin/env python3
"""Reproduce build 4's two RX table-write bugs; validate the actual patched cases."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

source = Path(__file__).resolve().parents[1]
root = source.parents[2]
runtime = root / '.build/ios-jit/managed-runtime/runtime-v8.0.28'
stage = root / '.build/ios-jit/managed-canary/host-tests'
stage.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',
           UBSAN_OPTIONS='halt_on_error=1', ASAN_OPTIONS='halt_on_error=1')
template = (source / 'tests/switch_table_harness.c').read_text()
files = {'POSTPROCESS': 'src/mono/mono/mini/mini.c', 'RESOLVE': 'src/mono/mono/mini/mini-runtime.c'}


def extract_case(text):
    marker = 'case MONO_PATCH_INFO_SWITCH: {'
    assert text.count(marker) == 1
    start = text.index(marker)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


receipt = {'device_execution': False, 'sanitizers': ['address', 'undefined'], 'cases': {}, 'negative_controls': {}}
for variant in ('upstream', 'patched'):
    program = template
    for key, name in files.items():
        content = (runtime / name).read_text() if variant == 'patched' else subprocess.check_output(
            ['git', '-C', str(runtime), 'show', 'HEAD:' + name], text=True)
        case = extract_case(content)
        receipt['cases'][variant + '_' + key.lower()] = hashlib.sha256(case.encode()).hexdigest()
        program = program.replace('/* ' + key + '_CASE */', case)
    c_file = stage / ('switch-tables-' + variant + '.c')
    c_file.write_text(program)
    binary = c_file.with_suffix('')
    command = ['xcrun', 'clang', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-DCJ_MONO_IOS_JIT=1',
               '-I' + str(source / 'src'), str(c_file), str(source / 'src/CJCodeArena.c'), '-o', str(binary)]
    if variant == 'patched': command += ['-fsanitize=address,undefined']
    subprocess.run(command, env=env, check=True)
    if variant == 'upstream':
        for mode in ('postprocess-static', 'postprocess-dynamic', 'resolve-static', 'resolve-dynamic'):
            result = subprocess.run([binary, mode], env=env, capture_output=True, text=True)
            assert result.returncode in (-signal.SIGSEGV, -signal.SIGBUS), (mode, result.returncode, result.stderr)
            receipt['negative_controls'][mode] = signal.Signals(-result.returncode).name
    else:
        result = subprocess.run([binary], env=env, capture_output=True, text=True)
        (stage / 'switch-tables.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout, end='')
receipt['result'] = 'PASS_ACTUAL_MONO_SWITCH_TABLE_REGRESSION'
(stage / 'switch-tables.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('PASS: all four unpatched RX-write negative controls faulted as expected.')
