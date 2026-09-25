#!/usr/bin/env python3
"""Cabrillo export -> original vanilla serialization -> native import -> real Everest."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-save-transfers'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--game',required=True);p.add_argument('--native',required=True);a=p.parse_args()
    work=ROOT/a.work;game=ROOT/a.game;native=ROOT/a.native
    for f in [work,game,native]:assert f.resolve()==f.absolute() and ROOT/'.build' in f.parents
    assert not work.exists();work.mkdir(parents=True)
    prior=json.loads((game/'receipt.json').read_text());assert prior['status']=='PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT' and prior['hair_fixed']
    for n,h in prior['source_sha256'].items():assert sha(ROOT/n)==h,n
    for n,h in prior['host_managed_sha256'].items():assert sha(game/'Managed'/n)==h,n
    inputs=ROOT/'.private/loading-inputs';manifest=json.loads((inputs/'manifest.json').read_text())['files']
    original=sorted((inputs/'orig').glob('*'))
    for f in original:
        row=manifest[str(f.relative_to(ROOT))];assert sha(f)==(row['sha256'] if isinstance(row,dict) else row)
    sources=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests/VanillaSaveImport.swift',SOURCE/'tests/VanillaSaveCompatibility.cs',Path(__file__)]
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources};commands=[]
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    def run(cmd,label):
        cmd=list(map(str,cmd));commands.append(cmd)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        if r.returncode:raise RuntimeError(label+' failed: '+str(work/(label+'.log')))
    for n in ['Profile','GameLibrary','Managed']:run(['cp','-cR',game/n,work/n],'copy-'+n)
    for n in ['GameContentManifest.json','desktop-main.celeste','SessionIntegrationTests.dll']:shutil.copyfile(game/n,work/n)
    (work/'Incoming').mkdir()
    run(['mono','--version'],'mono-version')
    run(['mcs','-r:System.Xml','-out:'+str(work/'VanillaSave.exe'),SOURCE/'tests/VanillaSaveCompatibility.cs'],'compile-vanilla')
    run(['sandbox-exec','-f',ROOT/'.build/loading-managed-sandbox.sb','mono',work/'VanillaSave.exe',inputs/'orig',work/'desktop-main.celeste',work/'Incoming/0.celeste'],'vanilla')
    run(['xcrun','swiftc','-swift-version','5','-O','-I',native,'-I',ROOT/'vendor/Yams/Sources/CYaml/include',*sources[:-3],SOURCE/'tests/VanillaSaveImport.swift',native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'native-import'],'compile-native')
    run(['sandbox-exec','-f',ROOT/'.build/loading-managed-sandbox.sb',work/'native-import',work],'native-import')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(work/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(work/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='0',CJIT_HOST_NORMAL='1',CJIT_GAME_SAVE_ROOT=str(work/'Profile'),CJIT_SESSION_TEST=str(work/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(ROOT/'.private/loading-host-inputs/ReflectionSignatures.dll'),CJIT_EXPECT_HAIR_FIXED='1')
    command=[str(x).replace(str(game/'Managed'),str(work/'Managed')) for x in prior['commands'][-1]]
    run(command,'everest')
    log=(work/'everest.log').read_text()
    for marker in ['PASS_DESKTOP_SAVE_TRANSFER_REAL_EVEREST','PASS_REAL_GAME_HAIR_MOTION_RESTORED','PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME','game_checks_pass']:assert marker in log,marker
    assert hashes=={n:sha(ROOT/n) for n in hashes}
    result=dict(status='PASS_CABRILLO_VANILLA_EVEREST_SAVE_ROUNDTRIP',source_sha256=hashes,original_input_sha256={str(f.relative_to(ROOT)):sha(f) for f in original},vanilla_save_sha256=sha(work/'Incoming/0.celeste'),game_receipt_sha256=sha(game/'receipt.json'),commands=commands,host_only=True,original_vanilla_serializer=True,all_platforms_or_versions_tested=False)
    (work/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
