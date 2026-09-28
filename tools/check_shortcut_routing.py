#!/usr/bin/env python3
"""Compile/run the native launch reducer and exercise generated shortcut branches.

These are host controls, not a claim that iOS Shortcuts/VPN/JIT has passed on-device.
"""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
from build_shortcut_files import generate, launch_url

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-shortcut-routing'

def execute(workflow, supplied=None):
    """Small strict interpreter for the emitted plist control flow; no UI/radios."""
    outputs={}; stack=[]; effects=[]
    def value(v):
        if isinstance(v,dict) and v.get('WFSerializationType')=='WFTextTokenAttachment':
            attachment=v['Value']
            return supplied if attachment['Type']=='ExtensionInput' else outputs[attachment['OutputUUID']]
        return v
    for row in workflow['WFWorkflowActions']:
        action=row['WFWorkflowActionIdentifier'].removeprefix('is.workflow.actions.')
        p=row['WFWorkflowActionParameters']
        enabled=all(x[1] for x in stack)
        if action=='conditional':
            mode=p['WFControlFlowMode']
            if mode==0:
                found=value(p['WFInput']['Variable']) if enabled else None
                result=bool(found) if p['WFCondition']==100 else found==p['WFConditionalActionString']
                stack.append((p['GroupingIdentifier'],enabled and result,enabled))
            else:
                group,matched,parent=stack.pop();assert group==p['GroupingIdentifier']
                if mode==1:stack.append((group,parent and not matched,parent))
                else:assert mode==2
            continue
        if not enabled:continue
        result=None
        if action=='comment':pass
        elif action=='detect.dictionary':
            raw=value(p['WFInput']);result=json.loads(raw) if isinstance(raw,str) else raw
        elif action=='getvalueforkey':result=value(p['WFInput']).get(p['WFDictionaryKey'])
        elif action=='output':return effects,value(p['WFOutput'])
        elif action=='exit':return effects,None
        elif action=='openurl':effects.append(('open',value(p['WFInput'])))
        elif action=='delay':effects.append(('wait',p['WFDelayTime']))
        elif action=='alert':effects.append(('alert',p['WFAlertActionTitle']))
        elif action in {'wifi.set','cellulardata.set','airplanemode.set'}:
            assert p['Operation']=='Set' and isinstance(p['OnValue'],bool)
            effects.append((action,p['OnValue']))
        else:raise AssertionError('Unreviewed action '+action)
        outputs[p['UUID']]=result
    assert not stack
    return effects,None

def shortcut_checks():
    checks=[]
    for host in ['livecontainer','']:
        workflow=generate(host)
        assert generate(host)==workflow
        effects,_=execute(workflow)
        assert effects==[('open',launch_url(host))];checks.append('home '+(host or 'standalone'))
        for stage in ['prepare','isolate','jit','restore']:
            for wifi in ['on','off']:
                for cellular in ['on','off']:
                    payload=dict(stage=stage,token='fresh',schema=1,wifi=wifi,cellular=cellular,ack='receipt',jitURL='stikdebug://enable-jit?pid=5678&script-data=fresh')
                    effects,output=execute(workflow,json.dumps(payload));assert output=='receipt'
                    expected={'prepare':[('airplanemode.set',False),('cellulardata.set',True),('wifi.set',True)],
                              'isolate':[('airplanemode.set',True),('wifi.set',False)],
                              'jit':[('open',payload['jitURL']),('wait',2)],
                              'restore':[('airplanemode.set',False),('wifi.set',wifi=='on'),('cellulardata.set',cellular=='on')]}[stage]
                    assert effects==expected,(effects,expected);checks.append((host or 'standalone')+' '+stage+' '+wifi+' '+cellular)
        effects,_=execute(workflow,dict(stage='unknown'));assert effects==[('alert','Update the Cabrillo shortcut')]
        checks.append('unknown stage '+(host or 'standalone'))
    return checks

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    work=a.work.absolute();work.mkdir(parents=True,exist_ok=False)
    files=[SOURCE/'tests/ShortcutSessionTests.m',*[SOURCE/'src'/n for n in ['CJShortcutSession.m','CJShortcutPlatform.m','CJPlatformOptions.m']]]
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    command=['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-I'+str(SOURCE/'src'),*[str(f) for f in files],'-framework','Foundation','-o',str(work/'test')]
    subprocess.run(command,env=env,check=True)
    native=subprocess.check_output([work/'test',work/'journals'],text=True)
    branches=shortcut_checks()
    receipt=dict(status='PASS_HOST_SHORTCUT_CONTROLS',native=native.strip(),shortcut_branches=len(branches),checks=branches,
                 physical_device_tested=False,source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files+[Path(__file__),ROOT/'tools/build_shortcut_files.py']})
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(native.strip());print('PASS',len(branches),'generated shortcut branches')

if __name__=='__main__':main()
