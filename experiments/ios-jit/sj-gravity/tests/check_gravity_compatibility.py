#!/usr/bin/env python3
"""Run the packaged compatibility transform/policy on pinned Mono with controls."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2];STAGE=ROOT/'.build/ios-jit/sj-gravity-compat-tests';STAGE.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=ROOT/'.build/ios-jit/managed-runtime';sdk=base/'dotnet-sdk-8.0.422';mono=base/'mono-build-host-coop';pack=base/'pack-osx-8.0.28/runtimes/osx-x64';g1=SOURCE.parent/'managed-canary'
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
managed=ROOT/'.build/ios-jit/sj-gravity-managed';framework=STAGE/'Managed';framework.mkdir(exist_ok=True)
for p in list((pack/'lib/net8.0').glob('*.dll'))+[pack/'native/System.Private.CoreLib.dll']+list(managed.glob('*.dll')):shutil.copy2(p,framework/p.name)
fixture=framework/'GravityCompatibilityTests.dll';refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
rsp=STAGE/'compile.rsp';rsp.write_text('\n'.join(['-nologo','-target:library','-nostdlib+','-deterministic+','-optimize+','-out:"'+str(fixture)+'"']+['-r:"'+str(p)+'"' for p in refs+[managed/'CelesteJITEverest.dll',managed/'Mono.Cecil.dll']]+['"'+str(SOURCE/'tests/GravityCompatibilityTests.cs')+'"']))
commands=[]
def run(command):
 commands.append(list(map(str,command)));subprocess.run(command,env=env,check=True)
run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)])
archive=ROOT/'.build/ios-jit/sj-budget-runtime/host/libmonosgen-2.0.a';libraries=[archive]+[mono/('mono/mini/libmono-component-'+n+'-static.a') for n in ['marshal-ilgen','debugger-stub','hot_reload-stub','diagnostics_tracing-stub']]
# The existing small native harness invokes Entry.Arithmetic and checks its result.
sources=[SOURCE/'tests/visibility_host.c',SOURCE/'tests/host_page_model.c',g1/'src/CJMonoThread.c',g1/'src/CJNativeResolver.c',g1/'src/CanaryNative.c']
run(['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-I'+str(g1/'src'),'-I'+str(base/'pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0'),*map(str,sources),*map(str,libraries),'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-o',str(STAGE/'test')])
env['CJIT_TEST_TPA']=':'.join(str(p) for p in framework.glob('*.dll'))
inputs=[ROOT/'.build/ios-jit/sj-gravity-inputs/GravityHelper.dll',ROOT/'.build/ios-jit/sj-gravity-host-test/GravityProfile/Mods/Cache/GravityHelper.GravityHelper.dll']
results=[]
for i,p in enumerate(inputs):
 env['CJIT_GRAVITY_TEST_INPUT']=str(p);r=subprocess.run([STAGE/'test',pack/'native/libSystem.Native.dylib',framework,fixture,'0'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (STAGE/(str(i)+'.log')).write_text(r.stdout)
 assert r.returncode==0 and 'PASS_GRAVITY_COMPATIBILITY_CONTROLS checks=17' in r.stdout,r.stdout[-6000:]
 results.append(dict(input_path=str(p.relative_to(ROOT)),input_sha256=sha(p),log_sha256=sha(STAGE/(str(i)+'.log'))));print(r.stdout[-420:])
(STAGE/'receipt.json').write_text(json.dumps(dict(status='PASS_GRAVITY_OPTIONAL_TRANSFORM_AND_POLICY_CONTROLS_ON_MONO',cases_per_input=17,results=results,adapter_sha256=sha(managed/'CelesteJITEverest.dll'),mono_archive_sha256=sha(archive),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),SOURCE/'tests/GravityCompatibilityTests.cs',SOURCE/'managed/GravityOptionalIntegration.cs',*sources]},commands=commands,real_celestenet_integration_tested=False),indent=2)+'\n')
