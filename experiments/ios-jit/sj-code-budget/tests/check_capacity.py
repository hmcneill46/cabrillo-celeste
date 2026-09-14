#!/usr/bin/env python3
"""Replay the physical failure and actual new host chunk sizes with 16 KiB aliases."""
import hashlib,json,os,re,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2];BASE=SOURCE.parent/'managed-canary'
STAGE=ROOT/'.build/ios-jit/sj-budget-capacity-tests';STAGE.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
physical=ROOT/'.build/ios-jit/device-evidence/2026-09-12/build-15-crash'
validation=json.loads((physical/'validation.json').read_text());trace=physical/'build15-allocation-sizes.txt'
assert sha(trace)==validation['allocation_trace_sha256']
host=ROOT/'.build/ios-jit/sj-budget-host-test';host_receipt=json.loads((host/'receipt.json').read_text())
assert sha(host/'run.log')==host_receipt['log_sha256']
assert host_receipt['code_manager_model']==dict(page_bytes=16384,granule_bytes=16384,bind_room_divisor=4,minimum_chunk_bytes=65536)
log=(host/'run.log').read_text();sizes=list(map(int,re.findall(r'^HOST_CODE_CHUNK_BYTES (\d+)$',log,re.M)))
assert len(sizes)>800 and sizes.count(65536)>500
# Every created chunk is budgeted even if Mono recycled the same address.
# Conservatively add all possible 256 native hook allocations at the maximum
# allowed 64 KiB each. This covers non-profiler code reservations as well.
# Two full host traces plus this reserve must fit in the same 128 MiB arena.
host_chunks=len(sizes); host_rounded=sum((n+16383)&~16383 for n in sizes)
sizes = sizes*2 + [65536]*256
host_trace=STAGE/'host-device-sizing-with-native-reserve.txt';host_trace.write_text(''.join(str(x)+'\n' for x in sizes))
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',UBSAN_OPTIONS='halt_on_error=1',ASAN_OPTIONS='halt_on_error=1')
results={}
for old,requests in [(True,trace),(False,host_trace)]:
 name='physical-build15-control' if old else 'build16-host-trace-with-reserve'
 command=['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(BASE/'src'),'-I'+str(SOURCE/'src')]
 if old:command+=['-DCJ_TEST_PHYSICAL_FAILURE=1']
 command += [str(SOURCE/'tests/arena_capacity_test.c'),str(BASE/'src/CJCodeArena.c' if old else SOURCE/'src/CJHookCodeArena.c'),'-o',str(STAGE/name)]
 subprocess.run(command,env=env,check=True)
 run=subprocess.run([STAGE/name,requests],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (STAGE/(name+'.log')).write_text(run.stdout)
 assert run.returncode==0 and 'runtime error:' not in run.stdout and 'ERROR: AddressSanitizer' not in run.stdout,run.stdout
 assert ('PASS_REPRODUCED_BUILD15_EXACT_EXHAUSTION' if old else 'PASS_EXHAUSTION_STOPS_BEFORE_MONO_USES_NULL') in run.stdout
 results[name]=dict(command=command,output=run.stdout);print(run.stdout.strip())
inputs=[Path(__file__),SOURCE/'tests/arena_capacity_test.c',SOURCE/'src/CJHookCodeArena.c',SOURCE/'src/CJHookMemory.h',BASE/'src/CJCodeArena.c',BASE/'src/CJCodeArena.h',BASE/'src/cjit-mono-bridge.h',trace,host/'receipt.json',host/'run.log']
result=dict(status='PASS_BUILD15_EXACT_FAILURE_AND_BUILD16_DEVICE_SIZED_ALIAS_REPLAY',runs=results,page_bytes=16384,budget_bytes=134217728,host_chunks=host_chunks,host_chunk_rounded_bytes=host_rounded,extra_native_reserve_bytes=256*65536,repetitions=2,code_regions_reused_or_reclaimed=False,physical_failure_exactly_reproduced=True,input_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},scope='Actual alias allocator with read-only/RW shared mappings, ASan/UBSan; actual full helper host chunk sizes under 16 KiB/ARM64 binding-room sizing plus conservative native reserve. ARM64 execution and larger future mod graphs remain phone gates.')
(STAGE/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
