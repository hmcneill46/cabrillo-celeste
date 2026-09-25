#!/usr/bin/env python3
"""Rebuild only the launcher adapter over the exact build34 precision payload."""
import argparse, datetime, json, os, shutil, subprocess
from pathlib import Path
from loading_inputs import ROOT, local, sha
from save_transfer_inputs import validate_managed

BASE_SHA='80bb0a19d7f63944aa6fe23379338c747db776cae51744c73482a390425b13aa'

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    base=local(a.base);assert sha(base)==BASE_SHA
    previous,resources=validate_managed(base)
    work=local(a.work);assert ROOT/'.build' in work.parents and not work.exists();work.mkdir(parents=True)
    inputs=ROOT/'.private/loading-inputs';sdk=inputs/'sdk8'
    sources=sorted((ROOT/'experiments/ios-jit/launcher-loading/managed').glob('*.cs'))
    sources=[ROOT/'experiments/ios-jit/launcher-platforms/managed/GameEntry.cs' if s.name=='GameEntry.cs' else s for s in sources]
    sources += [ROOT/'modern-ios/CelesteIOSFoundation'/n for n in ['PlatformPolicies.cs','TouchControlsPolicy.cs']]
    hashes={str(x.relative_to(ROOT)):sha(x) for x in sources+[Path(__file__),ROOT/'tools/platform_inputs.py']}
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    compiler=sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'
    assets=sorted((inputs/'touch-assets').glob('*.a8'))
    manifest=json.loads((inputs/'manifest.json').read_text())['files']
    for f in refs+[compiler,sdk/'dotnet']+assets:assert sha(f)==manifest[str(f.relative_to(ROOT))]['sha256']
    output=work/'resources';shutil.copytree(resources,output)
    libs=[output/'Managed'/n for n in ['Celeste.dll','FNA.dll','MMHOOK_Celeste.dll','MonoMod.Core.dll','MonoMod.RuntimeDetour.dll','MonoMod.Utils.dll','Mono.Cecil.dll','NLua.dll','KeraLua.dll','Newtonsoft.Json.dll','CelesteIOS.dll']]
    rsp=work/'adapter.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-unsafe+','-nullable:annotations','-optimize+','-deterministic+','-target:library','-out:"'+str(output/'Managed/CelesteJITEverest.dll')+'"']+['-r:"'+str(x)+'"' for x in refs+libs]+['"'+str(x)+'"' for x in sources]+['-resource:"'+str(x)+'",Celeste.IOSTouchControls.'+x.name for x in assets])+'\n')
    command=list(map(str,[sdk/'dotnet','exec',compiler,'@'+str(rsp)]))
    with (work/'compile.log').open('w') as f:r=subprocess.run(command,cwd=work,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Adapter compile failed: '+str(work/'compile.log'))
    files={str(f.relative_to(output)):sha(f) for f in output.rglob('*') if f.is_file()}
    assert {n for n,h in files.items() if h!=previous['resources'][n]}=={'Managed/CelesteJITEverest.dll'}
    assert hashes=={str(x.relative_to(ROOT)):sha(x) for x in sources+[Path(__file__),ROOT/'tools/platform_inputs.py']}
    # Carry the original precision repair evidence through unchanged.
    shutil.copyfile(base.parent/'repair.json',work/'repair.json')
    receipt=dict(schema=1,status='PASS_PLATFORM_ADAPTER_BUILD',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        base_receipt=str(base.relative_to(ROOT)),base_receipt_sha256=BASE_SHA,source_sha256=hashes,
        resource_root=str(output.relative_to(ROOT)),resources=files,changed_resources=['Managed/CelesteJITEverest.dll'],
        repair_sha256=sha(work/'repair.json'),commands=[command],device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])

if __name__=='__main__':main()
