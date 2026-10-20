#!/usr/bin/env python3
"""Exercise actual build57 launcher views in synthetic iPhone/iPad simulator containers.

Compiles the selected production Swift and public ZIP/YAML sources. No native
coordinator, helper, game, pairing data, network service or JIT is executed.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
OVERLAY = ROOT / 'experiments/ios-jit/launcher-integrated-jit'
XCODE = '/Applications/Xcode.app/Contents/Developer'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    parser.add_argument('--device', action='append', required=True)
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Use a fresh, unaliased ignored .build output directory')
    if len(set(args.device)) != len(args.device):
        raise ValueError('Do not repeat a simulator identifier')
    work.mkdir(parents=True)
    env = dict(os.environ, DEVELOPER_DIR=XCODE, CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'))
    commands = []

    def run(command, label, timeout=1200):
        command = list(map(str, command)); commands.append(command)
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        output = (work / (label + '.log')).read_text()
        if result.returncode:
            raise RuntimeError(label + ' failed: ' + output[-5000:])
        return output.strip()

    sys.path.insert(0, str(ROOT / 'tools'))
    from compile_release57 import selected_swift_sources
    sources = selected_swift_sources()
    if OVERLAY / 'native/LauncherUI.swift' not in sources or OVERLAY / 'native/IntegratedJITViews.swift' not in sources or SOURCE / 'native/LauncherUI.swift' in sources:
        raise ValueError('The fixture must use the actual selected build57 UI overlay')
    vendor = sorted((ROOT / 'vendor/ZIPFoundation/Sources/ZIPFoundation').glob('*.swift'))
    yaml = ROOT / 'vendor/Yams/Sources/CYaml'
    c = sorted((yaml / 'src').glob('*.c'))
    fixture = OVERLAY / 'tests/IntegratedJITPreview.swift'
    tests = OVERLAY / 'tests/IntegratedJITUITests.swift'
    template = SOURCE / 'tests/LoadingUITests.pbxproj.template'
    scheme = SOURCE / 'tests/LoadingUITests.xcscheme'
    inputs = sources + vendor + c + [fixture, tests, template, scheme, Path(__file__)]
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    (work / 'source-initial.json').write_text(json.dumps(hashes, indent=2) + '\n')
    native = work / 'native'; native.mkdir()
    sdk = run(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path'], 'sdk')
    architecture = platform.machine()
    if architecture not in {'x86_64', 'arm64'}:
        raise ValueError('Unsupported simulator host architecture')
    target = architecture + '-apple-ios26.0-simulator'
    flags = ['-swift-version', '5', '-g', '-target', target, '-sdk', sdk]
    run(['xcrun', 'swiftc', *flags, '-module-name', 'ZIPFoundation', '-emit-library', '-static', '-emit-module', '-emit-module-path', native / 'ZIPFoundation.swiftmodule', '-o', native / 'libZIPFoundation.a', *vendor], 'compile-zip')
    for source in c:
        run(['xcrun', 'clang', '-target', target, '-isysroot', sdk, '-DYAML_DECLARE_STATIC', '-I' + str(yaml / 'include'), '-c', source, '-o', native / (source.stem + '.o')], 'compile-yaml-' + source.stem)
    run(['xcrun', 'libtool', '-static', '-o', native / 'libCYaml.a', *[native / (source.stem + '.o') for source in c]], 'archive-yaml')
    app = work / 'IntegratedJITPreview.app'; app.mkdir()
    bundle = 'io.github.hmcneill46.cabrillo.integrated57.preview'
    settings = dict(CFBundleIdentifier=bundle, CFBundleName='IntegratedJITPreview', CFBundleExecutable='IntegratedJITPreview', CFBundlePackageType='APPL', CFBundleVersion='1', CFBundleShortVersionString='1.0', MinimumOSVersion='26.0', UIDeviceFamily=[1, 2], LSRequiresIPhoneOS=True, UILaunchScreen={}, UIApplicationSceneManifest={'UIApplicationSupportsMultipleScenes':False}, UISupportedInterfaceOrientations=['UIInterfaceOrientationPortrait', 'UIInterfaceOrientationLandscapeLeft', 'UIInterfaceOrientationLandscapeRight'])
    (app / 'Info.plist').write_bytes(plistlib.dumps(settings))
    run(['xcrun', 'swiftc', *flags, '-parse-as-library', '-I', native, '-I', yaml / 'include', *sources, fixture, native / 'libZIPFoundation.a', native / 'libCYaml.a', '-lz', '-o', app / 'IntegratedJITPreview'], 'compile-preview')
    run(['codesign', '--force', '--sign', '-', app], 'sign')
    project = work / 'Loading.xcodeproj'; project.mkdir()
    (project / 'project.pbxproj').write_text(template.read_text().replace('SOURCE_PATH', str(tests)))
    schemes = project / 'xcshareddata/xcschemes'; schemes.mkdir(parents=True)
    (schemes / 'LoadingUITests.xcscheme').write_bytes(scheme.read_bytes())
    devices = json.loads(run(['xcrun', 'simctl', 'list', 'devices', 'available', '--json'], 'devices'))
    results = []
    sentinels = ['PASS_RUN_BUTTON_PRODUCTION_STATES', 'PASS_RUN_BUTTON_LARGE_TYPE_LANDSCAPE_FORCED_DARK',
                 'PASS_RUN_BUTTON_ACTUAL_HELD_PRESS', 'PASS_INTEGRATED_SERVICE_DDI_AND_JIT_DISTINCTION',
                 'PASS_INTEGRATED_SETTINGS_ACTIONS_AND_RESTART_LOCK', 'PASS_INTEGRATED_LARGE_TYPE_PROGRESS_AND_RUN_LABEL',
                 'PASS_LEGACY_JIT_PROVIDER_CONTROLS_RETAINED']
    for index, device_id in enumerate(args.device):
        selected = [d for group in devices['devices'].values() for d in group if d['udid'] == device_id]
        if len(selected) != 1:
            raise ValueError('Expected exactly one available simulator for ' + device_id)
        selected = selected[0]
        was_booted = selected['state'] == 'Booted'
        log_path = work / ('uitests-' + str(index) + '.log')
        stop = threading.Event()
        captures = []

        def held_capture():
            while not stop.wait(0.1):
                if not log_path.exists() or 'PRESS_SCREENSHOT_BEGIN' not in log_path.read_text():
                    continue
                time.sleep(1.5)
                path = work / ('pressed-' + str(index) + '.png')
                command = ['xcrun', 'simctl', 'io', device_id, 'screenshot', str(path)]
                outcome = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
                before_release = 'PRESS_SCREENSHOT_END' not in log_path.read_text()
                captures.append(dict(command=command, returncode=outcome.returncode, output=outcome.stdout.decode(errors='replace'), before_release_marker=before_release, path=path.name, sha256=sha(path) if path.exists() else None))
                return

        watcher = threading.Thread(target=held_capture, daemon=True)
        try:
            if not was_booted: run(['xcrun', 'simctl', 'boot', device_id], 'boot-' + str(index))
            run(['xcrun', 'simctl', 'bootstatus', device_id, '-b'], 'bootstatus-' + str(index))
            run(['xcrun', 'simctl', 'install', device_id, app], 'install-' + str(index))
            watcher.start()
            result_path = work / ('UI-' + str(index) + '.xcresult')
            output = run(['xcodebuild', 'test', '-project', project, '-scheme', 'LoadingUITests', '-destination', 'platform=iOS Simulator,id=' + device_id, '-derivedDataPath', work / 'DerivedData', '-parallel-testing-enabled', 'NO', '-maximum-concurrent-test-simulator-destinations', '1', '-resultBundlePath', result_path, '-test-timeouts-enabled', 'YES', '-default-test-execution-time-allowance', '300', '-maximum-test-execution-time-allowance', '360'], 'uitests-' + str(index))
            for sentinel in sentinels:
                if sentinel not in output: raise ValueError('Missing actual UI sentinel: ' + sentinel)
            run(['xcrun', 'xcresulttool', 'export', 'attachments', '--path', result_path, '--output-path', work / ('screenshots-' + str(index))], 'screenshots-' + str(index))
            stop.set(); watcher.join(timeout=35)
            if len(captures) != 1 or captures[0]['returncode'] != 0 or not captures[0]['before_release_marker']:
                raise ValueError('Actual pressed screenshot was not captured during the held gesture')
            results.append(dict(device=selected, log_sha256=sha(log_path), sentinels=sentinels, pressed=captures, simulator_shutdown=not was_booted))
        finally:
            stop.set()
            if watcher.is_alive(): watcher.join(timeout=35)
            if not was_booted: run(['xcrun', 'simctl', 'shutdown', device_id], 'shutdown-' + str(index))
    if hashes != {str(path.relative_to(ROOT)): sha(path) for path in inputs}:
        raise RuntimeError('Selected production Swift or fixture changed during presentation validation')
    receipt = dict(status='PASS_BUILD57_PRODUCTION_SWIFTUI_PRESENTATION', verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), devices=results, compiled_production_swift_sources=len(sources), compiled_test_sources=1, target=target, source_sha256=hashes, screenshots={str(path.relative_to(work)):sha(path) for path in sorted(work.rglob('*.png'))}, commands=commands, simulator_fixture_not_in_device_binary=True, native_coordinator_executed=False, helper_executed=False, network_service_or_pairing_tested=False, game_or_jit_tested=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(status=receipt['status'], receipt=str((work / 'receipt.json').relative_to(ROOT)), receipt_sha256=sha(work / 'receipt.json')), indent=2))


if __name__ == '__main__':
    main()
