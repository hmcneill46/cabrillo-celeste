#!/usr/bin/env python3
"""Actual build17 failure control and page-sized range validation, including Darwin VM."""
import hashlib,json,os,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/sj-lobby-vm-tests';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
physical=R/'.build/ios-jit/device-evidence/2026-09-12/build-17-results'
v=json.loads((physical/'validation.json').read_text());raw=next(physical.glob('CelesteJIT*.json'))
assert sha(raw)==v['raw_sha256']
d=json.loads(raw.read_text());entries=next(e['fields']['details']['entries'] for e in d['current_events'] if e['event']=='check_fail')
assert len(entries)==4096
(O/'physical-prefix.h').write_text('static const CJVMEntry physical_entries[] = {\n'+''.join('{'+f"{r['region_start']}ULL, {r['region_bytes']}, {r['protection']}, {r['maximum_protection']}"+'},\n' for r in entries)+'};\n')
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
results={};inputs=[Path(__file__),S/'tests/vm_range_capacity_test.c',raw,physical/'validation.json',O/'physical-prefix.h']
for old in [True,False]:
 name='build17-control' if old else 'build19-fixed';source=S.parent/'native-probe/src' if old else S/'src'
 files=[source/'VMRange.c',source/'VMRangeDarwin.c'];inputs.extend(files+[source/'VMRange.h'])
 command=['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DCJ_VM_OLD_CONTROL='+str(int(old)),'-I'+str(O),str(S/'tests/vm_range_capacity_test.c'),*map(str,files),'-o',str(O/name)]
 subprocess.run(command,check=True,env=env)
 p=subprocess.run([O/name],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (O/(name+'.log')).write_text(p.stdout);assert p.returncode==0,p.stdout
 result=json.loads(p.stdout.splitlines()[-1]);assert result['cases']==(1 if old else 20),result
 result.update(command=command,log_sha256=sha(O/(name+'.log')));results[name]=result;print(p.stdout.strip())
r=dict(status='PASS_PHYSICAL_BUILD17_LIMIT_CONTROL_AND_PAGE_SIZED_VM_CHECKER',results=results,includes_real_darwin_8192_entries=True,observed_prefix_only_never_accepted=True,late_protection_gap_error_and_missing_tail_controls=True,sanitizers=['address','undefined'],physical_execution=False,input_sha256={str(p.relative_to(R)):sha(p) for p in inputs})
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
