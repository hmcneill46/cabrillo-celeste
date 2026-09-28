#!/usr/bin/env python3
"""Run original Motion Smoothing at 60/120 callbacks with the owned-game bootstrap."""
import argparse, json, os, shutil, subprocess
from pathlib import Path
from compile_owned_game import ROOT, SOURCE, sha

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--host',required=True); p.add_argument('--work',required=True); p.add_argument('--mod',required=True)
    a=p.parse_args(); host=(ROOT/a.host).resolve(); work=(ROOT/a.work).resolve(); mod=(ROOT/a.mod).resolve()
    assert ROOT/'.build' in work.parents and not work.exists()
    prior=json.loads((host/'receipt.json').read_text()); assert prior['status']=='PASS_OWNED_GAME_COLD_WARM_GAMEPLAY'
    assert sha(mod)=='fb021011aa505e5670cf08ade375e7f80b58eb40c5045f9da15556a9bff888d2'
    for name,h in prior['game_free_bundle'].items(): assert sha(host/'Managed'/name)==h
    work.mkdir(parents=True); env=dict(os.environ); commands=[]
    def run(cmd,label):
        cmd=list(map(str,cmd)); commands.append(cmd)
        with (work/(label+'.log')).open('w') as f:r=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
        if r.returncode: raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
    sdk=ROOT/'.build/owned-public-inputs38-d/sdk8.0-osx-x64'
    recipe=host/'OwnedGameRecipe.json'; generation_root=host/'GameCode/v1'/sha(recipe)
    generation=json.loads((generation_root/'active.json').read_text())['generation']
    game=generation_root/generation/'Celeste.dll'
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[game,host/'Managed/FNA.dll']
    source=SOURCE/'tests/MotionSmoothingTests.cs'; rsp=work/'tests.rsp'
    rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'Tests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(source)+'"'])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile')
    results=[]
    for fps,renderer in [(60,'Fast'),(120,'Fast'),(60,'Fancy'),(120,'Fancy')]:
        name=str(fps)+'-'+renderer; profile=work/('Profile-'+name)
        run(['cp','-cR',host/'warm/Profile',profile],'profile-'+name)
        shutil.copyfile(mod,profile/'Mods'/mod.name)
        run([ROOT/'.build/everest-game37-c/catalogue',profile,'keep'],'catalogue-'+name)
        env.update(CJIT_GAME_CONTENT_ROOT=str(host/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(host/'GameLibrary/v1'),
            CJIT_CONTENT_MANIFEST=str(host/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',
            CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(profile),CJIT_SESSION_TEST=str(work/'Tests.dll'),CJIT_MOTION_FPS=str(fps),CJIT_MOTION_RENDERER=renderer,
            CJIT_GAME_CODE_ROOT=str(host/'GameCode/v1'),CJIT_GAME_CODE_RECIPE=str(recipe))
        run(prior['commands'][-1],name)
        log=(work/(name+'.log')).read_text()
        marker=[line for line in log.splitlines() if line.startswith('PASS_MOTION_SMOOTHING_REAL_GAME')]
        assert len(marker)==1 and 'PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME' in log,name
        results.append(dict(fps=fps,renderer=renderer,marker=marker[0],log_sha256=sha(work/(name+'.log')))); print('PASS '+name,flush=True)
    (work/'receipt.json').write_text(json.dumps(dict(status='PASS_OWNED_GAME_MOTION',host_receipt_sha256=sha(host/'receipt.json'),mod_sha256=sha(mod),commands=commands,results=results,physical_display_tested=False),indent=2)+'\n')
if __name__=='__main__': main()
