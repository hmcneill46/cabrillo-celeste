#!/usr/bin/env python3
"""Run real Everest/Metal startup, gameplay, save and Quit in Cabrillo's private host fixture."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
from loading_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-loading'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--managed',required=True);p.add_argument('--cached',action='store_true');a=p.parse_args()
    work=ROOT/a.work
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists()!=a.cached:raise ValueError('Use a fresh .build directory, or --cached after its successful cold run')
    managed,resources=validate_managed(ROOT/a.managed)
    inputs=ROOT/'.private/loading-inputs';fixtures=ROOT/'.private/loading-host-inputs'
    manifest=json.loads((fixtures/'manifest.json').read_text())
    for name,row in manifest['files'].items():
        if sha(fixtures/name)!=row['sha256']:raise ValueError('Changed host fixture: '+name)
    if not a.cached:work.mkdir(parents=True)
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',DOTNET_CLI_HOME=str(work/'cli-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    commands=[]
    def run(command,label='build',timeout=600):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('a') as log:
            log.write(repr(command)+'\n');log.flush();result=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if result.returncode:raise RuntimeError(label+' failed; see '+str(work/(label+'.log')))
    framework=work/'Managed';pack=inputs/'host/runtime';host=inputs/'host/native';sdk=inputs/'sdk8'
    native_sources=[SOURCE/'src/CJSession.c',SOURCE/'tests/host_page_model.c',SOURCE/'tests/host_graphics.m',SOURCE/'src/CJLoadingState.m',SOURCE/'src/CJGraphicsManaged.m',SOURCE/'src/CJContentImport.m',SOURCE/'src/CJHookNative.c',ROOT/'experiments/ios-jit/managed-canary/src/CJMonoThread.c',ROOT/'experiments/ios-jit/managed-canary/src/CJNativeResolver.c',ROOT/'experiments/ios-jit/managed-canary/src/CanaryNative.c',SOURCE/'src/VMRange.c',SOURCE/'src/VMRangeDarwin.c']
    swift=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests/CatalogueTool.swift']
    session_sources=[SOURCE/'tests'/n for n in ['SessionIntegrationTests.cs','ReflectionFlagsTests.cs','RuntimeUpgradeTests.cs']]
    source_paths=native_sources+swift+session_sources+list((SOURCE/'src').glob('*.h'))+[Path(__file__),ROOT/'tools/loading_inputs.py']
    source_hashes={str(f.relative_to(ROOT)):sha(f) for f in source_paths}
    if a.cached:
        prior=json.loads((work/'cold-receipt.json').read_text())
        if prior['source_sha256']!=source_hashes or prior['managed_receipt_sha256']!=sha(ROOT/a.managed):raise ValueError('Cold/warm must use identical source and managed output')
    else:
        shutil.copytree(resources/'Managed',framework)
        for f in (pack/'lib/net8.0').glob('*.dll'):shutil.copyfile(f,framework/f.name)
        shutil.copyfile(inputs/'host/reflection/System.Private.CoreLib.dll',framework/'System.Private.CoreLib.dll')
        for f in host.glob('*.dylib'):shutil.copyfile(f,work/f.name)
        objects=[]
        lock=json.loads((SOURCE/'Dependencies.json').read_text())
        includes=[SOURCE/'src',ROOT/'experiments/ios-jit/hook-canary/src',ROOT/'experiments/ios-jit/managed-canary/src',ROOT/'experiments/ios-jit/native-probe/src']+[ROOT/n for n in lock['include_directories']]
        for f in native_sources:
            obj=work/(f.stem+'.o');objects.append(obj)
            run(['xcrun','clang','-O1','-g','-Wall','-Wextra','-Werror','-DCJ_HOOK_HOST_TEST=1','-DCJ_GRAPHICS_HOST_TEST=1',*['-I'+str(d) for d in includes],*(['-fobjc-arc','-Wno-deprecated-declarations'] if f.suffix=='.m' else ['-std=c11']),'-c',f,'-o',obj])
        libraries=[host/'libmonosgen-2.0.a']+sorted(host.glob('libmono-component-*.a'))
        assert len(libraries)==5
        run(['xcrun','clang',*objects,*libraries,'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-framework','AppKit','-Wl,-rpath,'+str(work),'-o',work/'graphics-test'])
        refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
        refs += [framework/n for n in ['Celeste.dll','FNA.dll','CelesteIOS.dll','CelesteJITEverest.dll']]
        rsp=work/'session-tests.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'SessionIntegrationTests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(f)+'"' for f in session_sources])+'\n')
        run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)])
        native=work/'native';native.mkdir();yaml=ROOT/'vendor/Yams/Sources/CYaml'
        run(['xcrun','swiftc','-swift-version','5','-O','-module-name','ZIPFoundation','-emit-library','-static','-emit-module','-emit-module-path',native/'ZIPFoundation.swiftmodule','-o',native/'libZIPFoundation.a',*sorted((ROOT/'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))])
        objects=[]
        for f in sorted((yaml/'src').glob('*.c')):
            obj=native/(f.stem+'.o');objects.append(obj);run(['xcrun','clang','-DYAML_DECLARE_STATIC','-O2','-I'+str(yaml/'include'),'-c',f,'-o',obj])
        run(['xcrun','libtool','-static','-o',native/'libCYaml.a',*objects])
        run(['xcrun','swiftc','-swift-version','5','-O','-I',native,'-I',yaml/'include',*swift,native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'catalogue'])
        shutil.copytree(fixtures/'catalogue-profile',work/'Profile')
        for f in fixtures.glob('CJITCodeCanary*.zip'):shutil.copyfile(f,work/'Profile/Mods'/f.name)
        shutil.copyfile(resources/'GameContentManifest.json',work/'GameContentManifest.json')
        (work/'GameLibrary/v1').mkdir(parents=True)
    run([work/'catalogue',work/'Profile','keep'],'preflight-warm' if a.cached else 'preflight-cold')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='' if a.cached else str(fixtures/'celeste-win-opengl.zip'),CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(work/'Profile'),CJIT_SESSION_TEST=str(work/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(fixtures/'ReflectionSignatures.dll'))
    label='warm' if a.cached else 'cold'
    run([work/'graphics-test',pack/'native/libSystem.Native.dylib',framework,framework/'CelesteJITEverest.dll',*[work/n for n in ['libSDL2-2.0.0.dylib','libFNA3D.0.dylib','libfmod.dylib','libfmodstudio.dylib','liblua54.dylib']]],label)
    output=(work/(label+'.log')).read_text()
    for sentinel in ['PASS_HOST_COOPERATIVE_BOOT','PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME','PASS_REAL_IOS_SUPPORT_AND_TOUCH_GLYPHS','PASS_REAL_EVEREST_6531_SOURCE_CONTROLS','PASS_MONO_REFLECTION_FLAGS_CONTRACT','everest_selection_module_verified Cateline 0.1.0;','everest_selection_module_verified memorialHelper 1.0.4;','content_library_ready','reused=True' if a.cached else 'reused=False']:
        if sentinel not in output:raise ValueError('Missing host evidence: '+sentinel)
    steps=re.findall(r'HOST_STARTUP_STEP index=(\d+) duration=([\d.]+) main_thread=(\d) phase=(\w+)',output)
    progress=[json.loads(line.split('GAME startup_progress ',1)[1]) for line in output.splitlines() if line.startswith('GAME startup_progress ')]
    assert steps and all(row[2]=='1' for row in steps) and progress[-1]['phase']=='ready'
    assert all(sha(ROOT/n)==h for n,h in source_hashes.items())
    receipt=dict(status='PASS_REAL_HOST_COOPERATIVE_LOADING_GAMEPLAY_SAVE_QUIT',cached_content=a.cached,managed_receipt_sha256=sha(ROOT/a.managed),source_sha256=source_hashes,private_fixture_manifest_sha256=sha(fixtures/'manifest.json'),steps=[dict(index=int(i),seconds=float(t),main_thread=bool(int(m)),phase=p) for i,t,m,p in steps],progress=progress,reflection_checks=output.count('REFLECTION_FLAGS_PASS '),session_checks=output.count('SESSION_CONTRACT_PASS '),host_runtime='Mono 8.0.28 macOS x64; 16KiB code allocation model; Metal',physical_loading_or_jit_tested=False,log_sha256=sha(work/(label+'.log')),commands=commands)
    (work/(label+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],label)
if __name__=='__main__':main()
