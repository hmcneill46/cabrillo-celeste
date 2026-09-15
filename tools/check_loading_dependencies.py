#!/usr/bin/env python3
"""Compare delayed loading with the exact pinned Everest dependency algorithm."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-loading'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args();work=ROOT/a.work
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists():raise ValueError('Use a fresh .build directory')
    work.mkdir(parents=True);sdk=ROOT/'.private/loading-inputs/sdk8'
    original=ROOT/'.private/loading-inputs/source/Everest/Celeste.Mod.mm/Mod/Everest/Everest.cs';text=original.read_text()
    start=text.index('        internal static void CheckDependenciesOfDelayedMods() {')
    end=text.index('        /// <summary>\n        /// Unregisters an already registered EverestModule',start)
    reference=work/'PinnedReference.cs';reference.write_text('using System;using System.Collections.Generic;using System.Linq;using System.Threading;\nnamespace Celeste.Mod { public static partial class Everest {\n'+text[start:end]+'\n}}\n')
    sources=[SOURCE/'upstream/CabrilloDelayedLoading.cs',SOURCE/'tests/DelayedDependencyTests.cs',reference]
    rsp=work/'tests.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:exe','-out:"'+str(work/'DependencyTests.dll')+'"']+['-r:"'+str(f)+'"' for f in sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))]+['"'+str(f)+'"' for f in sources])+'\n')
    (work/'DependencyTests.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
    env=dict(os.environ,DOTNET_CLI_HOME=str(work/'cli-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1');outputs=[];commands=[]
    for command in [[sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],[sdk/'dotnet',work/'DependencyTests.dll']]:
        command=list(map(str,command));commands.append(command);result=subprocess.run(command,cwd=work,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);outputs.append(result.stdout)
        if result.returncode:raise RuntimeError(result.stdout)
    output='\n'.join(outputs);assert 'PASS_DELAYED_DEPENDENCY_ORDER_AND_LOCKS' in output
    (work/'run.log').write_text(output);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    receipt=dict(status='PASS_DELAYED_DEPENDENCY_ORDER_AND_LOCKS',cases=8,private_reference_sha256=sha(original),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in sources[:2]+[Path(__file__)]},log_sha256=sha(work/'run.log'),commands=commands)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
