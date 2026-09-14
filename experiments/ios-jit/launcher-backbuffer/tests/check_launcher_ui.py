#!/usr/bin/env python3
"""Actual XCUITest interactions with the installed native launcher; no phone/JIT claims."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-backbuffer-ui-tests';O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--device',required=True);a=p.parse_args();env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
def run(cmd):
 r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 with (O/'commands.log').open('a') as f:f.write(repr(cmd)+'\n'+r.stdout)
 if r.returncode:raise RuntimeError(r.stdout[-6000:])
 return r.stdout.strip()
bundle='io.github.hmcneill46.celeste.everest.jit.everest';app=R/'artifacts/ios-jit/launcher-backbuffer-20260912-24-simulator/CelesteJITEverest.app'
subprocess.run(['xcrun','simctl','terminate',a.device,bundle],env=env,capture_output=True)
run(['xcrun','simctl','install',a.device,str(app)])
container=Path(run(['xcrun','simctl','get_app_container',a.device,bundle,'data']))
folder=container/'Documents/LauncherImport';folder.mkdir(parents=True,exist_ok=True)
fixture=R/'.build/ios-jit/launcher-backbuffer-example/CJITLauncherExample-v1.0.0.zip';shutil.copy2(fixture,folder/fixture.name)
old=set((container/'Documents/Diagnostics').glob('*.diagnostics.json'))
prior=R/'.build/ios-jit/picker-ui-tests/Picker.xcodeproj';project=O/'Launcher.xcodeproj';project.mkdir(exist_ok=True)
text=(prior/'project.pbxproj').read_text().replace(str(R/'experiments/ios-jit/content-picker/tests/PickerUITests.swift'),str(S/'tests/LauncherUITests.swift')).replace('Picker','Launcher').replace('celeste.picker.uitests','celeste.launcher.uitests')
(project/'project.pbxproj').write_text(text)
scheme=project/'xcshareddata/xcschemes';scheme.mkdir(parents=True,exist_ok=True)
(scheme/'LauncherUITests.xcscheme').write_text((prior/'xcshareddata/xcschemes/PickerUITests.xcscheme').read_text().replace('Picker','Launcher'))
result=O/'UITests.xcresult'
if result.exists():shutil.rmtree(result)
cmd=['xcodebuild','test','-project',str(project),'-scheme','LauncherUITests','-destination','platform=iOS Simulator,id='+a.device,'-derivedDataPath',str(O/'DerivedData'),'-parallel-testing-enabled','NO','-maximum-concurrent-test-simulator-destinations','1','-resultBundlePath',str(result)]
output=run(cmd);(O/'run.log').write_text(output)
assert 'PASS_NATIVE_CLOSING_SCREEN_PORTRAIT_AND_LANDSCAPE' in output
assert 'PASS_LAUNCHER_PORTRAIT_LANDSCAPE_DEPENDENCY_AND_JIT_GATE' in output and 'PASS_LAUNCHER_REAL_ZIP_PICKER_AND_FRESH_PROCESS_SELECTION' in output
new=set((container/'Documents/Diagnostics').glob('*.diagnostics.json'))-old
assert new
for f in new:shutil.copy2(f,O/f.name)
state=json.loads((container/'Documents/Profiles/sj-first-play/launcher-mod-state.json').read_text());assert state['disabled']==[]
assert (folder/fixture.name).read_bytes()==fixture.read_bytes()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
(O/'receipt.json').write_text(json.dumps(dict(status='PASS_NATIVE_LAUNCHER_XCUITEST',real_picker=True,native_closing_presentation=True,closing_state_is_simulator_fixture=True,portrait_and_landscape_launcher=True,missing_dependency_blocked=True,selection_survives_process_relaunch=True,run_disabled_without_jit=True,original_import_source_preserved=True,source_sha256={str(f.relative_to(R)):sha(f) for f in [Path(__file__),S/'tests/LauncherUITests.swift']},fixture_sha256=sha(fixture),simulator_build_info_sha256=sha(app/'BuildInfo.json'),simulator_executable_sha256=sha(app/'CelesteJITEverest'),physical_game_orientation_tested=False,command=cmd),indent=2)+'\n');print('PASS_NATIVE_LAUNCHER_XCUITEST')
