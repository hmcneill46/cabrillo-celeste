#!/usr/bin/env python3
"""Generate inspectable Shortcuts plists and optionally Apple-signed import files.

No user identifiers, scripts, pairing records or network secrets are embedded.
The native coordinator supplies a fresh stage/return URL for every invocation.
"""
import argparse, base64, copy, hashlib, json, plistlib, subprocess, uuid
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]

def text_token(value):
    """Serialize a magic variable for an Apple text parameter."""
    return dict(WFSerializationType='WFTextTokenString', Value=dict(
        string='\ufffc', attachmentsByRange={'{0, 1}':copy.deepcopy(value['Value'])}))

class Workflow:
    def __init__(self):
        self.actions = []
    def action(self, identifier, **parameters):
        identity = str(uuid.uuid5(uuid.NAMESPACE_URL, 'cabrillo48:'+str(len(self.actions))+':'+identifier)).upper()
        self.actions.append(dict(WFWorkflowActionIdentifier='is.workflow.actions.'+identifier,
                                 WFWorkflowActionParameters=dict(parameters, UUID=identity)))
        return dict(WFSerializationType='WFTextTokenAttachment', Value=dict(Type='ActionOutput', OutputUUID=identity, OutputName=identifier))
    def open_url(self, value):
        # Keep URLs typed throughout the handoff. Converting a long plain string
        # to a URL through Apple's data detector can discard its query value.
        item=text_token(value) if isinstance(value,dict) else value
        url=self.action('url', WFURLActionURL=[item], **{'Show-WFURLActionURL':True})
        # Open URL has its own input parameter; adjacency does not bind it.
        # Use the URL action's typed output directly, without a text token string.
        self.action('openurl', WFInput=url, **{'Show-WFInput':True})
    def condition(self, value, equal=None, mode=0, group=None, comparison=4):
        group = group or str(uuid.uuid5(uuid.NAMESPACE_URL, 'cabrillo48:if:'+str(len(self.actions)))).upper()
        parameters = dict(GroupingIdentifier=group, WFControlFlowMode=mode)
        if mode == 0:
            parameters.update(WFInput=dict(Type='Variable', Variable=value), WFCondition=100 if equal is None else comparison)
            if equal is not None:
                # Dictionary values have a generic content type. Apple If needs
                # an explicit text coercion to expose its string comparison.
                typed = copy.deepcopy(value)
                typed['Value'].setdefault('Aggrandizements', []).append(
                    dict(Type='WFCoercionVariableAggrandizement', CoercionItemClass='WFStringContentItem'))
                parameters['WFInput']['Variable'] = typed
                parameters['WFConditionalActionString'] = equal
        self.action('conditional', **parameters)
        return group
    def end(self, group): self.condition(None, mode=2, group=group)
    def key(self, dictionary, key):
        return self.action('getvalueforkey', WFInput=dictionary, WFDictionaryKey=key, WFGetDictionaryValueType='Value')
    def radio(self, name, enabled): self.action(name+'.set', Operation='Set', OnValue=enabled)
    def plist(self):
        return dict(WFWorkflowName='Cabrillo', WFWorkflowClientVersion='4046.0.3.2',
                    WFWorkflowMinimumClientVersion=900, WFWorkflowMinimumClientVersionString='900',
                    WFWorkflowIcon=dict(WFWorkflowIconStartColor=3980825855, WFWorkflowIconGlyphNumber=59511),
                    WFWorkflowActions=self.actions, WFWorkflowTypes=[], WFQuickActionSurfaces=[],
                    WFWorkflowInputContentItemClasses=['WFStringContentItem'], WFWorkflowOutputContentItemClasses=['WFStringContentItem'],
                    WFWorkflowHasShortcutInputVariables=True, WFWorkflowImportQuestions=[],
                    WFWorkflowHasOutputFallback=False, WFWorkflowNoInputBehavior={'Name':'WFWorkflowNoInputBehaviorContinue'})

