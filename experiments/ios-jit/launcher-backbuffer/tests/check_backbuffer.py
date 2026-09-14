#!/usr/bin/env python3
"""Real desktop FNA/Metal frames on pinned Mono; separate from iOS acceptance."""
import argparse,hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stage=ROOT/'.build/ios-jit/launcher-backbuffer-contract-tests';stage.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--original',action='store_true');args=parser.parse_args()
runtime=ROOT/'.build/ios-jit/managed-runtime';pack=runtime/'pack-osx-8.0.28/runtimes/osx-x64';mono=runtime/'mono-build-host-coop'
hooks=SOURCE.parent/'hook-canary';g1=SOURCE.parent/'managed-canary'
framework=stage/'Managed';framework.mkdir(exist_ok=True)
runtime_il=ROOT/'.build/ios-jit/launcher-backbuffer-managed'
for f in [*list((pack/'lib/net8.0').glob('*.dll')),pack/'native/System.Private.CoreLib.dll']:
    shutil.copy2(f,framework/f.name)
for f in runtime_il.glob('*.dll'):
    if f.name in ['EverestSplash.dll','CelesteJITEverest.dll']: continue
    shutil.copy2(f,framework/f.name)
shutil.copytree(runtime_il/'orig',framework/'orig',dirs_exist_ok=True)
shutil.copy2(ROOT/'.build/ios-jit/everest-lua/host/liblua54.dylib',stage/'liblua54.dylib')
desktop=Path('/Users/harrymcneill/Projects/Celeste Required Files/Celeste Untouched.app/Contents/MacOS/osx')
native=ROOT/('.build/ios-jit/graphics-native-build11' if args.original else '.build/ios-jit/launcher-backbuffer-renderer')
native_receipt=json.loads((native/'receipt.json').read_text())
shutil.copy2(desktop/'libSDL2-2.0.0.dylib',stage/'libSDL2-2.0.0.dylib')
shutil.copy2(native/'host/libFNA3D.0.dylib',stage/'libFNA3D.0.dylib')
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
runtime_compat=ROOT/'.build/ios-jit/sj-lobby-runtime'
runtime_receipt=json.loads((runtime_compat/'receipt.json').read_text())
assert sha(runtime_compat/'host/libmonosgen-2.0.a')==runtime_receipt['targets']['host']['sha256']
libs=[runtime_compat/'host/libmonosgen-2.0.a']+[mono/('mono/mini/libmono-component-'+n+'.a') for n in ['marshal-ilgen-static','debugger-stub-static','hot_reload-stub-static','diagnostics_tracing-stub-static']]
files=[SOURCE/'src/CJSession.c',SOURCE/'tests/host_page_model.c',SOURCE/'tests/host_backbuffer.m',SOURCE/'src/CJGraphicsManaged.m',SOURCE/'src/CJContentImport.m',SOURCE/'src/CJHookNative.c',g1/'src/CJMonoThread.c',g1/'src/CJNativeResolver.c',g1/'src/CanaryNative.c',SOURCE/'src/VMRange.c',SOURCE/'src/VMRangeDarwin.c']
objects=[];commands=[]
def run(cmd):
    commands.append(list(map(str,cmd)))
    r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    with (stage/'build.log').open('a') as log: log.write(repr(cmd)+'\n'+r.stdout)
    if r.returncode: raise RuntimeError(r.stdout)
for name in ['libfmod.dylib','libfmodstudio.dylib']: shutil.copy2(desktop/name,stage/name)
for f in files:
    obj=stage/(f.stem+'.o');objects.append(obj)
    cmd=['xcrun','clang','-O1','-g','-Wall','-Wextra','-Werror','-DCJ_HOOK_HOST_TEST=1','-DCJ_GRAPHICS_HOST_TEST=1',
         '-I'+str(ROOT/'.build/ios-jit/game-native-output/SDL2.xcframework/ios-arm64/Headers'),'-I'+str(SOURCE/'src'),'-I'+str(hooks/'src'),'-I'+str(g1/'src'),'-I'+str(SOURCE.parent/'native-probe/src'),'-I'+str(runtime/'pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0')]
    cmd+=['-fobjc-arc','-Wno-deprecated-declarations'] if f.suffix=='.m' else ['-std=c11']
    run([*cmd,'-c',str(f),'-o',str(obj)])
run(['xcrun','clang',*map(str,objects),*map(str,libs),'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-framework','AppKit','-Wl,-rpath,'+str(stage),'-o',str(stage/'graphics-test')])
fixture=stage/'BackbufferFixture.dll'
cmd=[str(stage/'graphics-test'),str(pack/'native/libSystem.Native.dylib'),str(framework),str(fixture),str(stage/'libSDL2-2.0.0.dylib'),str(stage/'libFNA3D.0.dylib'),str(stage/'libfmod.dylib'),str(stage/'libfmodstudio.dylib'),str(stage/'liblua54.dylib')]
sdk=runtime/'dotnet-sdk-8.0.422';refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
rsp=stage/'fixture.rsp'
fixture_sources=[SOURCE/'tests/BackbufferFixture.cs',SOURCE/'managed/BackbufferChecks.cs']
rsp.write_text('\n'.join(['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:library','-out:"'+str(fixture)+'"']+['-r:"'+str(p)+'"' for p in refs+[runtime_il/'FNA.dll']]+['"'+str(p)+'"' for p in fixture_sources])+'\n')
run([str(sdk/'dotnet'),'exec',str(sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)])
env['MTL_DEBUG_LAYER']='1'
if args.original:env['CJIT_ORIGINAL_BACKBUFFER']='1'
case='original' if args.original else 'fixed';log=stage/(case+'.log')
with log.open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
output=log.read_text()
if args.original:
 assert r.returncode!=0 and 'ABOUT_TO_READ_ORIGINAL_BACKBUFFER' in output and ('Assertion' in output or 'SIGSEGV' in output or 'SIGABRT' in output),output[-6000:]
else:
 assert r.returncode==0 and 'PASS_ACTUAL_MONO_METAL_BACKBUFFER' in output and 'PASS_BACKBUFFER_NATIVE_CALLBACK_AND_MONO_DETACH' in output,output[-6000:]
assert 'Metal API Validation Enabled' in output
inputs=[*files,SOURCE/'tests/host_graphics.m',*fixture_sources,Path(__file__),runtime_il/'FNA.dll',libs[0],native/'receipt.json',native/'host/libFNA3D.0.dylib']
receipt=dict(status='PASS_ORIGINAL_NATIVE_READBACK_FAILURE_CONTROL' if args.original else 'PASS_ACTUAL_MONO_METAL_BACKBUFFER',exit_code=r.returncode,checks=output.count('BACKBUFFER_PASS '),pattern_checks=output.count('graphics_check_pass backbuffer_'),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},fna_sha256=sha(runtime_il/'FNA.dll'),renderer_sha256=sha(native/'host/libFNA3D.0.dylib'),fixture_sha256=sha(fixture),log_sha256=sha(log),metal_validation=True,callback_pools=True,physical_ios_tested=False,commands=commands,run=cmd)
(stage/(case+'.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],receipt['checks'],receipt['pattern_checks'])
