#!/usr/bin/env python3
"""Run the production59 resize policy and exact58 draft failure control on public synthetic layouts."""
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LANE=ROOT/'experiments/ios-jit/launcher-input-fixes59'
BASE=ROOT/'experiments/ios-jit/launcher-unified58'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args()
    work=(ROOT/a.work).absolute()
    assert ROOT/'.build' in work.parents and not work.exists()
    work.mkdir(parents=True)
    inputs=[LANE/'native/TouchEditor.swift',LANE/'native/TouchProfile.swift',LANE/'tests/TouchResizeTests.swift',BASE/'native/TouchEditor.swift',Path(__file__)]
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    hashes={str(f.relative_to(ROOT)):sha(f) for f in inputs};commands=[]
    env=dict(os.environ,DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer'))
    def run(args,label):
        command=list(map(str,args));commands.append(command)
        r=subprocess.run(command,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        (work/(label+'.log')).write_text(r.stdout)
        if r.returncode:raise RuntimeError(label+' failed: '+r.stdout[-3000:])
        return r.stdout
    run(['xcrun','swiftc','-O',inputs[0],inputs[1],inputs[2],'-o',work/'resize59'],'compile59')
    output=run([work/'resize59'],'resize59')
    match=re.search(r'PASS_TOUCH_RESIZE59 checks=(\d+) cases=(\d+) tolerance_cases=(\d+) wide_schema_cases=(\d+)',output);assert match
    # Keep the old method body byte-for-byte apart from UI observation wrappers.
    source=inputs[3].read_text();draft=source[source.index('private final class TouchDraft:'):source.index('\nstruct TouchLayoutDocument:')]
    draft=draft.replace('private final class TouchDraft: ObservableObject','final class TouchDraft').replace('@Published ','')
    synthetic='''import Foundation
struct TouchSurface {let width=852.0;let height=393.0;var factory:TouchProfile{.factory(width:width,height:height)};static var current:Self{Self()}}
struct CJTouchStore {static func load(_ surface:TouchSurface)->TouchProfile{surface.factory}}
'''
    fixture=work/'Baseline58.swift'
    fixture.write_text(synthetic+draft+'''
@main enum Baseline58 {
 static func main() {
  for (name,box,shape) in [("right",TouchBox(x:0.97,y:0.5,width:0.03,height:0.15),"rectangle"),("bottom",TouchBox(x:0.5,y:0.97,width:0.15,height:0.03),"rectangle"),("circle",TouchBox(x:0.97,y:1-24/393.0,width:0.03,height:24/393.0),"circle")] {
   let draft=TouchDraft();let i=draft.value.controls.firstIndex{$0.kind=="jump"}!
   draft.value.controls[i].box=box;draft.value.controls[i].shape=shape
   precondition(draft.value.validation()==nil)
   draft.drag(draft.value.controls[i].id,translation:CGSize(width:1,height:1),canvas:CGSize(width:852,height:393),resize:true)
   precondition(draft.value.validation() != nil)
   draft.end();draft.undo();precondition(draft.value.validation()==nil)
   print("EXPECTED_BUILD58_INVALID_RESIZE "+name+" undo_recovers=true")
  }
 }
}
''')
    run(['xcrun','swiftc','-O',inputs[1],fixture,'-o',work/'resize58'],'compile58')
    baseline=run([work/'resize58'],'resize58');assert baseline.count('EXPECTED_BUILD58_INVALID_RESIZE')==3
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in inputs},'Source drift during resize check'
    receipt=dict(status='PASS_BUILD59_RESIZE_AND_BUILD58_NEGATIVE_CONTROL',checks=int(match[1]),resize_cases=int(match[2]),actual_schema_tolerance_cases=int(match[3]),actual_schema_wide_cases=int(match[4]),baseline_invalid_cases=3,source_sha256=hashes,commands=commands,logs={f.name:sha(f) for f in work.glob('*.log')},scope='Actual production Foundation resize policy and actual profile validation; old exact draft method extracted with observation wrappers removed. Synthetic geometry only; no UIKit gesture or physical-device claim.')
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],receipt['checks'],receipt['resize_cases'])
if __name__=='__main__':main()
