#!/usr/bin/env python3
"""Exercise production helper IPC on a new, disposable iOS simulator.

The actual coordinator, helper entry and helper Swift implementation are compiled.
A fixture host overrides only preflightError; StikJIT is replaced by a no-JIT
stub. Prepare returns synthetic readiness. No real pairing, network, DDI, game,
device signing or JIT is used. This does not establish physical-device support.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-integrated-jit'
BASE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
BUNDLE = 'io.github.hmcneill46.celeste.everest.jit.everest'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/integrated57-ipc')
    parser.add_argument('--developer-dir', default=os.environ.get('DEVELOPER_DIR', '/Applications/Xcode.app/Contents/Developer'))
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if ROOT / '.build' not in work.parents or work.resolve() != work or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    env = dict(os.environ, DEVELOPER_DIR=args.developer_dir)
    if subprocess.check_output(['xcodebuild', '-version'], env=env, text=True).strip() != 'Xcode 26.6\nBuild version 17F113':
        raise ValueError('Xcode26.6 /17F113 is required')
    if subprocess.check_output(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-version'], env=env, text=True).strip() != '26.5':
        raise ValueError('iOS Simulator SDK26.5 is required')
    arch = platform.machine()
    if arch not in {'x86_64', 'arm64'}:
        raise ValueError('Unsupported simulator architecture')
    sdk = subprocess.check_output(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path'], env=env, text=True).strip()
    target = arch + '-apple-ios26.5-simulator'
    env['SDKROOT'] = sdk
    production = [LANE/'src/CJIntegratedJITCoordinator.h', LANE/'src/CJIntegratedJITCoordinator.m',
                  LANE/'helper/CabrilloJITHelper.swift', LANE/'helper/main.m', LANE/'helper/Info.plist',
                  BASE/'src/CJShortcutPlatform.h', BASE/'src/CJShortcutPlatform.m']
    fixtures = [LANE/'tests/IntegratedJITIPCStub.swift', LANE/'tests/IntegratedJITIPCHost.m']
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in [*production, *fixtures, Path(__file__).resolve()]}
    work.mkdir(parents=True)
    app = work/'IPCFixture.app'; framework = app/'Frameworks/StikJIT.framework'; helper = app/'PlugIns/CabrilloJITHelper.appex'
    framework.mkdir(parents=True); helper.mkdir(parents=True)
    commands = []

    def run(command, label, timeout=90):
        command = list(map(str, command)); commands.append(command)
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=timeout)
        (work/(label+'.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(label + ' failed; inspect its log in ' + str(work))
        return result.stdout.strip()

    module = framework/('Modules/StikJIT.swiftmodule/'+arch+'-apple-ios-simulator.swiftmodule')
    run(['xcrun','swiftc','-target',target,'-sdk',sdk,'-module-name','StikJIT','-emit-library','-emit-module',
         '-emit-module-path',module,'-Xlinker','-install_name','-Xlinker','@rpath/StikJIT.framework/StikJIT',
         '-o',framework/'StikJIT',fixtures[0]], 'compile-stub')
    for source, name in [(LANE/'helper/main.m','helper-main'),(LANE/'src/CJIntegratedJITCoordinator.m','coordinator'),
                         (BASE/'src/CJShortcutPlatform.m','platform'),(fixtures[1],'host')]:
        run(['xcrun','clang','-target',target,'-isysroot',sdk,'-fobjc-arc','-O0','-g','-Wall','-Wextra','-Werror',
             '-Wno-deprecated-declarations','-I'+str(LANE/'src'),'-I'+str(BASE/'src'),'-c',source,'-o',work/(name+'.o')], 'compile-'+name)
    run(['xcrun','swiftc','-target',target,'-sdk',sdk,'-parse-as-library','-module-name','CabrilloJITHelper',
         '-F',app/'Frameworks','-framework','StikJIT','-framework','Foundation',work/'helper-main.o',
         '-Xlinker','-rpath','-Xlinker','@executable_path/../../Frameworks','-o',helper/'CabrilloJITHelper',
         LANE/'helper/CabrilloJITHelper.swift'], 'link-helper')
    run(['xcrun','clang','-target',target,'-isysroot',sdk,work/'host.o',work/'coordinator.o',work/'platform.o',
         '-framework','Foundation','-framework','UIKit','-framework','Security','-o',app/'IPCFixture'], 'link-host')
    helper_info = plistlib.loads((LANE/'helper/Info.plist').read_bytes())
    helper_info['CFBundleSupportedPlatforms'] = ['iPhoneSimulator']
    (helper/'Info.plist').write_bytes(plistlib.dumps(helper_info))
    (framework/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier='com.stik.StikJIT', CFBundleExecutable='StikJIT',
        CFBundlePackageType='FMWK', CFBundleVersion='1', CFBundleShortVersionString='1.0', MinimumOSVersion='17.4')))
    (app/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier=BUNDLE,CFBundleExecutable='IPCFixture',
        CFBundleName='IPCFixture',CFBundlePackageType='APPL',CFBundleVersion='57',CFBundleShortVersionString='0.26.0',
        MinimumOSVersion='26.5',CFBundleSupportedPlatforms=['iPhoneSimulator'],UILaunchScreen={},UIDeviceFamily=[1,2])))
    for path in [framework, helper, app]:
        run(['codesign','--force','--sign','-',path], 'sign-'+path.name)
    simulator = None
    try:
        simulator = run(['xcrun','simctl','create','Cabrillo57-IPC-'+work.name,
            'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro','com.apple.CoreSimulator.SimRuntime.iOS-26-5'], 'create-simulator')
        run(['xcrun','simctl','boot',simulator], 'boot-simulator')
        run(['xcrun','simctl','bootstatus',simulator,'-b'], 'wait-for-boot', timeout=180)
        run(['xcrun','simctl','install',simulator,app], 'install-fixture')
        run(['xcrun','simctl','launch',simulator,BUNDLE], 'launch-fixture')
        host = Path(run(['xcrun','simctl','get_app_container',simulator,BUNDLE,'data'], 'host-container'))
        result = None; deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            path = host/'Documents/ipc-result.json'
            if path.exists():
                candidate = json.loads(path.read_text())
                if candidate['status'] in {'PASS_AUTHORITATIVE_PREPARE_RESPONSE','FAIL_EXTENSION_PATH','FAIL_SYNTHETIC_PAIRING'}:
                    result = candidate; break
            time.sleep(.25)
        if result is None or result['status'] != 'PASS_AUTHORITATIVE_PREPARE_RESPONSE':
            (work/'host-result.json').write_text(json.dumps(result,indent=2)+'\n')
            raise RuntimeError('Simulator helper did not complete prepare; inspect host-result.json')
        device = Path.home()/'Library/Developer/CoreSimulator/Devices'/simulator/'data'
        containers = []
        for path in (device/'Containers/Data/PluginKitPlugin').glob('*'):
            metadata = path/'.com.apple.mobile_container_manager.metadata.plist'
            if metadata.exists() and plistlib.loads(metadata.read_bytes()).get('MCMMetadataIdentifier') == BUNDLE+'.JITHelper':
                containers.append(path)
        if len(containers) != 1:
            raise RuntimeError('Expected exactly one helper data container on the new simulator')
        helper_record = json.loads((containers[0]/'Library/fixture-no-jit.json').read_text())
        if helper_record['helper_pid'] == result['host_pid'] or helper_record['jit_attempted'] is not False:
            raise RuntimeError('Helper process separation or no-JIT assertion failed')
        if list((containers[0]/'Library/StikJIT').glob('session-*.plist')):
            raise RuntimeError('Helper did not remove its temporary synthetic pairing file')
        messages = [e['message'] for e in result['events']]
        if not all(any(stage in message for message in messages) for stage in
                   ['Remote Pairing endpoint','Checking the Developer Disk Image','Developer Disk Image ready']):
            raise RuntimeError('Expected all three actual Darwin progress stages')
        if any(sha(ROOT/name) != digest for name,digest in inputs.items()):
            raise RuntimeError('A production or fixture input changed during the check')
        (work/'host-result.json').write_text(json.dumps(result,indent=2)+'\n')
        (work/'helper-result.json').write_text(json.dumps(helper_record,indent=2)+'\n')
        receipt = dict(status='PASS_PRODUCTION_COORDINATOR_SIMULATOR_HELPER_IPC',
            created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_sha256=inputs,
            target=target, simulator_runtime='iOS26.5', host_pid=result['host_pid'],helper_pid=helper_record['helper_pid'],
            commands=commands, authoritative_prepare_reply=True, darwin_progress_stages=3,
            protected_helper_temporary_pairing_removed=True, synthetic_pairing_only=True,
            fixture_preflight_override_only=True, stikjit_stub=True, real_ddi_preparation=False,
            jit_attempted=False,physical_device_tested=False,
            helper_fixture_plist_change='CFBundleSupportedPlatforms=iPhoneSimulator')
        (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(receipt['status'])
    finally:
        if simulator:
            run(['xcrun','simctl','shutdown',simulator], 'shutdown-own-simulator')
            run(['xcrun','simctl','delete',simulator], 'delete-own-simulator')


if __name__ == '__main__':
    main()
