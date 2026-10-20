#!/usr/bin/env python3
"""Exercise original Player death/respawn and cross-map grab persistence privately."""
import argparse,json,os,subprocess,shutil
from compile_input_preferences import ROOT,SOURCE,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--host',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    host=(ROOT/a.host).resolve();work=(ROOT/a.work).resolve();assert ROOT/'.build' in work.parents and not work.exists()
    prior=json.loads((host/'receipt.json').read_text());assert prior['status']=='PASS_OWNED_GAME_COLD_WARM_GAMEPLAY'
    for name,h in prior['game_free_bundle'].items():assert sha(host/'Managed'/name)==h
    work.mkdir();env=dict(os.environ);commands=[]
    def run(cmd,label):
        cmd=list(map(str,cmd));commands.append(cmd)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        if r.returncode:raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
        print(label+' PASS',flush=True)
    recipe=host/'OwnedGameRecipe.json';code=host/'GameCode/v1'/sha(recipe)/json.loads((host/'GameCode/v1/selected-source.json').read_text())['source']
    generation=json.loads((code/'active.json').read_text())['generation'];sdk=ROOT/'.build/release51-local/inputs/sdk8.0-osx-x64'
    sources=[SOURCE/'tests/GrabLifecycleTests.cs',__import__('pathlib').Path(__file__)];hashes={str(f.relative_to(ROOT)):sha(f) for f in sources}
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[code/generation/'Celeste.dll']+[host/'Managed'/n for n in ['FNA.dll','CelesteJITEverest.dll']]
    rsp=work/'tests.rsp';rsp.write_text('\n'.join(['-nologo','-target:library','-out:"'+str(work/'Tests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(sources[0])+'"']))
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile')
    profile=work/'Profile';run(['cp','-cR',host/'cold/Profile',profile],'profile')
    env.update(CJIT_GAME_CONTENT_ROOT=str(host/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(host/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(host/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_TOUCH_CONFIG=str(work/'TouchConfig.json'),CJIT_GAME_SAVE_ROOT=str(profile),CJIT_FEATHER_TOUCH='0',CJIT_SESSION_TEST=str(work/'Tests.dll'),CJIT_GAME_CODE_ROOT=str(host/'GameCode/v1'),CJIT_GAME_CODE_RECIPE=str(recipe))
    run(prior['commands'][-1],'lifecycle');output=(work/'lifecycle.log').read_text();assert 'PASS_REAL_GRAB_DEATH_AND_MAPS' in output and 'PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME' in output
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in sources}
    (work/'receipt.json').write_text(json.dumps(dict(status='PASS_REAL_GRAB_DEATH_AND_MAPS',source_sha256=hashes,commands=commands,host_receipt_sha256=sha(host/'receipt.json'),log_sha256=sha(work/'lifecycle.log'),physical_device_tested=False),indent=2)+'\n')
if __name__=='__main__':main()
