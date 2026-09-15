#!/usr/bin/env python3
"""Observe early real game frames using the existing validated host and exact managed payload."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
from loading_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-first-frame'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--host',required=True);p.add_argument('--managed',required=True);a=p.parse_args()
    work=ROOT/a.work;host=ROOT/a.host
    if work.exists() or work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents:raise ValueError('Use fresh .build output')
    if host.resolve()!=host.absolute() or ROOT/'.build' not in host.parents:raise ValueError('Use existing Cabrillo host')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    managed,resources=validate_managed(ROOT/a.managed)
    prior=json.loads((host/'warm-receipt.json').read_text())
    assert prior['status']=='PASS_REAL_HOST_COOPERATIVE_LOADING_GAMEPLAY_SAVE_QUIT'
    for name,h in prior['source_sha256'].items():assert sha(ROOT/name)==h,name
    expected={name.split('/',1)[1]:h for name,h in managed['resources'].items() if name.startswith('Managed/')}
    # The established macOS harness uses its pinned Mono host BCL; the game,
    # adapter, Everest, hooks, FNA and support assembly retain the phone bytes.
    inputs=ROOT/'.private/loading-inputs'
    expected.update({f.name:sha(f) for f in (inputs/'host/runtime/lib/net8.0').glob('*.dll')})
    expected['System.Private.CoreLib.dll']=sha(inputs/'host/reflection/System.Private.CoreLib.dll')
    for name,h in expected.items():assert sha(host/'Managed'/name)==h,name
    work.mkdir(parents=True);env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',
        DOTNET_CLI_HOME=str(work/'cli-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_CLI_TELEMETRY_OPTOUT='1')
    commands=[]
    def run(cmd,label,timeout=360):
        cmd=list(map(str,cmd));commands.append(cmd)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(cmd,env=env,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if r.returncode:raise RuntimeError(label+' failed; inspect '+str(work/(label+'.log')))
    for name in ['Profile','GameLibrary']:run(['cp','-cR',host/name,work/name],'copy-'+name)
    shutil.copyfile(host/'GameContentManifest.json',work/'GameContentManifest.json')
    source=SOURCE/'tests/FirstFrames.cs';dll=work/'SessionIntegrationTests.dll'
    refs=[l for l in (host/'session-tests.rsp').read_text().splitlines() if l.startswith('-r:')]
    rsp=work/'capture.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(dll)+'"',*refs,'"'+str(source)+'"'])+'\n')
    sdk=ROOT/'.private/loading-inputs/sdk8'
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'capture-build')
    run([host/'catalogue',work/'Profile','keep'],'preflight')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),
        CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',
        CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_QUIT_TITLE='1',CJIT_GAME_SAVE_ROOT=str(work/'Profile'),
        CJIT_SESSION_TEST=str(dll),CJIT_REFLECTION_SIGNATURES=str(ROOT/'.private/loading-host-inputs/ReflectionSignatures.dll'),
        CJIT_FRAME_CAPTURE=str(work))
    run(prior['commands'][-1],'frames')
    output=(work/'frames.log').read_text();samples=[l for l in output.splitlines() if l.startswith('FIRST_FRAME_SAMPLE ')]
    # The original title-menu Quit may finish before later optional captures.
    assert any('frame=1;' in l and 'scene=Celeste.GameLoader;' in l for l in samples),samples
    assert any('frame=15;' in l and 'scene=Celeste.GameLoader;' in l for l in samples),samples
    assert any('scene=Celeste.Overworld;' in l for l in samples),samples
    assert 'game_checks_pass' in output and 'game_first_draw' in output
    inputs=[Path(__file__),source,host/'graphics-test',host/'warm-receipt.json',dll]
    receipt=dict(status='PASS_REAL_HOST_EARLY_FRAME_OBSERVATION',samples=samples,images={f.name:sha(f) for f in work.glob('frame-*.png')},
        source_and_input_sha256={str(f.relative_to(ROOT)):sha(f) for f in inputs},managed_receipt_sha256=sha(ROOT/a.managed),
        commands=commands,host_managed_sha256=expected,env={k:v for k,v in env.items() if k.startswith('CJIT_')},
        log_sha256=sha(work/'frames.log'),native_ios_window_tested=False,physical_game_presentation_tested=False,
        performance_benchmark=False,extra_readbacks_only_in_host_fixture=True)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status']);print('\n'.join(samples))
if __name__=='__main__':main()
