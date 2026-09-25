#!/usr/bin/env python3
"""Exercise the released Motion Smoothing mod using a private copied host profile."""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--host',required=True);p.add_argument('--mod',required=True);p.add_argument('--managed',required=True);a=p.parse_args()
    work=ROOT/a.work;host=ROOT/a.host;mod=ROOT/a.mod
    assert all(x.resolve()==x.absolute() and ROOT/'.build' in x.parents for x in [work,host,mod]) and not work.exists()
    prior=json.loads((host/'receipt.json').read_text());assert prior['status']=='PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT' and prior['hair_fixed']
    assert sha(mod)=='fb021011aa505e5670cf08ade375e7f80b58eb40c5045f9da15556a9bff888d2'
    for name,h in prior['host_managed_sha256'].items():assert sha(host/'Managed'/name)==h,name
    from platform_inputs import validate_managed
    derived,overlay=validate_managed(ROOT/a.managed)
    work.mkdir(parents=True);commands=[]
    source=ROOT/'experiments/ios-jit/launcher-platforms/tests/MotionSmoothingTests.cs'
    native_source=source.parent/'host_motion.m'
    inputs=[source,native_source,Path(__file__)]
    hashes={str(x.relative_to(ROOT)):sha(x) for x in inputs}
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    def run(cmd,label,timeout=600):
        cmd=list(map(str,cmd));commands.append(cmd)
        with (work/(label+'.log')).open('w') as f:r=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        if r.returncode:raise RuntimeError(label+' failed; see '+str(work/(label+'.log')))
    run(['cp','-cR',host/'Managed',work/'Managed'],'managed')
    shutil.copyfile(overlay/'Managed/CelesteJITEverest.dll',work/'Managed/CelesteJITEverest.dll')
    run(['cp','-cR',host/'GameLibrary',work/'GameLibrary'],'content')
    shutil.copyfile(host/'GameContentManifest.json',work/'GameContentManifest.json')
    sdk=ROOT/'.private/loading-inputs/sdk8'
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))+[work/'Managed'/n for n in ['Celeste.dll','FNA.dll']]
    rsp=work/'tests.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:library','-out:"'+str(work/'Tests.dll')+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(source)+'"'])+'\n')
    run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile')
    original=ROOT/'.build/loading-host30-c'
    lock=json.loads((ROOT/'experiments/ios-jit/launcher-loading/Dependencies.json').read_text())
    includes=[ROOT/'experiments/ios-jit/launcher-loading/src',ROOT/'experiments/ios-jit/managed-canary/src']+[ROOT/n for n in lock['include_directories']]
    run(['xcrun','clang','-O1','-g','-Wall','-Wextra','-Werror','-DCJ_HOOK_HOST_TEST=1','-DCJ_GRAPHICS_HOST_TEST=1','-fobjc-arc','-Wno-deprecated-declarations',*['-I'+str(d) for d in includes],'-c',native_source,'-o',work/'host_motion.o'],'native-test')
    objects=[work/'host_motion.o']+[x for x in sorted(original.glob('*.o')) if x.name!='host_graphics.o']
    native=ROOT/'.private/loading-inputs/host/native'
    libraries=[native/'libmonosgen-2.0.a']+sorted(native.glob('libmono-component-*.a'))
    run(['xcrun','clang',*objects,*libraries,'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-framework','AppKit','-Wl,-rpath,'+str(original),'-o',work/'motion-test'],'link-native-test')
    results=[]
    for fps,renderer in [(60,'Fast'),(120,'Fast'),(60,'Fancy'),(120,'Fancy')]:
        name=f'{fps}-{renderer}';profile=work/('Profile-'+name)
        run(['cp','-cR',host/'Profile',profile],'profile-'+name)
        shutil.copyfile(mod,profile/'Mods'/mod.name)
        # The original ZIP is indexed and its exact identity enters the launcher manifest.
        catalogue=ROOT/'.build/loading-host30-c/catalogue'
        run([catalogue,profile,'keep'],'catalogue-'+name)
        env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),
            CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',
            CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(profile),CJIT_SESSION_TEST=str(work/'Tests.dll'),CJIT_MOTION_FPS=str(fps),CJIT_MOTION_RENDERER=renderer)
        cmd=[str(x).replace(str(host/'Managed'),str(work/'Managed')) for x in prior['commands'][-1]]
        cmd[0]=str(work/'motion-test')
        run(['sandbox-exec','-f',ROOT/'.build/loading-managed-sandbox.sb',*cmd],name)
        log=(work/(name+'.log')).read_text()
        markers=[line for line in log.splitlines() if line.startswith('PASS_MOTION_SMOOTHING_REAL_GAME')]
        assert len(markers)==1 and 'PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME' in log,name
        results.append(dict(fps=fps,renderer=renderer,observation=markers[0],log_sha256=sha(work/(name+'.log'))))
        print('PASS '+name,flush=True)
    assert hashes=={str(x.relative_to(ROOT)):sha(x) for x in inputs}
    receipt=dict(status='PASS_MOTION_SMOOTHING_HOST',managed_receipt_sha256=sha(ROOT/a.managed),mod_sha256=sha(mod),source_sha256=hashes,host_receipt_sha256=sha(host/'receipt.json'),results=results,commands=commands,physical_display_or_ios_jit_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':main()
