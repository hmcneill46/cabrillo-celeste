#!/usr/bin/env python3
"""Build the pinned public SDL for private host controller/LED integration tests."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    inputs=(ROOT/a.inputs).resolve();work=(ROOT/a.work).resolve();assert ROOT/'.build' in work.parents
    receipt=json.loads((inputs/'receipt.json').read_text());assert receipt['status']=='PASS_PUBLIC_SOURCE_INPUTS'
    expected={n[5:]:h for n,h in receipt['files'].items() if n.startswith('SDL2/')}
    def verify(source):
        for n,h in expected.items():assert sha(source/n)==h,n
        assert {str(f.relative_to(source)) for f in source.rglob('*') if f.is_file()}==set(expected)
    verify(inputs/'SDL2');work.mkdir(exist_ok=True,parents=True)
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer');commands=[]
    def run(args,name):
        args=list(map(str,args));commands.append(args)
        with (work/(name+'.log')).open('w') as log:r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError(name+' failed: '+str(work/(name+'.log')))
        print(name+' PASS',flush=True)
    if not (work/'source').exists():run(['cp','-cR',inputs/'SDL2',work/'source'],'copy-source')
    verify(work/'source')
    run(['cmake','-S',work/'source','-B',work/'build','-DCMAKE_BUILD_TYPE=Release','-DSDL_SHARED=ON','-DSDL_STATIC=OFF','-DSDL_TEST=OFF','-DSDL_TESTS=OFF','-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DHAVE_GCC_WERROR_DECLARATION_AFTER_STATEMENT=OFF'],'configure-verified')
    run(['cmake','--build',work/'build','--parallel','6'],'build')
    library=work/'build/libSDL2-2.0.0.dylib';assert library.is_file();verify(work/'source')
    result=dict(status='PASS_PINNED_HOST_SDL',input_receipt_sha256=sha(inputs/'receipt.json'),source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},source_files=expected,commands=commands,library=str(library.relative_to(ROOT)),library_sha256=sha(library),logs={f.name:sha(f) for f in work.glob('*.log')},physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
