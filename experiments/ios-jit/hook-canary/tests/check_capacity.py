#!/usr/bin/env python3
"""Replay the physical build-8 reservation sizes through actual alias allocators."""
from pathlib import Path
import hashlib, json, os, subprocess

source = Path(__file__).resolve().parents[1]; root = source.parents[2]
base = source.parent / 'managed-canary'
stage = root / '.build/ios-jit/hook-runtime/capacity-test'; stage.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',
           UBSAN_OPTIONS='halt_on_error=1', ASAN_OPTIONS='halt_on_error=1')
trace = source / 'tests/build8-allocation-sizes.txt'
original = json.loads((root / 'artifacts/ios-jit/hook-canary-20260911-08/build-receipt.json').read_text())
allocator = base / 'src/CJCodeArena.c'
assert hashlib.sha256(allocator.read_bytes()).hexdigest() == original['source_sha256'][str(allocator.relative_to(root))]
inputs = [source / 'tests/arena_capacity_test.c', source / 'src/CJHookCodeArena.c',
          source / 'src/CJHookMemory.h', base / 'src/CJCodeArena.c', base / 'src/CJCodeArena.h',
          base / 'src/cjit-mono-bridge.h', Path(__file__), trace]
results = {}
for old in [True, False]:
    name = 'old-budget' if old else 'new-budget'
    command = ['xcrun', 'clang', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
               '-fsanitize=address,undefined', '-I' + str(base / 'src'), '-I' + str(source / 'src')]
    if old: command += ['-DCJ_TEST_OLD_ALLOCATOR=1']
    command += [str(source / 'tests/arena_capacity_test.c'),
                str(base / 'src/CJCodeArena.c' if old else source / 'src/CJHookCodeArena.c'), '-o', str(stage / name)]
    subprocess.run(command, env=env, check=True)
    run = subprocess.run([stage / name, trace], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stage / (name + '.log')).write_text(run.stdout)
    assert run.returncode == 0 and 'runtime error:' not in run.stdout and 'ERROR: AddressSanitizer' not in run.stdout, run.stdout
    if old: assert 'PASS_REPRODUCED_BUILD8_EXHAUSTION' in run.stdout
    else:
        assert 'PASS_REPLAYED_THREE_TRACES allocations=198' in run.stdout
        assert 'EVENT jit_code_budget_exhausted' in run.stdout
        assert 'PASS_EXHAUSTION_STOPS_BEFORE_MONO_USES_NULL' in run.stdout
    results[name] = {'command': command, 'output': run.stdout}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
result = {'status': 'PASS_BUILD8_ALLOCATION_REPLAY_AND_TERMINAL_BUDGET_GUARD',
          'physical_export_sha256': '52414eae61af815d85ece23fa6f0e57a572d314c08c7a6ee3b91d09de6ad4f7f',
          'physical_successful_reservations': 65, 'physical_failed_request': 262144,
          'old_bytes_per_arena': 4194304, 'new_bytes_per_arena': 16777216,
          'base_allocator_matches_crashed_build': True,
          'emulated_device_page_bytes': 16384, 'sanitizers': ['address', 'undefined'],
          'source_sha256': {str(p.relative_to(root)): sha(p) for p in inputs}, 'runs': results,
          'scope': 'actual C allocators, host read-only/writable aliases, physical allocation trace replay; no ARM64 execution or full device fixture'}
(stage / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v['output'] for k, v in results.items()}, indent=2))
