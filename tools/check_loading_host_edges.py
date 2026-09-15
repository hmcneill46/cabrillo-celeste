#!/usr/bin/env python3
"""Additional real-Everest controls: multi-module ZIP, thrown mod load and full SJ profile."""
import argparse,hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
from loading_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-loading'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--host',required=True);p.add_argument('--work',required=True);p.add_argument('--managed',required=True);a=p.parse_args()
    work=ROOT/a.work;host=ROOT/a.host
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists():raise ValueError('Use a fresh .build directory')
    _,resources=validate_managed(ROOT/a.managed)
    warm=json.loads((host/'warm-receipt.json').read_text());assert warm['managed_receipt_sha256']==sha(ROOT/a.managed)
    for n,h in warm['source_sha256'].items():assert sha(ROOT/n)==h,n
    work.mkdir(parents=True);inputs=ROOT/'.private/loading-inputs';fixtures=ROOT/'.private/loading-host-inputs';sj=ROOT/'.private/loading-sj-inputs'
    for name,row in json.loads((sj/'manifest.json').read_text())['files'].items():assert sha(sj/name)==row['sha256']
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',DOTNET_CLI_HOME=str(work/'cli-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1')
    sdk=inputs/'sdk8';commands=[]
    def run(command,label,expected=0):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        if r.returncode!=expected:raise RuntimeError(label+' returned '+str(r.returncode)+'; see '+str(work/(label+'.log')))
        return (work/(label+'.log')).read_text()
    rsp=work/'failure.rsp'
    rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'FailingStartupMod.dll')+'"']+['-r:"'+str(f)+'"' for f in sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))]+['-r:"'+str(resources/'Managed/Celeste.dll')+'"','"'+str(SOURCE/'tests/FailingStartupMod.cs')+'"'])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'failure-build')
    shutil.copytree(host/'GameLibrary',work/'GameLibrary')
    results={}
    for case in ['pair','failure','sj']:
        profile=work/case;mods=profile/'Mods';mods.mkdir(parents=True)
        for f in (sj if case=='sj' else fixtures/'catalogue-profile/Mods').glob('*.zip'):shutil.copyfile(f,mods/f.name)
        if case!='sj':
            for f in fixtures.glob('CJITCodeCanary*.zip'):shutil.copyfile(f,mods/f.name)
            with zipfile.ZipFile(mods/'CabrilloStartupPair.zip','w') as z:z.writestr('everest.yaml','- Name: CabrilloStartupPairOne\n  Version: 1.0.0\n- Name: CabrilloStartupPairTwo\n  Version: 1.0.0\n')
        if case=='failure':
            with zipfile.ZipFile(mods/'CabrilloStartupFailure.zip','w') as z:
                z.writestr('everest.yaml','- Name: CabrilloStartupFailure\n  Version: 1.0.0\n  DLL: FailingStartupMod.dll\n  Dependencies: [{Name: Everest, Version: 1.6531.0}]\n')
                z.write(work/'FailingStartupMod.dll','FailingStartupMod.dll')
        run([host/'catalogue',profile,'full'],case+'-preflight')
        env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(host/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='1' if case=='sj' else '0',CJIT_GAME_SAVE_ROOT=str(profile),CJIT_SESSION_TEST=str(host/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(fixtures/'ReflectionSignatures.dll'))
        if case=='sj':env.pop('CJIT_HOST_NORMAL',None)
        else:env['CJIT_HOST_NORMAL']='1'
        output=run([host/'graphics-test',inputs/'host/runtime/native/libSystem.Native.dylib',host/'Managed',host/'Managed/CelesteJITEverest.dll',*[host/n for n in ['libSDL2-2.0.0.dylib','libFNA3D.0.dylib','libfmod.dylib','libfmodstudio.dylib','liblua54.dylib']]],case,expected=3 if case=='failure' else 0)
        progress=[json.loads(line.split('GAME startup_progress ',1)[1]) for line in output.splitlines() if line.startswith('GAME startup_progress ')]
        if case=='failure':
            assert 'HOST_START_FAILED' in output and 'CABRILLO_EXPECTED_STARTUP_MOD_FAILURE' in output
            assert any(v['load_failures']>=1 and v['detail']=='CabrilloStartupFailure 1.0.0' for v in progress)
            assert not any(v['phase']=='ready' for v in progress) and 'GAME game_shutdown_stage_started' not in output
        elif case=='pair':
            assert 'PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME' in output
            assert all('everest_selection_module_verified '+n+' 1.0.0;' in output for n in ['CabrilloStartupPairOne','CabrilloStartupPairTwo'])
            assert progress[-1]['archives_processed']==4 and progress[-1]['modules_loaded']==5 and progress[-1]['load_failures']==0
        else:
            assert 'PASS_HOST_REAL_SJ_LOBBY_BING_SAVES_AND_RESUME' in output and output.count('GAME sj_module_verified ')==52
        results[case]=dict(status='PASS',progress=progress,log_sha256=sha(work/(case+'.log')),mod_sha256={f.name:sha(f) for f in mods.glob('*.zip')})
        print('PASS_REAL_LOADING_'+case.upper(),flush=True)
    sources=[Path(__file__),SOURCE/'tests/FailingStartupMod.cs']
    receipt=dict(status='PASS_REAL_LOADING_EDGE_CASES',host_warm_receipt_sha256=sha(host/'warm-receipt.json'),managed_receipt_sha256=sha(ROOT/a.managed),results=results,commands=commands,source_sha256={str(f.relative_to(ROOT)):sha(f) for f in sources},physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
