#!/usr/bin/env python3
"""Reproduce58's missed controller replay and test the actual59 lifecycle source.

The engine, SDL and hook boundaries are controlled. Optional --adapter inspects
the actual compiled public adapter with Cecil; it never loads the target DLL.
No game, native controller backend, private input or device is used.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / 'experiments/ios-jit/launcher-input-fixes59'
BASELINE = ROOT / 'experiments/ios-jit/launcher-unified58/managed/ControllerIntegration.cs'
BASELINE_SHA = 'bf0f831a4b09ddb321903be4c7b8b409ee46542700f08ad6a5184a4ec68c8b59'
CECIL_SHA = 'e3d33263117ffe94550abb1099dc75eb501b7ea9622a93a880decb992dfde7e7'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def regular(path):
    path = path.absolute()
    require(ROOT in path.parents and ROOT / '.private' not in path.parents
            and path.is_file() and not path.is_symlink() and path.resolve() == path,
            'Expected a regular unaliased public repository input')
    return path


def method_body(text, signature):
    """Read the simple selected lifecycle method without crossing its braces."""
    start = text.index(signature)
    start = text.index('{', start)
    depth = 1
    for end in range(start + 1, len(text)):
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
            if depth == 0:
                return re.sub(r'\s+', '', text[start + 1:end])
    raise ValueError('Unclosed lifecycle method')


def wiring_checks(entry, native):
    checks = []
    suspend = method_body(entry, 'public static int Suspend(int unused)')
    resume = method_body(entry, 'public static int Resume(int unused)')
    require(suspend.count('ControllerIntegration.Suspend();') == 1
            and suspend.index('ControllerIntegration.Suspend();') < suspend.index('TouchPort.Reset();')
            < suspend.index('Platform.SuspendAudio(true);'), 'Managed suspend wiring/order differs')
    checks.append('selected Entry.Suspend marks controller suspended before touch/audio suspension')
    require(resume.count('ControllerIntegration.Resume();') == 1
            and resume.index('Platform.SuspendAudio(false);') < resume.index('game.ResetElapsedTime();')
            < resume.index('ControllerIntegration.Resume();') < resume.index('state=2;'),
            'Managed resume wiring/order differs')
    checks.append('selected Entry.Resume queues controller replay after audio/clock and before active state')
    resign = method_body(native, '- (void)resignActive')
    foreground = method_body(native, '- (void)foreground')
    require(resign.index('self.displayLink.paused=YES;') < resign.index('CJGraphicsCall("Suspend",'),
            'Native must stop display ticks before managed suspension')
    require(foreground.index('CJGraphicsCall("Resume",') < foreground.index('self.displayLink.paused=NO;'),
            'Native must resume managed state before restarting ticks')
    checks.append('actual selected native lifecycle stops ticks before Suspend and restarts after Resume')
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True)
    parser.add_argument('--sdk', default='.build/everest55-audit-sdk/sdk')
    parser.add_argument('--adapter', help='Fresh compiled59 public adapter, inspected as metadata only')
    parser.add_argument('--baseline-adapter', help='Public58 adapter that must fail the lifecycle call audit')
    parser.add_argument('--cecil', default='.build/everest55-audit-sdk/audit-tools/Mono.Cecil.dll')
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    require(ROOT / '.build' in work.parents and work.resolve() == work and not work.exists(),
            'Use a fresh unaliased output under .build')
    sdk = (ROOT / args.sdk).absolute()
    require(ROOT / '.build' in sdk.parents and sdk.resolve() == sdk, 'Use an explicit public SDK under .build')
    dotnet = regular(sdk / 'dotnet')
    compiler = regular(sdk / 'sdk/8.0.422/Roslyn/bincore/csc.dll')
    refs = sorted((sdk / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    require(len(refs) == 163, 'Use pinned SDK8.0.422 / reference pack8.0.28')
    for path in refs:
        regular(path)
    require(sha(regular(BASELINE)) == BASELINE_SHA, 'Frozen original58 controller source differs')
    controller = regular(LANE / 'managed/ControllerIntegration.cs')
    entry = regular(LANE / 'managed/GameEntry.cs')
    native = regular(LANE / 'src/main.m')
    fixture = regular(LANE / 'tests/ControllerLifecycleTests.cs')
    metadata_fixture = regular(LANE / 'tests/ControllerLifecycleMetadata.cs')
    inputs = [Path(__file__).resolve(), BASELINE, controller, entry, native, fixture,
              metadata_fixture, dotnet, compiler, *refs]
    adapter = regular(ROOT / args.adapter) if args.adapter else None
    baseline_adapter = regular(ROOT / args.baseline_adapter) if args.baseline_adapter else None
    require(not baseline_adapter or adapter, '--baseline-adapter requires the current59 --adapter')
    cecil = regular(ROOT / args.cecil) if adapter else None
    if adapter:
        require(ROOT / '.build' in adapter.parents, 'Use an explicitly compiled public adapter under .build')
        require(sha(cecil) == CECIL_SHA, 'Use the exact public audit Cecil')
        inputs += [adapter, cecil]
        if baseline_adapter:
            require(ROOT / '.build' in baseline_adapter.parents, 'Use a copied public58 adapter under .build')
            inputs.append(baseline_adapter)
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    wiring = wiring_checks(entry.read_text(), native.read_text())
    work.mkdir(parents=True)
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for path in [ROOT / '.private', ROOT.parent / 'celeste-ios',
                 ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(path)) + '))\n'
    sandbox = work / 'audit.sb'
    sandbox.write_text(policy)
    env = dict(os.environ, DOTNET_ROOT=str(sdk), DOTNET_CLI_HOME=str(work / 'cli-home'),
               DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_MULTILEVEL_LOOKUP='0',
               DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', DOTNET_GENERATE_ASPNET_CERTIFICATE='false')
    commands = []

    def run(command, label, success=True):
        command = list(map(str, command))
        commands.append(command)
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=90, check=False)
        require((result.returncode == 0) == success, 'Unexpected command result; inspect scoped ' + label + '.log')

    def compile_tool(name, sources, definitions=(), extra=()):
        target = work / (name + '.dll')
        response = work / (name + '.rsp')

        def quote(path):
            value = str(path)
            require(not any(c in value for c in ['"', '\n', '\r']), 'Unsupported compiler path')
            return '"' + value + '"'

        response.write_text('\n'.join(['-nologo', '-nostdlib+', '-target:exe', '-optimize+',
                                      '-deterministic+', '-warnaserror+', '-out:' + quote(target)]
                                     + ['-define:' + value for value in definitions]
                                     + ['-r:' + quote(path) for path in [*refs, *extra]]
                                     + [quote(path) for path in sources]) + '\n')
        target.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': {
            'tfm': 'net8.0', 'framework': {'name': 'Microsoft.NETCore.App', 'version': '8.0.28'}}}) + '\n')
        run(['sandbox-exec', '-f', sandbox, dotnet, 'exec', compiler, '-noconfig', '@' + str(response)], 'compile-' + name)
        return target

    reports = {}
    for name, source, defines, expected in [
            ('original58', BASELINE, (), 'REPRODUCED_CONTROLLER58_RESUME_GAP'),
            ('current59', controller, ('BUILD59',), 'PASS_CONTROLLER59_LIFECYCLE')]:
        target = compile_tool(name, [source, fixture], defines)
        report = work / (name + '-report.json')
        run(['sandbox-exec', '-f', sandbox, dotnet, target, report], name)
        value = json.loads(report.read_text())
        require(value['status'] == expected and value['checks'], 'Unexpected controller fixture result')
        reports[name] = dict(status=value['status'], checks=len(value['checks']),
                             report_sha256=sha(report), binary_sha256=sha(target))
        print(expected, 'checks=' + str(len(value['checks'])), flush=True)
    if adapter:
        shutil.copyfile(cecil, work / 'Mono.Cecil.dll')
        target = compile_tool('MetadataWiring', [metadata_fixture], extra=[cecil])
        report = work / 'actual-adapter-report.json'
        run(['sandbox-exec', '-f', sandbox, dotnet, target, adapter, report], 'actual-adapter-wiring')
        value = json.loads(report.read_text())
        require(value['status'] == 'PASS_CONTROLLER59_ACTUAL_ADAPTER_WIRING' and len(value['checks']) == 5,
                'Actual compiled59 adapter lifecycle wiring differs')
        reports['actual_adapter'] = dict(status=value['status'], checks=5, adapter_sha256=sha(adapter),
                                         report_sha256=sha(report), binary_sha256=sha(target))
        print(value['status'], 'checks=5', flush=True)
        if baseline_adapter:
            negative_report = work / 'original58-adapter-report.json'
            run(['sandbox-exec', '-f', sandbox, dotnet, target, baseline_adapter, negative_report],
                'original58-adapter-rejected', success=False)
            log = work / 'original58-adapter-rejected.log'
            require(not negative_report.exists() and 'Missing or repeated controller lifecycle call: Suspend' in log.read_text(),
                    'Original58 adapter did not fail at the intended missing lifecycle call')
            reports['original58_adapter'] = dict(status='REJECTED_ORIGINAL58_ADAPTER_MISSING_LIFECYCLE_CALLS',
                                                 checks=1, adapter_sha256=sha(baseline_adapter), log_sha256=sha(log))
            print(reports['original58_adapter']['status'], flush=True)
    require(hashes == {str(path.relative_to(ROOT)): sha(path) for path in inputs},
            'A captured production, fixture, SDK or adapter input changed')
    receipt = dict(status='PASS_CONTROLLER59_RESUME_REGRESSION',
                   verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   source_sha256=hashes, reports=reports, source_wiring_checks=wiring,
                   actual_production_controller_source_compiled=True, original58_negative_control=True,
                   actual_gameentry_adapter_metadata_checked=bool(adapter),
                   engine_sdl_hook_boundaries_controlled=True, network_denied=True,
                   payload_assembly_loaded_or_executed=False, game_or_native_controller_executed=False,
                   physical_device_tested=False, private_or_legacy_inputs=False, commands=commands)
    path = work / 'receipt.json'
    path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], sha(path), flush=True)


if __name__ == '__main__':
    main()
