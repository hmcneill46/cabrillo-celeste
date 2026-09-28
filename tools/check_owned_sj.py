#!/usr/bin/env python3
"""Run the retained full Strawberry Jam fixture through owned-game preparation/cache."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from compile_owned_game import ROOT,SOURCE,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    host=(ROOT/a.host).resolve(); work=(ROOT/a.work).resolve();assert ROOT/'.build' in work.parents and not work.exists()
    prior=json.loads((host/'receipt.json').read_text());assert prior['status']=='PASS_OWNED_GAME_COLD_WARM_GAMEPLAY'
    for n,h in prior['game_free_bundle'].items():assert sha(host/'Managed'/n)==h
    work.mkdir(parents=True); profile=work/'Profile'; mods=profile/'Mods';mods.mkdir(parents=True)
    fixture=ROOT/'.private/loading-sj-inputs'; fixture_manifest=fixture/'manifest.json'; files=json.loads(fixture_manifest.read_text())['files']
    commands=[];env=dict(os.environ)
    def run(cmd,label):
        cmd=list(map(str,cmd));commands.append(cmd)
        with (work/(label+'.log')).open('w') as f:r=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
        if r.returncode:raise RuntimeError(label+' failed; see '+str(work/(label+'.log')))
    for n,row in files.items():
        assert sha(fixture/n)==row['sha256']; run(['cp','-c',fixture/n,mods/n],'copy-'+n)
    shutil.copyfile(host/'warm/Profile/Mods/CJITCodeCanary-v1.0.0.zip',mods/'CJITCodeCanary-v1.0.0.zip')
    run([ROOT/'.build/everest-game37-c/catalogue',profile,'keep'],'catalogue')
    sdk=ROOT/'.build/owned-public-inputs38-d/sdk8.0-osx-x64';recipe=host/'OwnedGameRecipe.json'
    generations=host/'GameCode/v1'/sha(recipe); generation=json.loads((generations/'active.json').read_text())['generation']
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[generations/generation/'Celeste.dll',host/'Managed/FNA.dll']
    response=work/'compile.rsp';response.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'Tests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(SOURCE/'tests/OwnedGameSjTests.cs')+'"'])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(response)],'compile')
    env.update(CJIT_GAME_CONTENT_ROOT=str(host/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(host/'GameLibrary/v1'),
        CJIT_CONTENT_MANIFEST=str(host/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='1',
        CJIT_GAME_SAVE_ROOT=str(profile),CJIT_SESSION_TEST=str(work/'Tests.dll'),CJIT_GAME_CODE_ROOT=str(host/'GameCode/v1'),CJIT_GAME_CODE_RECIPE=str(recipe))
    env.pop('CJIT_HOST_NORMAL',None)
    for stage in ['cold-mods','warm-mods']:
        run(prior['commands'][-1],stage)
        log=(work/(stage+'.log')).read_text()
        assert 'PASS_HOST_REAL_SJ_LOBBY_BING_SAVES_AND_RESUME' in log and log.count('GAME sj_module_verified ')==52,stage
        print('PASS '+stage,flush=True)
    (work/'receipt.json').write_text(json.dumps(dict(status='PASS_OWNED_GAME_SJ_COLD_WARM',host_receipt_sha256=sha(host/'receipt.json'),
        fixture_manifest_sha256=sha(fixture_manifest),mod_sha256={f.name:sha(f) for f in sorted(mods.glob('*.zip'))},commands=commands,
        logs={n:sha(work/(n+'.log')) for n in ['cold-mods','warm-mods']},physical_device_tested=False),indent=2)+'\n')
if __name__=='__main__':main()
