#!/usr/bin/env python3
"""Exercise cooperative scheduling, progress validation and diagnostic retention."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-loading'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args()
    work=ROOT/a.work
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists():raise ValueError('Use a fresh .build directory')
    work.mkdir(parents=True)
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',DOTNET_CLI_HOME=str(work/'cli-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1')
    commands=[]
    def run(command):
        command=list(map(str,command));commands.append(command)
        result=subprocess.run(command,cwd=work,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        with (work/'run.log').open('a') as log:log.write(repr(command)+'\n'+result.stdout)
        if result.returncode:raise RuntimeError(result.stdout)
        return result.stdout
    native=[SOURCE/'src/CJLoadingState.m',SOURCE/'src/CJEventStore.m',SOURCE/'tests/LoadingStateTests.m']
    run(['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-I'+str(SOURCE/'src'),*native,'-framework','Foundation','-o',work/'state-tests'])
    assert 'PASS_LOADING_STATE_AND_RETENTION' in run([work/'state-tests',work/'state-results'])
    sdk=ROOT/'.private/loading-inputs/sdk8'
    sources=[SOURCE/'upstream/CabrilloLoading.cs',SOURCE/'tests/CooperativeLoadingTests.cs']
    rsp=work/'contracts.rsp'
    rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:exe','-out:"'+str(work/'Contracts.dll')+'"']+['-r:"'+str(f)+'"' for f in sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))]+['"'+str(f)+'"' for f in sources])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)])
    (work/'Contracts.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
    output=run([sdk/'dotnet',work/'Contracts.dll'])
    assert 'PASS_COOPERATIVE_LOADING_CONTRACT' in output
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    receipt=dict(status='PASS_LOADING_CONTRACTS',managed_checks=output.count('PASS '),native=json.loads((work/'state-results/result.json').read_text()),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in native+sources+[SOURCE/'src/CJLoadingState.h',SOURCE/'src/CJEventStore.h',Path(__file__)]},log_sha256=sha(work/'run.log'),commands=commands)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
