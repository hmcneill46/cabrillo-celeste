#!/usr/bin/env python3
"""Confirm changed prepared-game metadata is confined to the Everest loading code."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from loading_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-loading'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--managed',required=True);a=p.parse_args();work=ROOT/a.work
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists():raise ValueError('Use a fresh .build directory')
    _,resources=validate_managed(ROOT/a.managed);work.mkdir(parents=True);sdk=ROOT/'.private/loading-inputs/sdk8'
    source=SOURCE/'tests/AssemblyComparison.cs';refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[resources/'Managed/Mono.Cecil.dll']
    rsp=work/'audit.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-nullable:annotations','-target:exe','-out:"'+str(work/'AssemblyComparison.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(source)+'"'])+'\n')
    (work/'AssemblyComparison.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
    (work/'Mono.Cecil.dll').write_bytes((resources/'Managed/Mono.Cecil.dll').read_bytes())
    env=dict(os.environ,DOTNET_CLI_HOME=str(work/'cli-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1');commands=[]
    def run(command):
        command=list(map(str,command));commands.append(command)
        with (work/'run.log').open('a') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError('Assembly audit failed; see '+str(work/'run.log'))
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)])
    for name,game in [('before',ROOT/'.private/resources/build28/Managed/Celeste.dll'),('after',resources/'Managed/Celeste.dll')]:run([sdk/'dotnet',work/'AssemblyComparison.dll',game,work/(name+'.json')])
    old=json.loads((work/'before.json').read_text());new=json.loads((work/'after.json').read_text())
    assert old['identity']==new['identity'] and sorted(old['references'])==sorted(new['references']) and old['resources']==new['resources']
    differences={}
    for category in ['types','methods','fields']:
        changed=[key for key in old[category].keys()|new[category].keys() if old[category].get(key)!=new[category].get(key)]
        for key in changed:
            # Compiler-generated iterator/closure numbers also change inside
            # these two partial types. Other game/mod classes must be identical.
            declaring=key.split('::',1)[0].rsplit(' ',1)[-1]
            assert declaring in ['Celeste.Mod.Everest','Celeste.Mod.CabrilloLoading'] or declaring.startswith(('Celeste.Mod.Everest/','Celeste.Mod.CabrilloLoading/')),key
        differences[category]=sorted(changed)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    receipt=dict(status='PASS_PREPARED_GAME_CHANGE_SCOPE',identity_unchanged=True,assembly_reference_set_unchanged=True,all_embedded_resources_unchanged=True,changes_confined_to_everest_loading_types=True,changed_counts={k:len(v) for k,v in differences.items()},managed_receipt_sha256=sha(ROOT/a.managed),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [source,Path(__file__)]},commands=commands)
    (work/'differences.json').write_text(json.dumps(differences,indent=2)+'\n');(work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
