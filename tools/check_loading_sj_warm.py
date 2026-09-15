#!/usr/bin/env python3
"""Repeat a completed SJ integration in a fresh process with its existing mod cache and saves."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
from loading_inputs import validate_managed
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--host',required=True);p.add_argument('--edges',required=True);p.add_argument('--managed',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    work=ROOT/a.work;host=ROOT/a.host;edges=ROOT/a.edges
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists():raise ValueError('Use a fresh .build directory')
    validate_managed(ROOT/a.managed);prior=json.loads((edges/'receipt.json').read_text());assert prior['status']=='PASS_REAL_LOADING_EDGE_CASES'
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    assert prior['managed_receipt_sha256']==sha(ROOT/a.managed)
    for name,h in prior['results']['sj']['mod_sha256'].items():assert sha(edges/'sj/Mods'/name)==h
    work.mkdir(parents=True);command=prior['commands'][-1];assert command[0]==str(host/'graphics-test')
    env=dict(os.environ,CJIT_GAME_CONTENT_ROOT=str(edges/'pending/Content'),CJIT_CONTENT_LIBRARY_ROOT=str(edges/'GameLibrary/v1'),CJIT_CONTENT_MANIFEST=str(host/'GameContentManifest.json'),CJIT_CONTENT_ARCHIVE='',CJIT_TEST_TOUCH='1',CJIT_VERIFY_SJ='1',CJIT_GAME_SAVE_ROOT=str(edges/'sj'),CJIT_SESSION_TEST=str(host/'SessionIntegrationTests.dll'),CJIT_REFLECTION_SIGNATURES=str(ROOT/'.private/loading-host-inputs/ReflectionSignatures.dll'))
    env.pop('CJIT_HOST_NORMAL',None)
    with (work/'run.log').open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    output=(work/'run.log').read_text()
    if r.returncode or 'PASS_HOST_REAL_SJ_LOBBY_BING_SAVES_AND_RESUME' not in output:raise RuntimeError('Warm SJ failed; see '+str(work/'run.log'))
    assert 'reused=True' in output and output.count('GAME sj_module_verified ')==52
    progress=[json.loads(line.split('GAME startup_progress ',1)[1]) for line in output.splitlines() if line.startswith('GAME startup_progress ')]
    prior_order=[v['detail'] for v in prior['results']['sj']['progress'] if v['phase']=='mods' and v['total']==-1]
    order=[v['detail'] for v in progress if v['phase']=='mods' and v['total']==-1]
    assert order==prior_order and progress[-1]['phase']=='ready'
    receipt=dict(status='PASS_WARM_SJ_LOADING_GAMEPLAY_SAVE_QUIT',managed_receipt_sha256=sha(ROOT/a.managed),prior_receipt_sha256=sha(edges/'receipt.json'),startup_summary=re.search(r'PASS_HOST_COOPERATIVE_BOOT.*',output).group(),progress=progress,steps=[dict(index=int(i),seconds=float(t),main_thread=m=='1',next_phase=p) for i,t,m,p in re.findall(r'HOST_STARTUP_STEP index=(\d+) duration=([\d.]+) main_thread=(\d) phase=(\w+)',output)],module_order_preserved=True,log_sha256=sha(work/'run.log'),command=command,source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},physical_device_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status']);print(receipt['startup_summary'])
if __name__=='__main__':main()
