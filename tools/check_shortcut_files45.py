#!/usr/bin/env python3
"""Check revision45 typed URL handoff and Apple conditions/completion.

The Apple host fixture substitutes plain text input for each dictionary-output
reference; it retains the generated comparison parameters and coercion. Only If,
Comment and Nothing actions run in WorkflowKit. A separate ContentKit fixture
compares original text detection with typed URLs built by the native app43 helpers.
This does not execute ActionKit URL/Open URL or physical callbacks.
"""
import argparse
import copy
import hashlib
import json
import os
import plistlib
import subprocess
from pathlib import Path

import build_shortcut_files45 as generator


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/shortcut-files45/AppleWorkflowChecks.m'
URL_SOURCE = ROOT / 'experiments/ios-jit/shortcut-files45/AppleURLChecks.m'
NATIVE = ROOT / 'experiments/ios-jit/launcher-shortcut-guests/src'
generate = generator.generate
launch_url = generator.launch_url

def execute(workflow, supplied=None):
    """Small strict interpreter for the emitted plist control flow; no UI/radios."""
    outputs={}; stack=[]; effects=[]; current=None
    def value(v):
        if isinstance(v,dict) and v.get('WFSerializationType')=='WFTextTokenAttachment':
            attachment=v['Value']
            return supplied if attachment['Type']=='ExtensionInput' else outputs[attachment['OutputUUID']]
        if isinstance(v,dict) and v.get('WFSerializationType')=='WFTextTokenString':
            token=v['Value'];assert token['string']=='\ufffc'
            return value(dict(WFSerializationType='WFTextTokenAttachment',Value=token['attachmentsByRange']['{0, 1}']))
        return v
    for row in workflow['WFWorkflowActions']:
        action=row['WFWorkflowActionIdentifier'].removeprefix('is.workflow.actions.')
        p=row['WFWorkflowActionParameters']
        enabled=all(x[1] for x in stack)
        if action=='conditional':
            mode=p['WFControlFlowMode']
            if mode==0:
                found=value(p['WFInput']['Variable']) if enabled else None
                comparison=p['WFCondition']
                if comparison==100:result=bool(found)
                elif comparison==4:result=found==p['WFConditionalActionString']
                elif comparison==8:result=bool(found and found.startswith(p['WFConditionalActionString']))
                else:raise AssertionError('Unreviewed comparison '+str(comparison))
                stack.append((p['GroupingIdentifier'],enabled and result,enabled))
            else:
                group,matched,parent=stack.pop();assert group==p['GroupingIdentifier']
                if mode==1:stack.append((group,parent and not matched,parent))
                else:assert mode==2
            continue
        if not enabled:continue
        result=None
        if action in {'comment','nothing'}:pass
        elif action=='detect.dictionary':
            raw=value(p['WFInput']);result=json.loads(raw) if isinstance(raw,str) else raw
        elif action=='getvalueforkey':result=value(p['WFInput']).get(p['WFDictionaryKey'])
        elif action=='url':
            assert p['Show-WFURLActionURL'] and len(p['WFURLActionURL'])==1
            result=value(p['WFURLActionURL'][0])
        elif action=='output':return effects,value(p['WFOutput'])
        elif action=='exit':return effects,None
        elif action=='openurl':
            assert 'WFInput' not in p
            effects.append(('open',current))
        elif action=='delay':effects.append(('wait',p['WFDelayTime']))
        elif action=='alert':effects.append(('alert',p['WFAlertActionTitle']))
        elif action in {'wifi.set','cellulardata.set','airplanemode.set'}:
            assert p['Operation']=='Set' and isinstance(p['OnValue'],bool)
            effects.append((action,p['OnValue']))
        else:raise AssertionError('Unreviewed action '+action)
        outputs[p['UUID']]=result;current=result
    assert not stack
    return effects,None

def shortcut_checks():
    checks=[]
    for host in ['livecontainer','']:
        workflow=generate(host)
        assert generate(host)==workflow
        actions=workflow['WFWorkflowActions']
        for i,row in enumerate(actions):
            if row['WFWorkflowActionIdentifier']=='is.workflow.actions.openurl':
                assert i and actions[i-1]['WFWorkflowActionIdentifier']=='is.workflow.actions.url'
                assert 'WFInput' not in row['WFWorkflowActionParameters']
        assert not any(r['WFWorkflowActionIdentifier']=='is.workflow.actions.output' for r in workflow['WFWorkflowActions'])
        assert workflow['WFWorkflowActions'][-1]['WFWorkflowActionIdentifier']=='is.workflow.actions.nothing'
        effects,_=execute(workflow)
        assert effects==[('open',launch_url(host))];checks.append('home '+(host or 'standalone'))
        for stage in ['prepare','isolate','jit','restore']:
            for wifi in ['on','off']:
                for cellular in ['on','off']:
                    payload=dict(stage=stage,token='fresh',schema=1,wifi=wifi,cellular=cellular,ack='receipt',jitURL='stikdebug://enable-jit?pid=5678&script-data=fresh')
                    effects,output=execute(workflow,json.dumps(payload));assert output is None
                    expected={'prepare':[('airplanemode.set',False),('cellulardata.set',True),('wifi.set',True)],
                              'isolate':[('airplanemode.set',True),('wifi.set',False)],
                              'jit':[('open',payload['jitURL']),('wait',2)],
                              'restore':[('airplanemode.set',False),('wifi.set',wifi=='on'),('cellulardata.set',cellular=='on')]}[stage]
                    assert effects==expected,(effects,expected);checks.append((host or 'standalone')+' '+stage+' '+wifi+' '+cellular)
        effects,_=execute(workflow,dict(stage='unknown'));assert effects==[('alert','Update the Cabrillo shortcut')]
        checks.append('unknown stage '+(host or 'standalone'))
    return checks



