#!/usr/bin/env python3
"""Repair the ten player arithmetic mistakes and three lava precision boundaries."""
import argparse,datetime,hashlib,json,os,shutil,subprocess
from pathlib import Path
from loading_inputs import validate_managed, ROOT, local, sha
BASE_SHA='2c7392aa313865137c74cfd13bfb89168eb32d6e9da31421d88ec059581c26e4'
SOURCE=ROOT/'experiments/ios-jit/launcher-save-transfers/tools/RepairPlayerPrecision.cs'
def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    base=local(a.base);assert sha(base)==BASE_SHA
    previous,resources=validate_managed(base)
    work=local(a.work);assert ROOT/'.build' in work.parents and not work.exists();work.mkdir(parents=True)
    sdk=ROOT/'.private/loading-inputs/sdk8'
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    compiler=sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'
    manifest=json.loads((ROOT/'.private/loading-inputs/manifest.json').read_text())['files']
    for f in refs+[compiler,sdk/'dotnet']:
        row=manifest[str(f.relative_to(ROOT))];assert sha(f)==(row['sha256'] if isinstance(row,dict) else row)
    libs=[resources/'Managed'/n for n in ['Mono.Cecil.dll','Mono.Cecil.Rocks.dll']]
    for f in libs:shutil.copyfile(f,work/f.name)
    rsp=work/'repair.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:exe','-out:"'+str(work/'Repair.dll')+'"']+['-r:"'+str(f)+'"' for f in refs+libs]+['"'+str(SOURCE)+'"']))
    (work/'Repair.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
    commands=[]
    def run(cmd,name):
        cmd=list(map(str,cmd));commands.append(cmd)
        with (work/(name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError(name+' failed: '+str(work/(name+'.log')))
    inputs={str(f.relative_to(ROOT)):sha(f) for f in [SOURCE,Path(__file__),ROOT/'tools/save_transfer_inputs.py']}
    run([sdk/'dotnet','exec',compiler,'@'+str(rsp)],'compile')
    output=work/'resources';shutil.copytree(resources,output)
    run(['sandbox-exec','-f',ROOT/'.build/loading-managed-sandbox.sb',sdk/'dotnet',work/'Repair.dll',resources/'Managed/Celeste.dll',output/'Managed/Celeste.dll',work/'repair.json'],'repair')
    repair=json.loads((work/'repair.json').read_text());assert repair['status']=='PASS_SCOPED_PLAYER_PRECISION_REPAIR'
    files={str(f.relative_to(output)):sha(f) for f in output.rglob('*') if f.is_file()}
    assert [n for n in files if files[n]!=previous['resources'][n]]==['Managed/Celeste.dll']
    assert inputs=={n:sha(ROOT/n) for n in inputs}
    receipt=dict(schema=1,status='PASS_PLAYER_PRECISION_REPAIR_BUILD',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),base_receipt=str(base.relative_to(ROOT)),base_receipt_sha256=sha(base),source_sha256=inputs,resources=files,resource_root=str(output.relative_to(ROOT)),repair_sha256=sha(work/'repair.json'),repair=repair,commands=commands,device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],repair['changed_methods'], 'remaining arithmetic findings', len(repair['mixed_after']))
if __name__=='__main__':main()
