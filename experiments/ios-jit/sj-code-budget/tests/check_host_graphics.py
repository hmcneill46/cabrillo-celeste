#!/usr/bin/env python3
"""Real desktop FNA/Metal frames on pinned Mono; separate from iOS acceptance."""
import argparse,hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stage=ROOT/'.build/ios-jit/sj-budget-host-test';stage.mkdir(exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',default='Profile');parser.add_argument('--cached',action='store_true');args=parser.parse_args()
if '/' in args.profile or args.profile in ('', '.', '..'): raise ValueError('Profile must be a simple test-directory name.')
runtime=ROOT/'.build/ios-jit/managed-runtime';pack=runtime/'pack-osx-8.0.28/runtimes/osx-x64';mono=runtime/'mono-build-host-coop'
hooks=SOURCE.parent/'hook-canary';g1=SOURCE.parent/'managed-canary'
framework=stage/'Managed';framework.mkdir(exist_ok=True)
runtime_il=ROOT/'.build/ios-jit/sj-budget-managed'
for f in [*list((pack/'lib/net8.0').glob('*.dll')),pack/'native/System.Private.CoreLib.dll']:
    shutil.copy2(f,framework/f.name)
for f in runtime_il.glob('*.dll'):
    if f.name in ['EverestSplash.dll','CelesteJITEverest.dll']: continue
    shutil.copy2(f,framework/f.name)
shutil.copytree(runtime_il/'orig',framework/'orig',dirs_exist_ok=True)
shutil.copy2(ROOT/'.build/ios-jit/everest-lua/host/liblua54.dylib',stage/'liblua54.dylib')
desktop=Path('/Users/harrymcneill/Projects/Celeste Required Files/Celeste Untouched.app/Contents/MacOS/osx')
native=ROOT/'.build/ios-jit/graphics-native-build11'
native_receipt=json.loads((native/'receipt.json').read_text())
shutil.copy2(desktop/'libSDL2-2.0.0.dylib',stage/'libSDL2-2.0.0.dylib')
shutil.copy2(native/'host/libFNA3D.0.dylib',stage/'libFNA3D.0.dylib')
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
runtime_compat=ROOT/'.build/ios-jit/sj-budget-runtime'
runtime_receipt=json.loads((runtime_compat/'receipt.json').read_text())
assert sha(runtime_compat/'host/libmonosgen-2.0.a')==runtime_receipt['targets']['host']['sha256']
libs=[runtime_compat/'host/libmonosgen-2.0.a']+[mono/('mono/mini/libmono-component-'+n+'.a') for n in ['marshal-ilgen-static','debugger-stub-static','hot_reload-stub-static','diagnostics_tracing-stub-static']]
files=[SOURCE/'tests/host_page_model.c',SOURCE/'tests/host_graphics.m',SOURCE/'src/CJGraphicsManaged.m',SOURCE/'src/CJContentImport.m',SOURCE/'src/CJHookNative.c',g1/'src/CJMonoThread.c',g1/'src/CJNativeResolver.c',g1/'src/CanaryNative.c',SOURCE.parent/'native-probe/src/VMRange.c',SOURCE.parent/'native-probe/src/VMRangeDarwin.c']
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
fixture=runtime_il/'CelesteJITEverest.dll'
cmd=[str(stage/'graphics-test'),str(pack/'native/libSystem.Native.dylib'),str(framework),str(fixture),str(stage/'libSDL2-2.0.0.dylib'),str(stage/'libFNA3D.0.dylib'),str(stage/'libfmod.dylib'),str(stage/'libfmodstudio.dylib'),str(stage/'liblua54.dylib')]
env['CJIT_GAME_CONTENT_ROOT']=str(stage/'pending/Content')
env['CJIT_CONTENT_LIBRARY_ROOT']=str(stage/'GameLibrary/v1')
(stage/'GameLibrary/v1').mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(ROOT/'artifacts/ios-jit/everest-canary-20260911-13/CelesteJITEverest-unsigned.ipa') as archive:
    (stage/'GameContentManifest.json').write_bytes(archive.read('Payload/CelesteJITEverest.app/GameContentManifest.json'))
env['CJIT_CONTENT_MANIFEST']=str(stage/'GameContentManifest.json')
env['CJIT_CONTENT_ARCHIVE']='' if args.cached else '/Users/harrymcneill/Projects/Celeste Required Files/celeste-win-opengl.zip' 
env['CJIT_TEST_TOUCH']='1'
env['CJIT_GAME_SAVE_ROOT']=str(stage/args.profile)
mods=stage/args.profile/'Mods';mods.mkdir(parents=True,exist_ok=True)
for stale in mods.glob('GravityHelper-*.zip'): stale.unlink()
for source in (ROOT/'.build/ios-jit/sj-budget-mods').glob('*.zip'):
    shutil.copy2(source,mods/source.name)
inputs=[fixture,libs[0],runtime_compat/'receipt.json',*files,*sorted((SOURCE/'src').glob('*.h')),*sorted((ROOT/'.build/ios-jit/sj-budget-mods').glob('*.zip'))]
initial_inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs}
with (stage/'run.log').open('w') as log:
    r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
output=(stage/'run.log').read_text();assert 'content_library_ready' in output and ('reused=True' if args.cached else 'reused=False') in output;sentinel='PASS_HOST_REAL_LUACUTSCENES_MAXHELPINGHAND_SAVES_AND_RESUME'
if r.returncode or sentinel not in output: print(output[-5500:]);raise SystemExit(r.returncode or 1)
assert all(sha(ROOT/name)==digest for name,digest in initial_inputs.items()), 'A test input changed during execution.'
result=dict(status=sentinel,fixture_sha256=sha(fixture),fna_sha256=sha(framework/'FNA.dll'),
    source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},input_sha256=initial_inputs,
    code_manager_model=dict(page_bytes=16384, granule_bytes=16384, bind_room_divisor=4, minimum_chunk_bytes=65536),
    runtime='pinned Mono 8.0.28 macOS x64 cooperative GC; AOT/interpreter disabled',
    desktop_native_sha256={n:sha(stage/n) for n in ['libSDL2-2.0.0.dylib','libFNA3D.0.dylib','libfmod.dylib','libfmodstudio.dylib','liblua54.dylib']},
    callback_autorelease_pools=True,physical_touch_or_ios_background_tested=False,ios_jit_aliases_tested=False,
    content_retry_test='content_expected_error_retry_pass' in output,profile=args.profile,content_reused=args.cached,content_source=env['CJIT_CONTENT_ARCHIVE'],ns_zombie_enabled=env.get('NSZombieEnabled')=='YES',
    metal_api_validation_requested=env.get('MTL_DEBUG_LAYER')=='1',metal_api_validation_confirmed='Metal API Validation Enabled' in output,
    native_patch_sha256=native_receipt['patch_sha256'],mono_compatibility_receipt_sha256=sha(runtime_compat/'receipt.json'),mono_compatibility_archive_sha256=sha(libs[0]),log_sha256=sha(stage/'run.log'),commands=commands,run=cmd)
(stage/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(sentinel)
