#!/usr/bin/env python3
"""Real desktop FNA/Metal frames on pinned Mono; separate from iOS acceptance."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
stage=ROOT/'.build/ios-jit/graphics-host-test';stage.mkdir(exist_ok=True)
runtime=ROOT/'.build/ios-jit/managed-runtime';pack=runtime/'pack-osx-8.0.28/runtimes/osx-x64';mono=runtime/'mono-build-host-coop'
hooks=SOURCE.parent/'hook-canary';g1=SOURCE.parent/'managed-canary'
framework=stage/'Managed';framework.mkdir(exist_ok=True)
for f in [*list((pack/'lib/net8.0').glob('*.dll')),pack/'native/System.Private.CoreLib.dll',*list((ROOT/'.build/ios-jit/hook-runtime/managed-libraries').glob('*.dll')),ROOT/'.build/ios-jit/graphics-managed/FNA.dll']:
    shutil.copy2(f,framework/f.name)
desktop=Path('/Users/harrymcneill/Projects/Celeste Required Files/Celeste Untouched.app/Contents/MacOS/osx')
native=ROOT/'.build/ios-jit/graphics-native-build11'
native_receipt=json.loads((native/'receipt.json').read_text())
shutil.copy2(desktop/'libSDL2-2.0.0.dylib',stage/'libSDL2-2.0.0.dylib')
shutil.copy2(native/'host/libFNA3D.0.dylib',stage/'libFNA3D.0.dylib')
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
libs=[mono/'mono/mini/libmonosgen-2.0.a']+[mono/('mono/mini/libmono-component-'+n+'.a') for n in ['marshal-ilgen-static','debugger-stub-static','hot_reload-stub-static','diagnostics_tracing-stub-static']]
files=[SOURCE/'tests/host_graphics.m',SOURCE/'src/CJGraphicsManaged.m',hooks/'src/CJHookNative.c',g1/'src/CJMonoThread.c',g1/'src/CJNativeResolver.c',g1/'src/CanaryNative.c',SOURCE.parent/'native-probe/src/VMRange.c',SOURCE.parent/'native-probe/src/VMRangeDarwin.c']
objects=[];commands=[]
def run(cmd):
    commands.append(list(map(str,cmd)))
    r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    with (stage/'build.log').open('a') as log: log.write(repr(cmd)+'\n'+r.stdout)
    if r.returncode: raise RuntimeError(r.stdout)
for f in files:
    obj=stage/(f.stem+'.o');objects.append(obj)
    cmd=['xcrun','clang','-O1','-g','-Wall','-Wextra','-Werror','-DCJ_HOOK_HOST_TEST=1','-DCJ_GRAPHICS_HOST_TEST=1',
         '-I'+str(SOURCE/'src'),'-I'+str(hooks/'src'),'-I'+str(g1/'src'),'-I'+str(SOURCE.parent/'native-probe/src'),'-I'+str(runtime/'pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0')]
    cmd+=['-fobjc-arc','-Wno-deprecated-declarations'] if f.suffix=='.m' else ['-std=c11']
    run([*cmd,'-c',str(f),'-o',str(obj)])
run(['xcrun','clang',*map(str,objects),*map(str,libs),'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-framework','AppKit','-Wl,-rpath,'+str(stage),'-o',str(stage/'graphics-test')])
fixture=ROOT/'artifacts/ios-jit/graphics-canary-20260911-11/GraphicsCanary-v0.4.1.dll'
cmd=[str(stage/'graphics-test'),str(pack/'native/libSystem.Native.dylib'),str(framework),str(fixture),str(stage/'libSDL2-2.0.0.dylib'),str(stage/'libFNA3D.0.dylib')]
with (stage/'run.log').open('w') as log:
    r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
output=(stage/'run.log').read_text();sentinel='PASS_HOST_FNA_METAL_539_FRAMES_CALLBACK_POOLS_RESET_SKIP_RESUME_HOOK_AND_MAIN_THREAD_DETACH'
if r.returncode or sentinel not in output: print(output[-5500:]);raise SystemExit(r.returncode or 1)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(status=sentinel,fixture_sha256=sha(fixture),fna_sha256=sha(framework/'FNA.dll'),
    source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},runtime='pinned Mono 8.0.28 macOS x64 with cooperative GC; AOT/interpreter disabled',
    desktop_native_sha256={n:sha(stage/n) for n in ('libSDL2-2.0.0.dylib','libFNA3D.0.dylib')},
    main_thread_attachment_and_detachment=True,gpu_readback=True,render_hook_retained_and_removed=True,
    real_frames=539,callback_autorelease_pools=True,pending_clear_reset=True,suppressed_draw_recovered=True,
    native_patch_sha256=native_receipt["patch_sha256"],native_metal_source_sha256=native_receipt["patched_metal_sha256"],physical_touch_or_ios_background_tested=False,ios_jit_aliases_tested=False,
    code_memory='host Mono pages, no device alias ownership claim',log_sha256=sha(stage/'run.log'),commands=commands,run=cmd)
(stage/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(sentinel)
