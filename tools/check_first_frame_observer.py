#!/usr/bin/env python3
"""Compile the production frame observer; exercise gates and replay supplied phone evidence."""
import argparse,ctypes,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-first-frame'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--evidence',required=True);a=p.parse_args()
    work=ROOT/a.work
    if work.exists() or work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents:raise ValueError('Use fresh .build output')
    evidence=ROOT/a.evidence
    if evidence.resolve()!=evidence.absolute() or ROOT/'.private/device-evidence' not in evidence.parents:raise ValueError('Use a private collected export')
    work.mkdir(parents=True)
    sources=[SOURCE/'src/CJStartupFrame.c',SOURCE/'src/CJStartupFrame.h']
    command=['xcrun','clang','-dynamiclib','-Wall','-Wextra','-Werror',str(sources[0]),'-o',str(work/'observer.dylib')]
    subprocess.run(command,check=True,env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer'))
    class State(ctypes.Structure):_fields_=[('drawn',ctypes.c_bool),('readback',ctypes.c_bool)]
    library=ctypes.CDLL(str(work/'observer.dylib'));observe=library.CJStartupFrameObserve
    observe.argtypes=[ctypes.POINTER(State),ctypes.c_char_p,ctypes.c_char_p,ctypes.c_bool];observe.restype=None
    draw=('game_first_draw','Celeste draw returned; native Present follows.',True)
    read=('game_backbuffer_frame_pass','phase=after_present; width=2796; height=1290; sample=32x18; fnv=9ee0d2c5',True)
    cases=[
        ('start_only',[('game_start_returned','',True)],(False,False)),
        ('draw_only',[draw],(True,False)),
        ('read_before_draw',[read,draw],(True,False)),
        ('worker_draw',[(draw[0],draw[1],False),read],(False,False)),
        ('worker_readback',[draw,(read[0],read[1],False)],(True,False)),
        ('wrong_phase',[draw,('game_backbuffer_frame_pass','phase=after_resume; width=2796',True)],(True,False)),
        ('prefix_collision',[draw,('game_backbuffer_frame_pass','phase=after_present_fake;',True)],(True,False)),
        ('missing_message',[draw,('game_backbuffer_frame_pass',None,True)],(True,False)),
        ('missing_event',[(None,None,True)],(False,False)),
        ('real_frame',[draw,read],(True,True))]
    checks={}
    def apply(state,event):
        n,m,t=event;observe(ctypes.byref(state),n.encode() if n else None,m.encode() if m else None,t)
    for name,events,expected in cases:
        state=State()
        for event in events:apply(state,event)
        assert (state.drawn,state.readback)==expected,name
        checks[name]='PASS'
    export=json.loads(evidence.read_text());replayed=[]
    for events in [export['current_events']]+[p['events'] for p in export['previous_sessions']]:
        launch=next((e for e in events if e['event']=='native_launch'),None)
        if not launch or launch['fields']['build']['build_number']!='31':continue
        state=State();first=None;ready=None;old_handoff=None
        for e in sorted((e for e in events if 'sequence' in e),key=lambda x:x['sequence']):
            f=e['fields'];apply(state,(e['event'],f.get('message'),f.get('main_thread',False)))
            if first is None and e['event']=='graphics_first_frame_returned':
                assert state.drawn and state.readback,'Phone callback lacks real frame proof'
                first=e['uptime_seconds']
            if e['event']=='game_menu' and f.get('message')=='OuiTitleScreen' and ready is None:ready=e['uptime_seconds']
            if e['event']=='startup_window_handoff':old_handoff=e['uptime_seconds']
        assert first is not None and ready>first and old_handoff>first
        replayed.append(dict(session=launch['session'],first_frame_uptime=first,menu_uptime=ready,previous_hidden_seconds=old_handoff-first))
    assert len(replayed)==2
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    receipt=dict(status='PASS_FIRST_FRAME_OBSERVER_AND_PHONE_REPLAY',checks=checks,replayed=replayed,
        source_sha256={str(f.relative_to(ROOT)):sha(f) for f in sources+[Path(__file__)]},evidence_sha256=sha(evidence),
        commands=[command],new_build_phone_execution=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
