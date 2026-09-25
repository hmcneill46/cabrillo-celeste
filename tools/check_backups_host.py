#!/usr/bin/env python3
"""Roundtrip a copied real profile, then load, save and Quit with the pinned host game."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
from loading_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-backups'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--host',required=True);p.add_argument('--native',required=True);p.add_argument('--managed',required=True);a=p.parse_args()
    work=ROOT/a.work;host=ROOT/a.host;native=ROOT/a.native
    for path in [work,host,native]:assert path.resolve()==path.absolute() and ROOT/'.build' in path.parents
    assert not work.exists();work.mkdir(parents=True)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    prior=json.loads((host/'warm-receipt.json').read_text());assert prior['status']=='PASS_REAL_HOST_COOPERATIVE_LOADING_GAMEPLAY_SAVE_QUIT'
    for name,h in prior['source_sha256'].items():assert sha(ROOT/name)==h,name
    native_receipt=json.loads((native.parent/'receipt.json').read_text());assert native_receipt['status']=='PASS_PROFILE_BACKUPS'
    for name,h in native_receipt['source_sha256'].items():assert sha(ROOT/name)==h,name
    managed,_=validate_managed(ROOT/a.managed)
    expected={name.split('/',1)[1]:h for name,h in managed['resources'].items() if name.startswith('Managed/')}
    inputs=ROOT/'.private/loading-inputs'
    expected.update({f.name:sha(f) for f in (inputs/'host/runtime/lib/net8.0').glob('*.dll')});expected['System.Private.CoreLib.dll']=sha(inputs/'host/reflection/System.Private.CoreLib.dll')
    for name,h in expected.items():assert sha(host/'Managed'/name)==h,name
    sources=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests/ProfileBackupRoundtrip.swift',Path(__file__)]
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources};commands=[]
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    def run(command,label,timeout=600):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if r.returncode:raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
    for name in ['Profile','GameLibrary']:run(['cp','-cR',host/name,work/name],'copy-'+name)
    shutil.copyfile(host/'GameContentManifest.json',work/'GameContentManifest.json')
    run(['xcrun','swiftc','-swift-version','5','-O','-g','-I',native,'-I',ROOT/'vendor/Yams/Sources/CYaml/include',*sources[:-1],native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'roundtrip'],'compile')
    run([work/'roundtrip',work],'roundtrip')
    run([host/'catalogue',work/'Profile','keep'],'preflight')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(work/'Profile'),CJIT_SESSION_TEST=str(host/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(ROOT/'.private/loading-host-inputs/ReflectionSignatures.dll'))
    run(prior['commands'][-1],'restored-game')
    output=(work/'restored-game.log').read_text()
    for marker in ['PASS_HOST_COOPERATIVE_BOOT','PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME','PASS_REAL_IOS_SUPPORT_AND_TOUCH_GLYPHS','PASS_REAL_EVEREST_6531_SOURCE_CONTROLS','game_checks_pass']:
        assert marker in output,marker
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in sources}
    receipt=dict(status='PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT',source_sha256=hashes,managed_receipt_sha256=sha(ROOT/a.managed),host_managed_sha256=expected,roundtrip_sha256=sha(work/'roundtrip.json'),game_log_sha256=sha(work/'restored-game.log'),commands=commands,physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
