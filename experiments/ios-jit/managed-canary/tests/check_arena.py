#!/usr/bin/env python3
"""Exercise actual Mono ARM64 emission through read-only host aliases under ASan/UBSan."""
from pathlib import Path
import json,os,subprocess
source=Path(__file__).resolve().parents[1];root=source.parents[2]
base=root/'.build/ios-jit/managed-runtime';runtime=base/'runtime-v8.0.28'
stage=root/'.build/ios-jit/managed-canary/host-tests';stage.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',UBSAN_OPTIONS='halt_on_error=1',ASAN_OPTIONS='halt_on_error=1')
includes=[source/'src',runtime/'src/mono',runtime/'src/mono/mono/eglib',base/'mono-build-ios/mono/eglib',runtime/'src/native']
args=['xcrun','clang','-std=c11','-O1','-g','-fsanitize=address,undefined','-DCJ_MONO_IOS_JIT=1']
args += ['-I'+str(p) for p in includes]+[str(source/'tests/arena_test.c'),str(source/'src/CJCodeArena.c'),'-o',str(stage/'arena-test')]
subprocess.run(args,env=env,check=True)
result=subprocess.run([stage/'arena-test'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(stage/'arena-test.log').write_text(result.stdout);print(result.stdout)
assert result.returncode==0 and 'runtime error:' not in result.stdout and 'ERROR: AddressSanitizer' not in result.stdout
receipt={'result':'PASS_HOST_ALIAS_ALLOCATOR_AND_ACTUAL_ARM64_EMITTER','sanitizers':['address','undefined'],
         'checks':['read-only RX emission','branch uses RX PC','instruction patch','ordinary heap emission','allocation bounds','exhaustion','concurrent allocation','invalid code write aborts'],
         'device_execution':False,'command':args}
(stage/'arena-test.json').write_text(json.dumps(receipt,indent=2)+'\n')
