#!/usr/bin/env python3
"""Render the production shortcut controls in a simulator-only fixture."""
import argparse,hashlib,json,os,plistlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-shortcut-setup'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--device',required=True);a=p.parse_args()
    work=ROOT/a.work
    if work.resolve()!=work.absolute() or ROOT/'.build' not in work.parents or work.exists():raise ValueError('Use a fresh .build directory')
    work.mkdir(parents=True);env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    commands=[]
    def run(command,label,timeout=600):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        output=(work/(label+'.log')).read_text()
        if r.returncode:raise RuntimeError(label+' failed: '+output[-4000:])
        return output.strip()
    sdk=run(['xcrun','--sdk','iphonesimulator','--show-sdk-path'],'sdk')
    app=work/'LoadingPreview.app';app.mkdir();bundle='io.github.hmcneill46.cabrillo.shortcuts.preview'
    settings=dict(CFBundleIdentifier=bundle,CFBundleName='LoadingPreview',CFBundleExecutable='LoadingPreview',CFBundlePackageType='APPL',CFBundleVersion='1',CFBundleShortVersionString='1.0',MinimumOSVersion='26.0',UIDeviceFamily=[1,2],LSRequiresIPhoneOS=True,UILaunchScreen={},UIApplicationSceneManifest={'UIApplicationSupportsMultipleScenes':False},UISupportedInterfaceOrientations=['UIInterfaceOrientationPortrait','UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'])
    (app/'Info.plist').write_bytes(plistlib.dumps(settings))
    sources=[SOURCE/'native/ShortcutViews.swift',SOURCE/'tests/ShortcutPreview.swift']
    window_sources=[]
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    inputs=sources+window_sources+[SOURCE/'tests/ShortcutUITests.swift',SOURCE/'tests/LoadingUITests.pbxproj.template',SOURCE/'tests/LoadingUITests.xcscheme',Path(__file__)]
    input_hashes={str(f.relative_to(ROOT)):sha(f) for f in inputs}
    run(['xcrun','swiftc','-swift-version','5','-parse-as-library','-g','-target','x86_64-apple-ios26.0-simulator','-sdk',sdk,*sources,'-o',app/'LoadingPreview'],'preview-build')
    run(['codesign','--force','--sign','-',app],'sign')
    devices=json.loads(run(['xcrun','simctl','list','devices','available','--json'],'devices'))
    selected=[d for group in devices['devices'].values() for d in group if d['udid']==a.device];assert len(selected)==1
    if selected[0]['state']!='Booted':run(['xcrun','simctl','boot',a.device],'boot')
    run(['xcrun','simctl','bootstatus',a.device,'-b'],'boot-status')
    run(['xcrun','simctl','install',a.device,app],'install')
    project=work/'Loading.xcodeproj';project.mkdir()
    (project/'project.pbxproj').write_text((SOURCE/'tests/LoadingUITests.pbxproj.template').read_text().replace('SOURCE_PATH',str(SOURCE/'tests/ShortcutUITests.swift')))
    schemes=project/'xcshareddata/xcschemes';schemes.mkdir(parents=True)
    (schemes/'LoadingUITests.xcscheme').write_bytes((SOURCE/'tests/LoadingUITests.xcscheme').read_bytes())
    result=work/'UITests.xcresult'
    output=run(['xcodebuild','test','-project',project,'-scheme','LoadingUITests','-destination','platform=iOS Simulator,id='+a.device,'-derivedDataPath',work/'DerivedData','-parallel-testing-enabled','NO','-maximum-concurrent-test-simulator-destinations','1','-resultBundlePath',result,'-test-timeouts-enabled','YES','-default-test-execution-time-allowance','120','-maximum-test-execution-time-allowance','180'],'uitests')
    for sentinel in ['PASS_SHORTCUT_PRESET_CONTROLS','PASS_SHORTCUT_ACTIVE_PRESENTATION','PASS_SHORTCUT_RECOVERY_PRESENTATION','PASS_SHORTCUT_DETACH_PRESENTATION','PASS_SHORTCUT_INSTALL_EXPORT_ACTION','PASS_SHORTCUT_HELPER_SETUP_ACTION','PASS_SHORTCUT_SETUP_LAYOUT']:assert sentinel in output,sentinel
    run(['xcrun','xcresulttool','export','attachments','--path',result,'--output-path',work/'screenshots'],'screenshots')
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    inputs=sources+window_sources+[SOURCE/'tests/ShortcutUITests.swift',SOURCE/'tests/LoadingUITests.pbxproj.template',SOURCE/'tests/LoadingUITests.xcscheme',Path(__file__)]
    assert input_hashes=={str(f.relative_to(ROOT)):sha(f) for f in inputs},'UI input changed during compilation/testing'
    receipt=dict(status='PASS_SHORTCUT_PRESENTATION_XCUITEST',device=selected[0],source_sha256={str(f.relative_to(ROOT)):sha(f) for f in inputs},fixture_not_in_device_binary=True,game_or_jit_tested=False,log_sha256=sha(work/'uitests.log'),commands=commands)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
