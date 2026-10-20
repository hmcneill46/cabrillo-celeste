#!/usr/bin/env python3
"""Check one-process game preparation using the accepted embedded Mono runtime."""
import argparse,hashlib,json,os,shutil,subprocess,zipfile
from compile_unified58 import compile_bootstrap, write_recipe
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--managed', required=True);p.add_argument('--game-files',required=True)
    p.add_argument('--original54-control',action='store_true',help='Compile frozen54 preparation source and require the missing-staging-path failure')
    a=p.parse_args()
    work=ROOT/a.work
    assert ROOT/'.build' in work.parents and not work.exists()
    work.mkdir(parents=True); framework=work/'Managed';framework.mkdir()
    inputs=ROOT/'.private/loading-inputs';pack=inputs/'host/runtime';sdk=inputs/'sdk8'
    public=json.loads((ROOT/a.managed).read_text()) if a.managed else None
    if public:
        assert public['status']=='PASS_PUBLIC_GAME_FREE_MANAGED_BUILD'
        prepared=(ROOT/a.managed).parent/'resources/Managed'
        for name,digest in public['resources'].items():assert hashlib.sha256(((ROOT/a.managed).parent/'resources'/name).read_bytes()).hexdigest()==digest
    else: prepared=ROOT/'.build/everest-managed37-b/tool-artifacts/bin/EverestPrepare/release'
    for f in list((pack/'lib/net8.0').glob('*.dll'))+[pack/'native/System.Private.CoreLib.dll']+list(prepared.glob('*.dll')):
        shutil.copyfile(f,framework/f.name)
    shutil.copyfile(inputs/'host/reflection/System.Private.CoreLib.dll',framework/'System.Private.CoreLib.dll')
    if not public: shutil.copyfile(ROOT/'.build/everest-managed37-b/resources/Managed/FNA.dll',framework/'FNA.dll')
    shutil.copyfile(inputs/'source/Everest/lib-ext/lib64-osx/Steamworks.NET.dll',framework/'Steamworks.NET.dll')
    source=ROOT/'experiments/ios-jit/launcher-unified58'
    catalogue=json.loads((source/'OriginalGameIdentity.json').read_text())
    fixtures=[]
    game_root=Path(a.game_files).resolve()
    for archive in sorted(game_root.rglob('*.zip')):
        with zipfile.ZipFile(archive) as z:
            names=[n for n in z.namelist() if n=='Celeste.exe' or n.endswith('/Celeste.exe')]
            assert len(names)==1, archive
            prefix=names[0][:-len('Celeste.exe')]; pins={}
            for name in ['Celeste.exe','Celeste.Content.dll','FNA.dll','Steamworks.NET.dll']:
                if prefix+name in z.namelist():
                    data=z.read(prefix+name);pins[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            matches=[s for s in catalogue['sources'] if s['inputs']==pins];assert len(matches)==1, archive
            fixtures.append(dict(label=str(archive.relative_to(game_root)),archive=str(archive),prefix=prefix,
                                 source=matches[0]['source_id'],kind=matches[0]['kind']))
            if matches[0]['source_id']==catalogue['legacy_source_id'] and not (work/'original.zip').exists():
                with zipfile.ZipFile(work/'original.zip','w',compression=zipfile.ZIP_DEFLATED) as output:
                    for name in pins:output.writestr(name,z.read(prefix+name))
    assert len(fixtures)==9 and len({f['source'] for f in fixtures})==4
    (work/'fixtures.json').write_text(json.dumps(fixtures,indent=2))
    shutil.copyfile(source/'GameContentManifest.json',work/'GameContentManifest.json')
    native=inputs/'host/native';g1=ROOT/'experiments/ios-jit/managed-canary/src'
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CABRILLO_PREPARATION_PROBE=str(work))
    def run(command,label):
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(list(map(str,command)),cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
        if label=='prepare' and a.original54_control:
            # This embedded Mono console can emit UTF-16 beside native stderr.
            log=(work/(label+'.log')).read_bytes().decode('utf-8',errors='replace').replace('\0','')
            assert r.returncode!=0 and 'CHECK_SAVED_ORIGINALS_WITH_NATIVE_EMPTY_PATH' in log
            assert 'InvalidDataException: Import a complete original Celeste FNA 1.4.0.0 ZIP.' in log
            return
        if r.returncode:raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
        print(label,'PASS',flush=True)
    bootstrap=compile_bootstrap
    if a.original54_control:
        from compile_feather_touch import compile_bootstrap as bootstrap
    bootstrap(sdk,framework,work,run,[source/'tests/GameCodeStoreTests.cs',source/'tests/InputMatrixTests.cs',source/'tools/AssemblyAudit.cs'])
    write_recipe(catalogue,framework,work/'OwnedGameRecipe.json')
    host=(ROOT/'experiments/ios-jit/launcher-visibility/tests/visibility_host.c').read_text()
    host=host.replace('static void *system_native;', 'static uint32_t ImplementationFlags(MonoMethod *method) { uint32_t flags=0; mono_method_get_flags(method,&flags); return flags; }\nstatic void *system_native;')
    host=host.replace('mono_gc_init_finalizer_thread();', 'mono_add_internal_call("System.Reflection.MonoMethodInfo::CJITGetImplementationFlags",(const void *)ImplementationFlags);\n    mono_gc_init_finalizer_thread();')
    host=host.replace('"CelesteJIT.Canary", "Entry"','"Cabrillo.Preparation", "StoreTests"').replace('invoke("Arithmetic", atoi(argv[4]), 36);','invoke("Run", 0, 1);')
    # These are filesystem/parser checks: the runtime's normal platform resolver suffices.
    host=host.replace('static void *system_native;', 'static void *system_native, *compression, *crypto;')
    host=host.replace('return dlsym(system_native, entry);','void *p=dlsym(system_native,entry); if(!p)p=dlsym(compression,entry); if(!p)p=dlsym(crypto,entry); return p;')
    host=host.replace('setenv("DOTNET_SYSTEM_GLOBALIZATION_INVARIANT", "1", 1);',
        'compression=dlopen("'+str(pack/'native/libSystem.IO.Compression.Native.dylib')+'",RTLD_NOW|RTLD_LOCAL); assert(compression);\n'+
        'crypto=dlopen("'+str(pack/'native/libSystem.Security.Cryptography.Native.Apple.dylib')+'",RTLD_NOW|RTLD_LOCAL); assert(crypto);\n'+
        'setenv("DOTNET_SYSTEM_GLOBALIZATION_INVARIANT", "1", 1);')
    (work/'host.c').write_text(host)
    include=ROOT/'.private/inputs/.build/ios-jit/managed-runtime/pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0'
    archive=ROOT/'.build/visibility-runtime36-a/host-fixed/libmonosgen-2.0.a'
    run(['xcrun','clang','-std=c11','-O1','-g','-I'+str(g1),'-I'+str(include),work/'host.c',g1/'CJMonoThread.c',g1/'CJNativeResolver.c',g1/'CanaryNative.c',ROOT/'experiments/ios-jit/launcher-loading/tests/host_page_model.c',archive,*sorted(native.glob('libmono-component-*.a')),'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-o',work/'prepare'],'compile-host')
    env['CJIT_TEST_TPA']=':'.join(str(f) for f in sorted(framework.glob('*.dll')))
    run([work/'prepare',pack/'native/libSystem.Native.dylib',framework,framework/'Cabrillo.Bootstrap.dll','0'],'prepare')
    result=(dict(status='PASS_ORIGINAL54_MISSING_STAGING_PATH_FAILURE_CONTROL',checks=1,game_started=False)
            if a.original54_control else json.loads((work/'result.json').read_text()))
    result['public_managed_receipt_sha256']=hashlib.sha256((ROOT/a.managed).read_bytes()).hexdigest() if public else None
    preparation_source=ROOT/'experiments/ios-jit/launcher-feather-touch' if a.original54_control else source
    result['source_sha256']={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),*sorted((preparation_source/'preparation').glob('*.cs')),source/'tests/GameCodeStoreTests.cs',source/'tests/InputMatrixTests.cs',source/'OriginalGameIdentity.json']}
    result['log_sha256']=hashlib.sha256((work/'prepare.log').read_bytes()).hexdigest()
    (work/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['checks'])

if __name__=='__main__':main()
