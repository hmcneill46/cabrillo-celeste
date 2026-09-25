#!/usr/bin/env python3
"""Compile and test the production profile store in an isolated native host process."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-save-transfers'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args()
    work=ROOT/a.work
    assert work.resolve()==work.absolute() and ROOT/'.build' in work.parents and not work.exists()
    work.mkdir(parents=True);native=work/'native';native.mkdir()
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    sources=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests/ProfileBackupTests.swift',SOURCE/'tests/SaveTransferTests.swift']
    vendor=sorted((ROOT/'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml=ROOT/'vendor/Yams/Sources/CYaml';c=sorted((yaml/'src').glob('*.c'))
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    inputs=sources+vendor+c+[Path(__file__)];hashes={str(f.relative_to(ROOT)):sha(f) for f in inputs};commands=[]
    def run(command,label):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError(label+' failed; '+str(work/(label+'.log')))
    run(['xcrun','swiftc','-swift-version','5','-O','-module-name','ZIPFoundation','-emit-library','-static','-emit-module','-emit-module-path',native/'ZIPFoundation.swiftmodule','-o',native/'libZIPFoundation.a',*vendor],'zip')
    for f in c:run(['xcrun','clang','-DYAML_DECLARE_STATIC','-O2','-I'+str(yaml/'include'),'-c',f,'-o',native/(f.stem+'.o')],f.stem)
    run(['xcrun','libtool','-static','-o',native/'libCYaml.a',*[native/(f.stem+'.o') for f in c]],'yaml')
    run(['xcrun','swiftc','-swift-version','5','-O','-g','-I',native,'-I',yaml/'include',*sources,native/'libZIPFoundation.a',native/'libCYaml.a','-o',work/'tests'],'compile')
    run(['sandbox-exec','-f',ROOT/'.build/loading-managed-sandbox.sb',work/'tests',work/'results'],'tests')
    result=json.loads((work/'results/results.json').read_text());assert result['status']=='PASS_PROFILE_BACKUPS'
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in inputs},'Sources changed during check'
    receipt=dict(status=result['status'],created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=len(result['checks']),source_sha256=hashes,results_sha256=sha(work/'results/results.json'),commands=commands,physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],receipt['checks'])
if __name__=='__main__':main()
