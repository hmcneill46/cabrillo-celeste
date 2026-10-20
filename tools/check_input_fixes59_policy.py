#!/usr/bin/env python3
"""Cross-check Swift layout geometry and managed hit regions, then multi-touch behavior."""
import argparse,json,os,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-input-fixes59'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--sdk',required=True);a=p.parse_args()
    work=ROOT/a.work;sdk=(ROOT/a.sdk).resolve();assert ROOT/'.build' in work.parents and not work.exists();work.mkdir(parents=True)
    sources=[SOURCE/'native/TouchProfile.swift',SOURCE/'tests/TouchProfileTests.swift',SOURCE/'tests/TouchPolicyTests.cs',SOURCE/'managed/TouchConfiguration.cs',ROOT/'modern-ios/CelesteIOSFoundation/TouchControlsPolicy.cs',ROOT/'modern-ios/CelesteIOSFoundation/PlatformPolicies.cs',Path(__file__)]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    env=dict(os.environ,DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer'));commands=[]
    def run(args,name):
        args=list(map(str,args));commands.append(args)
        with (work/(name+'.log')).open('w') as out:r=subprocess.run(args,env=env,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,timeout=180)
        if r.returncode:raise RuntimeError(name+': '+(work/(name+'.log')).read_text()[-3500:])
        print(name+' PASS',flush=True)
    run(['xcrun','swiftc','-O',sources[0],sources[1],'-o',work/'swift-policy'],'compile-swift')
    run([work/'swift-policy',work/'geometry.json'],'swift-policy')
    usings=work/'Usings.cs';usings.write_text('global using System;\nglobal using System.Linq;\nglobal using System.Collections.Generic;\n')
    refs=list((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    rsp=work/'policy.rsp';rsp.write_text('\n'.join(['-nologo','-target:exe','-out:"'+str(work/'Policy.dll')+'"']+['-r:"'+str(p)+'"' for p in refs]+['"'+str(p)+'"' for p in sources[2:6]+[usings]]))
    (work/'Policy.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile-managed')
    run([sdk/'dotnet',work/'Policy.dll',work/'geometry.json'],'managed-policy')
    assert hashes=={str(p.relative_to(ROOT)):sha(p) for p in sources}
    (work/'receipt.json').write_text(json.dumps(dict(status='PASS_TOUCH_GEOMETRY_AND_OWNERSHIP',source_sha256=hashes,commands=commands,logs={p.name:sha(p) for p in work.glob('*.log')},physical_device_tested=False),indent=2)+'\n')
if __name__=='__main__':main()
