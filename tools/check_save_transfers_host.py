#!/usr/bin/env python3
"""Roundtrip a copied real profile, then load, save and Quit with the pinned host game."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
from save_transfer_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-save-transfers'
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
    baseline_expected=dict(expected)
    if a.hair_fixed:baseline_expected['Celeste.dll']=json.loads((ROOT/managed['base_receipt']).read_text())['resources']['Managed/Celeste.dll']
    for name,h in baseline_expected.items():assert sha(host/'Managed'/name)==h,name
    sources=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests/ProfileBackupRoundtrip.swift',Path(__file__)]
    session_sources=[SOURCE/'tests'/n for n in ['SessionIntegrationTests.cs','SaveTransferIntegrationTests.cs','HairMotionTests.cs','ReflectionFlagsTests.cs','RuntimeUpgradeTests.cs']]
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources+session_sources};commands=[]
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    def run(command,label,timeout=600):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if r.returncode:raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
    run(['cp','-cR',host/'Managed',work/'Managed'],'copy-managed')
    if a.hair_fixed:shutil.copyfile(overlay/'Managed/Celeste.dll',work/'Managed/Celeste.dll')
    for name,h in expected.items():assert sha(work/'Managed'/name)==h,name
    for name in ['Profile','GameLibrary']:run(['cp','-cR',host/name,work/name],'copy-'+name)
    shutil.copyfile(host/'GameContentManifest.json',work/'GameContentManifest.json')
    run(['xcrun','swiftc','-swift-version','5','-O','-g','-I',native,'-I',ROOT/'vendor/Yams/Sources/CYaml/include',*sources[:-1],native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'roundtrip'],'compile')
    run([work/'roundtrip',work],'roundtrip')
    run([host/'catalogue',work/'Profile','keep'],'preflight')
    sdk=inputs/'sdk8'
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[work/'Managed'/n for n in ['Celeste.dll','FNA.dll','CelesteIOS.dll','CelesteJITEverest.dll']]
    rsp=work/'session-tests.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'SessionIntegrationTests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(f)+'"' for f in session_sources])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile-game-checks')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(work/'Profile'),CJIT_SESSION_TEST=str(work/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(ROOT/'.private/loading-host-inputs/ReflectionSignatures.dll'))
    env['CJIT_EXPECT_HAIR_FIXED']='1' if a.hair_fixed else '0'
    command=[str(x).replace(str(host/'Managed'),str(work/'Managed')) for x in prior['commands'][-1]]
    run(command,'restored-game')
    output=(work/'restored-game.log').read_text()
    for marker in ['PASS_HOST_COOPERATIVE_BOOT','PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME','PASS_REAL_IOS_SUPPORT_AND_TOUCH_GLYPHS','PASS_REAL_EVEREST_6531_SOURCE_CONTROLS','game_checks_pass','PASS_DESKTOP_SAVE_TRANSFER_REAL_EVEREST']:
        assert marker in output,marker
    assert ('PASS_REAL_GAME_HAIR_MOTION_RESTORED' if a.hair_fixed else 'PASS_REPRODUCED_REAL_GAME_HAIR_MOTION_BUG') in output
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in sources+session_sources}
    receipt=dict(status='PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT',source_sha256=hashes,managed_receipt_sha256=sha(ROOT/a.managed),host_managed_sha256=expected,roundtrip_sha256=sha(work/'roundtrip.json'),game_log_sha256=sha(work/'restored-game.log'),commands=commands,hair_fixed=a.hair_fixed,physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
