#!/usr/bin/env python3
"""Run the actual device patch bridge against protected alias mappings under sanitizers."""
from pathlib import Path
import hashlib,json,os,subprocess
source=Path(__file__).resolve().parents[1];root=source.parents[2];g1=source.parent/'managed-canary'
stage=root/'.build/ios-jit/hook-runtime/alias-tests';stage.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',UBSAN_OPTIONS='halt_on_error=1',ASAN_OPTIONS='halt_on_error=1')
files=[source/'tests/alias_patch_test.c',source/'src/CJHookNative.c',g1/'src/CJCodeArena.c',source.parent/'native-probe/src/VMRange.c',source.parent/'native-probe/src/VMRangeDarwin.c']
args=['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-DCJ_HOOK_HOST_TEST=0']
args+=['-I'+str(p) for p in [source/'src',g1/'src',source.parent/'native-probe/src',root/'.build/ios-jit/managed-runtime/pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0']]
args+=list(map(str,files))+['-o',str(stage/'alias-patch-test')]
subprocess.run(args,env=env,check=True)
r=subprocess.run([stage/'alias-patch-test'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(stage/'run.log').write_text(r.stdout);print(r.stdout)
assert r.returncode==0 and 'runtime error:' not in r.stdout and 'ERROR: AddressSanitizer' not in r.stdout
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'status':'PASS_ACTUAL_DEVICE_PATCH_BRANCH_WITH_HOST_RX_RW_ALIASES','sanitizers':['address','undefined'],
 'summary':r.stdout.strip(),'device_execution':False,'mono_metadata_queries':'mocked; real Mono behavior checked separately',
 'source_sha256':{str(p.relative_to(root)):sha(p) for p in files},'log_sha256':sha(stage/'run.log'),'command':args}
(stage/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