def launch_url(host):
    # LiveContainer imports customize only this URL through Apple's setup question.
    # Cabrillo supplies the actual host, guest folder and current data container.
    return 'cabrillo://shortcut-setup-required' if host else 'cabrillo://launch'

def generate(host='livecontainer'):
    w=Workflow()
    w.action('comment', WFCommentActionText='Cabrillo shortcut revision 48 (for app build 48 or later). Keep this shortcut named Cabrillo. Add it to your Home Screen. Networking and recovery choices are in Cabrillo Settings. The JIT stage always uses a fresh process-specific URL from Cabrillo; no saved debugger script is used.')
    source=dict(WFSerializationType='WFTextTokenAttachment', Value=dict(Type='ExtensionInput'))
    outer=w.condition(source)
    dictionary=w.action('detect.dictionary', WFInput=source)
    stage=w.key(dictionary,'stage')
    stages = []
    for name in ['prepare','isolate','jit','restore']:
        group=w.condition(stage,name);stages.append(group)
        if name=='prepare':
            w.radio('airplanemode',False);w.radio('cellulardata',True);w.radio('wifi',True)
        elif name=='isolate':
            w.radio('airplanemode',True);w.radio('wifi',False)
        elif name=='jit':
            w.open_url(w.key(dictionary,'jitURL'))
            # Foreground fallback, not a readiness delay. StikDebug holds its
            # own background lease; Cabrillo verifies real completion later.
            w.action('delay', WFDelayTime=2)
        else:
            w.radio('airplanemode',False)
            for key, radio in [('wifi','wifi'),('cellular','cellulardata')]:
                switch=w.condition(w.key(dictionary,key),'on')
                w.radio(radio,True)
                w.condition(None,mode=1,group=switch);w.radio(radio,False);w.end(switch)
        w.condition(None,mode=1,group=group)
    w.action('alert',WFAlertActionTitle='Update the Cabrillo shortcut',WFAlertActionMessage='This launch stage is not supported. Import the shortcut supplied with your Cabrillo build.',WFAlertActionCancelButtonShown=False)
    w.action('exit')
    for group in reversed(stages):w.end(group)
    w.condition(None,mode=1,group=outer)
    w.open_url(launch_url(host))
    w.end(outer)
    # Native x-success already carries the stage receipt inside its routed URL.
    # Finish naturally without exporting data through Stop and Output, which
    # stalls in the phone's background runner. Clear all intermediate output.
    w.action('nothing')
    result=w.plist()
    if host:
        index=len(w.actions)-4
        assert w.actions[index]['WFWorkflowActionIdentifier']=='is.workflow.actions.url'
        result['WFWorkflowImportQuestions']=[dict(Category='Parameter',ActionIndex=index,
            ParameterKey='WFURLActionURL',Text='Paste the launch link copied by Cabrillo. This selects your app and its data container.')]
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--sign',action='store_true')
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    receipts={}
    for variant,host in [('LiveContainer','livecontainer'),('Standalone','')]:
        directory=args.output/variant;directory.mkdir(exist_ok=True)
        data=generate(host)
        unsigned=directory/'Cabrillo-unsigned.shortcut';unsigned.write_bytes(plistlib.dumps(data,sort_keys=False))
        (directory/'Cabrillo.actions.json').write_text(json.dumps(data,indent=2)+'\n')
        if args.sign:
            signed=directory/'Cabrillo.shortcut'
            subprocess.run(['shortcuts','sign','--mode','anyone','--input',str(unsigned),'--output',str(signed)],check=True)
        receipts[variant]={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(directory.iterdir()) if p.is_file()}
    (args.output/'receipt.json').write_text(json.dumps(dict(schema=1,build=48,app_minimum_build=48,callback_protocol="cabrillo-39",signed=args.sign,files=receipts),indent=2)+'\n')
    (args.output/'manifest.json').write_bytes((args.output/'receipt.json').read_bytes())
    print(json.dumps(dict(status='SIGNED_IMPORT_FILES' if args.sign else 'UNSIGNED_SOURCES',variants=list(receipts)),indent=2))

if __name__=='__main__':main()
