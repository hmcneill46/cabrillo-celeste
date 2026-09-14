#!/usr/bin/env python3
"""Execute real Hook/ILHook and a second native worker on pinned macOS Mono."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess

source=Path(__file__).resolve().parents[1];root=source.parents[2];g1=source.parent/'managed-canary'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path);a=p.parse_args()
base=root/'.build/ios-jit/hook-runtime';stage=base/'host-test';stage.mkdir(exist_ok=True)
runtime=root/'.build/ios-jit/managed-runtime';pack=runtime/'pack-osx-8.0.28/runtimes/osx-x64';mono=runtime/'mono-build-host-coop'
fixture=a.fixture or base/'development-fixture/HookCanary-v0.3.0.dll';assert fixture.exists()
framework=stage/'Managed';framework.mkdir(exist_ok=True)
for file in [*list((pack/'lib/net8.0').glob('*.dll')),pack/'native/System.Private.CoreLib.dll',*list((base/'managed-libraries').glob('*.dll'))]:shutil.copy2(file,framework/file.name)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CJIT_TEST_TPA=':'.join(map(str,sorted(framework.glob('*.dll')))))
libs=[mono/'mono/mini/libmonosgen-2.0.a']+[mono/('mono/mini/libmono-component-'+n+'.a') for n in ['marshal-ilgen-static','debugger-stub-static','hot_reload-stub-static','diagnostics_tracing-stub-static']]
sources=[source/'tests/mono_hooks_test.c',source/'src/CJHookNative.c',g1/'src/CJMonoThread.c',g1/'src/CJNativeResolver.c',g1/'src/CanaryNative.c',source.parent/'native-probe/src/VMRange.c',source.parent/'native-probe/src/VMRangeDarwin.c']
command=['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-DCJ_HOOK_HOST_TEST=1','-I'+str(source/'src'),'-I'+str(g1/'src'),'-I'+str(source.parent/'native-probe/src'),'-I'+str(runtime/'pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0'),*map(str,sources),*map(str,libs),'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-o',str(stage/'mono-hooks-test')]
r=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(stage/'compile.log').write_text(r.stdout)
if r.returncode:print(r.stdout);raise SystemExit(r.returncode)
run=[str(stage/'mono-hooks-test'),str(pack/'native/libSystem.Native.dylib'),str(framework),str(fixture)]
with (stage/'run.log').open('w') as log:r=subprocess.run(run,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
text=(stage/'run.log').read_text()
if r.returncode or 'PASS_REAL_MONOMOD_HOOKS' not in text:
 print(text[-13000:]);raise SystemExit(r.returncode or 1)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=next(l for l in text.splitlines() if l.startswith('PASS_REAL_MONOMOD_HOOKS'))
chunks=list(map(int,re.findall(r'HOST_CODE_CHUNK bytes=(\d+)',text)))
assert chunks
receipt={'status':'PASS_ACTUAL_MONO_HOOK_AND_ILHOOK_TWO_WORKERS','summary':summary,'fixture_sha256':sha(fixture),
 'source_sha256':{str(f.relative_to(root)):sha(f) for f in [*sources,Path(__file__)]},'dependencies':json.loads((base/'dependencies-receipt.json').read_text())['assemblies_sha256'],
 'capacity_planning':{'host_chunk_count':len(chunks),'host_cumulative_chunk_bytes':sum(chunks),
 'four_times_host_chunks_rounded_to_16k_bytes':sum(max(16384,((size*4+16383)//16384)*16384) for size in chunks),
 'scope':'planning estimate only; host code-manager sizes and ARM64 emission differ; physical peak still required'},
 'runtime':'Mono 8.0.28 macOS x64 cooperative GC','runtime_commit':'46295af5828b062bbbf93a9cef50fd8cb9fbcb09','aot_and_interpreter_disabled':True,
 'architecture':'x86_64','host_code_memory':'ordinary host Mono JIT pages; device alias path is separate','device_or_background_resume_tested':False,
 'log_sha256':sha(stage/'run.log'),'command':command,'run':run}
(stage/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(summary)
