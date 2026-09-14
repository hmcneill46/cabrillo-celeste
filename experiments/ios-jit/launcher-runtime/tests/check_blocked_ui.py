#!/usr/bin/env python3
"""External simulator fixtures for blocked actions and a real fresh map review."""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit';O=B/'launcher-runtime-blocked-ui';O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--device',required=True);args=p.parse_args()
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer');bundle='io.github.hmcneill46.celeste.everest.jit.everest'
def run(cmd):
 x=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 with (O/'commands.log').open('a') as f:f.write(repr(cmd)+'\n'+x.stdout)
 if x.returncode:raise RuntimeError(x.stdout[-6000:])
 return x.stdout.strip()
def stop():subprocess.run(['xcrun','simctl','terminate',args.device,bundle],env=env,capture_output=True)
stop();container=Path(run(['xcrun','simctl','get_app_container',args.device,bundle,'data']))
fixtures=container/'Documents/InstallerFixtures';catalogue=fixtures/'candidates.json';original=catalogue.read_bytes()
profile=container/'Documents/LauncherInstallUITestProfile';preserved=container/'Documents/LauncherInstallUITestProfile-before-blocked'
assert not preserved.exists()
if profile.exists():profile.rename(preserved)
data=json.loads(original);data['helper-new']['modules'][0]['dependencies']=[dict(name='Everest',version='1.9999.0')]
catalogue.write_text(json.dumps(data))
standard=B/'launcher-runtime-ui-tests';project=standard/'Launcher.xcodeproj'
def case(name,label):
 result=O/(label+'.xcresult');assert not result.exists()
 cmd=['xcodebuild','test','-project',str(project),'-scheme','LauncherUITests','-destination','platform=iOS Simulator,id='+args.device,'-derivedDataPath',str(O/'DerivedData'),'-parallel-testing-enabled','NO','-resultBundlePath',str(result),'-only-testing:LauncherUITests/LauncherUITests/'+name]
 output=run(cmd);(O/(label+'.log')).write_text(output);return output
try:
 output=case('testBlockedUpdateAndInstallationReview','Blocked')
 assert 'PASS_NATIVE_BLOCKED_UPDATES_AND_REVIEW' in output
 assert sorted(p.name for p in (profile/'Mods').glob('*.zip'))==['CJITCodeCanary-v1.0.0.zip','helper-old.zip','root.zip']
 assert (profile/'Mods/CJITCodeCanary-v1.0.0.zip').read_bytes()==(B/'sj-lobby-mods/CJITCodeCanary-v1.0.0.zip').read_bytes()
 assert not list((profile/'LauncherInstalls').glob('*.json'))
finally:
 stop();catalogue.write_bytes(original)
 if profile.exists():profile.rename(container/'Documents/LauncherInstallUITestProfile-blocked-result')
 if preserved.exists():preserved.rename(profile)
live=container/'Documents/Profiles/sj-first-play';saved=live.with_name('sj-first-play-before-spring-review')
assert not saved.exists()
if live.exists():live.rename(saved)
(live/'Mods').mkdir(parents=True)
shutil.copy2(B/'launcher-runtime-service/SpringCollab2020.zip',live/'Mods/SpringCollab2020.zip')
try:
 output=case('testFreshSpringReviewUsesCurrentReleases','FreshSpring')
 assert 'PASS_NATIVE_FRESH_SPRING_CURRENT_RELEASE_REVIEW' in output
 assert not list((live/'LauncherInstalls').glob('*.json'))
 # The native app may also install its own tiny required canary.
 assert all(p.name in ['SpringCollab2020.zip','CJITCodeCanary-v1.0.0.zip'] for p in (live/'Mods').glob('*.zip'))
finally:
 stop()
 if live.exists():live.rename(live.with_name('spring-review-result'))
 if saved.exists():saved.rename(live)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
app=R/'artifacts/ios-jit/launcher-runtime-20260913-27-simulator/CelesteJITEverest.app'
receipt=dict(status='PASS_NATIVE_BLOCKED_AND_FRESH_SPRING_UI',blocked_update_has_no_action=True,blocked_review_has_no_apply=True,zero_mod_downloads_or_transactions=True,actual_original_map_and_live_index_review=True,current_releases_selected=True,source_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),S/'tests/LauncherUITests.swift']},simulator_executable_sha256=sha(app/'CelesteJITEverest'),simulator_build_info_sha256=sha(app/'BuildInfo.json'),physical_execution=False)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
