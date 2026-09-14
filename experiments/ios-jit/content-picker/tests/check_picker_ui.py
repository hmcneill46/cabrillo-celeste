#!/usr/bin/env python3
"""Exercise actual UIKit document selection and folder fallback in a booted simulator."""
import argparse,hashlib,json,os,plistlib,shutil,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',required=True);args=p.parse_args()
OUT=ROOT/'.build/ios-jit/picker-ui-tests';OUT.mkdir(parents=True,exist_ok=True)
PROJECT=OUT/'Picker.xcodeproj';PROJECT.mkdir(exist_ok=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
def run(cmd):
    r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    with (OUT/'commands.log').open('a') as f:f.write(repr(cmd)+'\n'+r.stdout)
    if r.returncode:raise RuntimeError(r.stdout[-12000:])
    return r.stdout.strip()
app=ROOT/'artifacts/ios-jit/content-picker-20260911-15-simulator/CelesteJITEverest.app';bundle='io.github.hmcneill46.celeste.everest.jit.everest'
subprocess.run(['xcrun','simctl','terminate',args.device,bundle],env=env,capture_output=True)
run(['xcrun','simctl','install',args.device,str(app)])
container=Path(run(['xcrun','simctl','get_app_container',args.device,bundle,'data']))
fixture=OUT/'celeste-picker-fixture.zip'
with zipfile.ZipFile(fixture,'w',zipfile.ZIP_STORED) as z:z.writestr('fixture.bin',bytes(range(256))*16384)
for folder in ['PickerFixture','GameImport']:
    dest=container/'Documents'/folder;dest.mkdir(parents=True,exist_ok=True);shutil.copy2(fixture,dest/fixture.name)
old=set((container/'Documents/Diagnostics').glob('*.diagnostics.json'))
# A UI-test-only project launches the already installed app by its bundle ID.
(PROJECT/'project.pbxproj').write_text('''// !$*UTF8*$!
{
archiveVersion = 1; classes = {}; objectVersion = 56;
objects = {
A00000000000000000000001 = {isa = PBXProject; buildConfigurationList = A00000000000000000000002; compatibilityVersion = "Xcode 14.0"; mainGroup = A00000000000000000000003; productRefGroup = A00000000000000000000004; projectDirPath = ""; projectRoot = ""; targets = (A00000000000000000000005); };
A00000000000000000000002 = {isa = XCConfigurationList; buildConfigurations = (A00000000000000000000006); defaultConfigurationIsVisible = 0; defaultConfigurationName = Debug; };
A00000000000000000000003 = {isa = PBXGroup; children = (A00000000000000000000009,A00000000000000000000004); sourceTree = "<group>"; };
A00000000000000000000004 = {isa = PBXGroup; children = (A0000000000000000000000A); name = Products; sourceTree = "<group>"; };
A00000000000000000000005 = {isa = PBXNativeTarget; buildConfigurationList = A00000000000000000000007; buildPhases = (A0000000000000000000000B); buildRules = (); dependencies = (); name = PickerUITests; productName = PickerUITests; productReference = A0000000000000000000000A; productType = "com.apple.product-type.bundle.ui-testing"; };
A00000000000000000000006 = {isa = XCBuildConfiguration; buildSettings = {SDKROOT = iphonesimulator; IPHONEOS_DEPLOYMENT_TARGET = 26.0; }; name = Debug; };
A00000000000000000000007 = {isa = XCConfigurationList; buildConfigurations = (A00000000000000000000008); defaultConfigurationIsVisible = 0; defaultConfigurationName = Debug; };
A00000000000000000000008 = {isa = XCBuildConfiguration; buildSettings = {PRODUCT_NAME = "$(TARGET_NAME)"; PRODUCT_BUNDLE_IDENTIFIER = "io.github.hmcneill46.celeste.picker.uitests"; SWIFT_VERSION = 5.0; GENERATE_INFOPLIST_FILE = YES; CODE_SIGNING_ALLOWED = NO; TARGETED_DEVICE_FAMILY = 1; }; name = Debug; };
A00000000000000000000009 = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = "SOURCE_PATH"; sourceTree = "<absolute>"; };
A0000000000000000000000A = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; path = PickerUITests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };
A0000000000000000000000B = {isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (A0000000000000000000000C); runOnlyForDeploymentPostprocessing = 0; };
A0000000000000000000000C = {isa = PBXBuildFile; fileRef = A00000000000000000000009; };
}; rootObject = A00000000000000000000001;
}
'''.replace('SOURCE_PATH',str(SOURCE/'tests/PickerUITests.swift')))
scheme=PROJECT/'xcshareddata/xcschemes';scheme.mkdir(parents=True,exist_ok=True)
(scheme/'PickerUITests.xcscheme').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="2660" version="1.3">
<BuildAction parallelizeBuildables="NO" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="NO" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="NO"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="PickerUITests.xctest" BlueprintName="PickerUITests" ReferencedContainer="container:Picker.xcodeproj"/></BuildActionEntry></BuildActionEntries></BuildAction>
<TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="PickerUITests.xctest" BlueprintName="PickerUITests" ReferencedContainer="container:Picker.xcodeproj"/></TestableReference></Testables></TestAction>
</Scheme>''')
cmd=['xcodebuild','test','-project',str(PROJECT),'-scheme','PickerUITests','-destination','platform=iOS Simulator,id='+args.device,'-derivedDataPath',str(OUT/'DerivedData'),'-parallel-testing-enabled','NO','-maximum-concurrent-test-simulator-destinations','1']
output=run(cmd);(OUT/'run.log').write_text(output)
new=set((container/'Documents/Diagnostics').glob('*.diagnostics.json'))-old
records=[]
for path in new:
    j=json.loads(path.read_text());events=j['current_events'];names=[e['event'] for e in events]
    assert any(e['event']=='host_ui_content_stage_check' and e['fields']['staged'] and e['fields']['run_disabled_without_jit'] for e in events)
    if 'document_picker_did_pick' in names:
        selected=[e['fields'] for e in events if e['event']=='document_picker_did_pick'];assert len(selected)==1 and selected[0]['kind']=='content' and selected[0]['count']==1 and selected[0]['actual_mode']==0
        configuration=next(e['fields'] for e in events if e['event']=='content_picker_configured');assert configuration['requested_as_copy'] and configuration['actual_mode']==0
    elif 'content_folder_import_checked' in names:assert any(e['event']=='content_folder_import_checked' and e['fields']['archive_count']==1 for e in events)
    else:raise AssertionError('No real picker or fallback callback')
    shutil.copy2(path,OUT/path.name);records.append({'session':j['session'],'events':names})
assert len(records)==2,records
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(container/'Documents/ContentImport/game-input.zip')==sha(fixture)
assert all(sha(container/'Documents'/folder/fixture.name)==sha(fixture) for folder in ['PickerFixture','GameImport'])
result=dict(status='PASS_REAL_SIMULATOR_DOCUMENT_PICKER_AND_FOLDER_BUTTON',device=args.device,fixture_bytes=fixture.stat().st_size,fixture_sha256=sha(fixture),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [SOURCE/'tests/PickerUITests.swift',Path(__file__).resolve()]},sessions=records,host_test_command=cmd,physical_livecontainer_tested=False)
(OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
