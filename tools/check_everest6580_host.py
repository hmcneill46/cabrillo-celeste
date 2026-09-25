#!/usr/bin/env python3
"""Roundtrip a copied real profile, then load, save and Quit with the pinned host game."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
from everest6580_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-everest6580'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--host',required=True);p.add_argument('--native',required=True);p.add_argument('--managed',required=True);p.add_argument('--hair-fixed',action='store_true');a=p.parse_args()
    work=ROOT/a.work;host=ROOT/a.host;native=ROOT/a.native
    for path in [work,host,native]:assert path.resolve()==path.absolute() and ROOT/'.build' in path.parents
    assert not work.exists();work.mkdir(parents=True)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    prior=json.loads((host/'warm-receipt.json').read_text());assert prior['status']=='PASS_REAL_HOST_COOPERATIVE_LOADING_GAMEPLAY_SAVE_QUIT'
    for name,h in prior['source_sha256'].items():assert sha(ROOT/name)==h,name
    native_receipt=json.loads((native.parent/'receipt.json').read_text());assert native_receipt['status']=='PASS_PROFILE_BACKUPS'
    for name,h in native_receipt['source_sha256'].items():assert sha(ROOT/name)==h,name
    managed,overlay=validate_managed(ROOT/a.managed)
    expected={name.split('/',1)[1]:h for name,h in managed['resources'].items() if name.startswith('Managed/')}
    inputs=ROOT/'.private/loading-inputs'
    expected.update({f.name:sha(f) for f in (inputs/'host/runtime/lib/net8.0').glob('*.dll')});expected['System.Private.CoreLib.dll']=sha(inputs/'host/reflection/System.Private.CoreLib.dll')
    sources=sorted(f for f in (SOURCE/'native').glob('*.swift') if f.name!='PlatformViews.swift')+[SOURCE/'tests/ProfileBackupRoundtrip.swift',Path(__file__)]
    session_sources=[SOURCE/'tests'/n for n in ['SessionIntegrationTests.cs','SaveTransferIntegrationTests.cs','HairMotionTests.cs','ReflectionFlagsTests.cs','RuntimeUpgradeTests.cs']]
    hash_inputs=sources+session_sources+[SOURCE/'tests/CatalogueTool.swift'];hashes={str(f.relative_to(ROOT)):sha(f) for f in hash_inputs};commands=[]
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    def run(command,label,timeout=600):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if r.returncode:raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
    run(['cp','-cR',host/'Managed',work/'Managed'],'copy-managed')
    for name in ['Celeste.dll','Celeste.Mod.mm.dll','MMHOOK_Celeste.dll','CelesteJITEverest.dll']:shutil.copyfile(overlay/'Managed'/name,work/'Managed'/name)
    for name,h in expected.items():assert sha(work/'Managed'/name)==h,name
    for name in ['Profile','GameLibrary']:run(['cp','-cR',host/name,work/name],'copy-'+name)
    shutil.copyfile(host/'GameContentManifest.json',work/'GameContentManifest.json')
    run(['xcrun','swiftc','-swift-version','5','-O','-g','-I',native,'-I',ROOT/'vendor/Yams/Sources/CYaml/include',*sources[:-1],native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'roundtrip'],'compile')
    run([work/'roundtrip',work],'roundtrip')
    catalogue_sources=[x for x in sources[:-1] if x.name!='ProfileBackupRoundtrip.swift']+[SOURCE/'tests/CatalogueTool.swift']
    run(['xcrun','swiftc','-swift-version','5','-O','-I',native,'-I',ROOT/'vendor/Yams/Sources/CYaml/include',*catalogue_sources,native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'catalogue'],'compile-catalogue')
    run([work/'catalogue',work/'Profile','keep'],'preflight')
    sdk=inputs/'sdk8'
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[work/'Managed'/n for n in ['Celeste.dll','FNA.dll','CelesteIOS.dll','CelesteJITEverest.dll','Mono.Cecil.dll','MonoMod.Utils.dll']]
    rsp=work/'session-tests.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'SessionIntegrationTests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(f)+'"' for f in session_sources])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile-game-checks')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(work/'Profile'),CJIT_SESSION_TEST=str(work/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(ROOT/'.private/loading-host-inputs/ReflectionSignatures.dll'))
    env['CJIT_EXPECT_HAIR_FIXED']='1' if a.hair_fixed else '0'
    native_runtime=json.loads((ROOT/'.build/visibility-runtime36-a/receipt.json').read_text())
    archive=ROOT/native_runtime['host_fixed']['path'];assert sha(archive)==native_runtime['host_fixed']['sha256']
    objects=sorted(host.glob('*.o'));assert len(objects)==12
    host_libs=ROOT/'.private/loading-inputs/host/native'
    run(['xcrun','clang',*objects,archive,*sorted(host_libs.glob('libmono-component-*.a')),'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-framework','AppKit','-Wl,-rpath,'+str(host),'-o',work/'graphics-test'],'link-corrected-host')
    command=[str(x).replace(str(host/'Managed'),str(work/'Managed')) for x in prior['commands'][-1]]
    command[0]=str(work/'graphics-test')
    run(command,'restored-game')
    output=(work/'restored-game.log').read_text()
    for marker in ['PASS_HOST_COOPERATIVE_BOOT','PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME','PASS_REAL_IOS_SUPPORT_AND_TOUCH_GLYPHS','PASS_REAL_EVEREST_6580_SOURCE_CONTROLS','game_checks_pass','PASS_DESKTOP_SAVE_TRANSFER_REAL_EVEREST']:
        assert marker in output,marker
    assert ('PASS_REAL_GAME_HAIR_MOTION_RESTORED' if a.hair_fixed else 'PASS_REPRODUCED_REAL_GAME_HAIR_MOTION_BUG') in output
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in hash_inputs}
    receipt=dict(status='PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT',source_sha256=hashes,managed_receipt_sha256=sha(ROOT/a.managed),host_managed_sha256=expected,roundtrip_sha256=sha(work/'roundtrip.json'),game_log_sha256=sha(work/'restored-game.log'),commands=commands,hair_fixed=a.hair_fixed,native_runtime_sha256=sha(archive),everest_version='1.6580.0',physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