def apple_cases():
    cases = []
    for host in ('livecontainer', ''):
        for i, row in enumerate(generator.generate(host)['WFWorkflowActions']):
            p = row['WFWorkflowActionParameters']
            if row['WFWorkflowActionIdentifier'] != 'is.workflow.actions.conditional' or 'WFConditionalActionString' not in p:
                continue
            target = p['WFConditionalActionString']
            assert p['WFInput']['Variable']['Value']['Aggrandizements'] == [
                dict(Type='WFCoercionVariableAggrandizement', CoercionItemClass='WFStringContentItem')]
            matching=target+'bundle-name=Stik.app&open-url=CONTROL' if p['WFCondition']==8 else target
            for variant, supplied, expected in [('match', matching, 'MATCH'), ('other', 'not-'+target, 'OTHER'), ('original', matching, None)]:
                condition = copy.deepcopy(row)
                value = condition['WFWorkflowActionParameters']['WFInput']['Variable']['Value']
                value.pop('OutputUUID');value.pop('OutputName');value['Type'] = 'ExtensionInput'
                if variant == 'original':value.pop('Aggrandizements')
                group = p['GroupingIdentifier']
                def action(name, **params):
                    return dict(WFWorkflowActionIdentifier='is.workflow.actions.'+name, WFWorkflowActionParameters=params)
                actions = [condition, action('comment', WFCommentActionText='MATCH'),
                    action('conditional', GroupingIdentifier=group, WFControlFlowMode=1),
                    action('comment', WFCommentActionText='OTHER'),
                    action('conditional', GroupingIdentifier=group, WFControlFlowMode=2)]
                cases.append(dict(name=f'{host or "standalone"}-{i}-{variant}', actions=actions,
                    input=supplied, comments=[expected] if expected else [], truth=variant=='match', expectMissingParameter=variant=='original'))
    cases.append(dict(name='natural-completion-clears-output',input='CONTROL_INPUT',output=[],actions=[dict(
        WFWorkflowActionIdentifier='is.workflow.actions.nothing',WFWorkflowActionParameters={})]))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args();work = args.work.absolute();work.mkdir(parents=True, exist_ok=False)
    interpreted = shortcut_checks()
    cases = apple_cases();(work/'cases.plist').write_bytes(plistlib.dumps(cases))
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    subprocess.run(['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations',
        '-framework','Foundation',str(SOURCE),'-o',str(work/'apple-checks')], env=env, check=True)
    result = subprocess.run([str(work/'apple-checks'),str(work/'cases.plist')], capture_output=True, text=True)
    (work/'apple-results.json').write_text(result.stdout);(work/'apple-stderr.txt').write_text(result.stderr)
    result.check_returncode();apple = json.loads(result.stdout)
    assert apple['status'] == 'PASS_APPLE_WORKFLOW_CONTROLS' and apple['checks'] == 37
    dependencies=[NATIVE/(name+suffix) for name in ['CJPlatformOptions','CJShortcutPlatform','CJShortcutSession'] for suffix in ['.m','.h']]
    subprocess.run(['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations',
        '-framework','Foundation','-I',str(NATIVE),str(URL_SOURCE),
        *[str(p) for p in dependencies if p.suffix=='.m'],'-o',str(work/'url-checks')],env=env,check=True)
    result=subprocess.run([str(work/'url-checks')],capture_output=True,text=True)
    (work/'url-results.json').write_text(result.stdout);(work/'url-stderr.txt').write_text(result.stderr)
    result.check_returncode();url=json.loads(result.stdout)
    assert url['status']=='PASS_APPLE_URL_CONTENT_CONTROLS' and url['checks']==18 and url['original_truncation_controls']==4
    files = [Path(__file__),ROOT/'tools/build_shortcut_files45.py',SOURCE,URL_SOURCE,ROOT/'experiments/ios-jit/shortcut-files45/BuildInfo.json',*dependencies]
    receipt = dict(status='PASS_SHORTCUT45_HOST_CONTROLS',apple_condition_checks=36,apple_completion_checks=1,
        apple_url_content_checks=url['checks'],original_url_truncation_controls=url['original_truncation_controls'],
        expected_original_failures=sum(c.get('expectMissingParameter',False) for c in cases),
        generated_branches=len(interpreted),physical_device_tested=False,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':main()
