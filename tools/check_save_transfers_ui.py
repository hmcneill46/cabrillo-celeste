#!/usr/bin/env python3
"""Exercise production profile views and storage in isolated simulator containers."""
import argparse,hashlib,json,os,plistlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'experiments/ios-jit/launcher-save-transfers'
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--device',action='append',required=True);a=p.parse_args()
    work=ROOT/a.work
    assert work.resolve()==work.absolute() and ROOT/'.build' in work.parents and not work.exists()
    work.mkdir(parents=True);native=work/'native';native.mkdir()
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',CLANG_MODULE_CACHE_PATH=str(work/'module-cache'))
    commands=[]
    def run(command,label,timeout=700):
        command=list(map(str,command));commands.append(command)
        with (work/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        output=(work/(label+'.log')).read_text()
        if r.returncode:raise RuntimeError(label+' failed: '+output[-3000:])
        return output.strip()
    sdk=run(['xcrun','--sdk','iphonesimulator','--show-sdk-path'],'sdk');target='x86_64-apple-ios26.0-simulator'
    sources=sorted((SOURCE/'native').glob('*.swift'))+[SOURCE/'tests/ProfilePreview.swift']
    vendor=sorted((ROOT/'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'));yaml=ROOT/'vendor/Yams/Sources/CYaml';c=sorted((yaml/'src').glob('*.c'))
    inputs=sources+vendor+c+[SOURCE/'tests/ProfileUITests.swift',SOURCE/'tests/ProfileUITests.pbxproj.template',SOURCE/'tests/ProfileUITests.xcscheme',Path(__file__)]
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();hashes={str(f.relative_to(ROOT)):sha(f) for f in inputs}
    flags=['-swift-version','5','-g','-target',target,'-sdk',sdk]
    run(['xcrun','swiftc',*flags,'-module-name','ZIPFoundation','-emit-library','-static','-emit-module','-emit-module-path',native/'ZIPFoundation.swiftmodule','-o',native/'libZIPFoundation.a',*vendor],'zip')
    for f in c:run(['xcrun','clang','-target',target,'-isysroot',sdk,'-DYAML_DECLARE_STATIC','-I'+str(yaml/'include'),'-c',f,'-o',native/(f.stem+'.o')],f.stem)
    run(['xcrun','libtool','-static','-o',native/'libCYaml.a',*[native/(f.stem+'.o') for f in c]],'yaml')
    app=work/'ProfilePreview.app';app.mkdir();bundle='io.github.hmcneill46.cabrillo.backups.preview'
    settings=dict(CFBundleIdentifier=bundle,CFBundleName='ProfilePreview',CFBundleExecutable='ProfilePreview',CFBundlePackageType='APPL',CFBundleVersion='1',CFBundleShortVersionString='1.0',MinimumOSVersion='26.0',UIDeviceFamily=[1,2],LSRequiresIPhoneOS=True,UILaunchScreen={},UIApplicationSceneManifest={'UIApplicationSupportsMultipleScenes':False},UISupportedInterfaceOrientations=['UIInterfaceOrientationPortrait','UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'])
    (app/'Info.plist').write_bytes(plistlib.dumps(settings))
    run(['xcrun','swiftc',*flags,'-parse-as-library','-I',native,'-I',yaml/'include',*sources,native/'libZIPFoundation.a',native/'libCYaml.a','-lz','-o',app/'ProfilePreview'],'preview')
    run(['codesign','--force','--sign','-',app],'sign')
    project=work/'Profile.xcodeproj';project.mkdir();schemes=project/'xcshareddata/xcschemes';schemes.mkdir(parents=True)
    (project/'project.pbxproj').write_text((SOURCE/'tests/ProfileUITests.pbxproj.template').read_text().replace('SOURCE_PATH',str(SOURCE/'tests/ProfileUITests.swift')))
    (schemes/'ProfileUITests.xcscheme').write_text((SOURCE/'tests/ProfileUITests.xcscheme').read_text())
    devices=json.loads(run(['xcrun','simctl','list','devices','available','--json'],'devices'))
    results=[]
    for index,udid in enumerate(a.device):
        selected=[d for group in devices['devices'].values() for d in group if d['udid']==udid];assert len(selected)==1
        booted=selected[0]['state']=='Booted'
        try:
            if not booted:run(['xcrun','simctl','boot',udid],f'boot-{index}')
            run(['xcrun','simctl','bootstatus',udid,'-b'],f'bootstatus-{index}')
            run(['xcrun','simctl','install',udid,app],f'install-{index}')
            run(['xcodebuild','-project',project,'-scheme','ProfileUITests','-destination',f'platform=iOS Simulator,id={udid}','-derivedDataPath',work/'Derived','-resultBundlePath',work/f'UI-{index}.xcresult','-parallel-testing-enabled','NO','test'],f'uitests-{index}')
            run(['xcrun','simctl','launch',udid,bundle],f'preview-launch-{index}')
            run(['xcrun','simctl','io',udid,'screenshot',work/f'saves-{index}.png'],f'screenshot-{index}')
            results.append(dict(device=selected[0],status='PASS_PROFILE_UI_XCUITEST',log_sha256=sha(work/f'uitests-{index}.log')))
        finally:
            if not booted:run(['xcrun','simctl','shutdown',udid],f'shutdown-{index}')
    assert hashes=={str(f.relative_to(ROOT)):sha(f) for f in inputs},'Sources changed during check'
    receipt=dict(status='PASS_PROFILE_UI_XCUITEST',devices=results,source_sha256=hashes,commands=commands,fixture_not_in_device_binary=True,phone_game_or_jit_tested=False)
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
