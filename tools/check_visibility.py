#!/usr/bin/env python3
"""Exercise exact field/method grants and denied controls with both metadata objects."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from platform_inputs import ROOT, owned, sha
from build_visibility_runtime import ORIGINAL, PATCHED


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', required=True); p.add_argument('--work', required=True)
    a = p.parse_args(); receipt_path = owned(a.runtime); work = owned(a.work)
    assert ROOT / '.build' in work.parents and not work.exists()
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'PASS_SCOPED_VISIBILITY_RUNTIME_RESTORE'
    assert receipt['host_control']['class_sha256'] == ORIGINAL and receipt['host_fixed']['class_sha256'] == PATCHED
    work.mkdir(parents=True); framework = work / 'Managed'; framework.mkdir()
    pack = ROOT / '.private/loading-inputs/host/runtime'
    for f in list((pack / 'lib/net8.0').glob('*.dll')) + [pack / 'native/System.Private.CoreLib.dll']:
        shutil.copyfile(f, framework / f.name)
    source = ROOT / 'experiments/ios-jit/launcher-visibility/tests'
    g1 = ROOT / 'experiments/ios-jit/managed-canary/src'
    sdk = ROOT / '.private/loading-inputs/sdk8'
    native = ROOT / '.private/loading-inputs/host/native'
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    commands = []
    def run(cmd, label):
        cmd = list(map(str, cmd)); commands.append(cmd)
        r = subprocess.run(cmd, env=env, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        (work / (label + '.log')).write_bytes(r.stdout)
        if r.returncode: raise RuntimeError(label + ' failed: ' + r.stdout.decode(errors='replace')[-2000:])
        return r.stdout.decode()
    fixture = framework / 'VisibilityFixture.dll'
    refs = sorted((sdk / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    rsp = work / 'compile.rsp'
    rsp.write_text('\n'.join(['-nologo','-target:library','-nostdlib+','-deterministic+','-optimize+','-out:"'+str(fixture)+'"']+['-r:"'+str(f)+'"' for f in refs]+['"'+str(source/'VisibilityFixture.cs')+'"'])+'\n')
    run([sdk / 'dotnet','exec',sdk / 'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)], 'fixture')
    env['CJIT_TEST_TPA'] = ':'.join(str(f) for f in sorted(framework.glob('*.dll')))
    include = ROOT / '.private/inputs/.build/ios-jit/managed-runtime/pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0'
    results = {}
    for mode, key in [('0','host_control'), ('1','host_fixed')]:
        archive = owned(receipt[key]['path']); assert sha(archive) == receipt[key]['sha256']
        binary = work / ('visibility-'+mode)
        run(['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-I'+str(g1),'-I'+str(include),
             source / 'visibility_host.c',g1 / 'CJMonoThread.c',g1 / 'CJNativeResolver.c',g1 / 'CanaryNative.c',
             ROOT / 'experiments/ios-jit/launcher-loading/tests/host_page_model.c',
             archive,*sorted(native.glob('libmono-component-*.a')),'-lc++','-liconv','-lz',
             '-framework','CoreFoundation','-framework','Foundation','-framework','Security','-o',binary], 'compile-'+mode)
        log = run([binary,pack / 'native/libSystem.Native.dylib',framework,fixture,mode], 'run-'+mode)
        assert 'PASS_VISIBILITY_36_CASES' in log and log.count('VISIBILITY grant=') == 36
        results[key] = dict(archive_sha256=sha(archive),log_sha256=sha(work / ('run-'+mode+'.log')), cases=36)
        print('PASS '+key+' 36 cases',flush=True)
    result = dict(status='PASS_VISIBILITY_FIELDS_METHODS_AND_DENIED_CONTROLS',runtime_receipt_sha256=sha(receipt_path),
                  results=results,source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__),source/'visibility_host.c',source/'VisibilityFixture.cs',ROOT/'experiments/ios-jit/launcher-loading/tests/host_page_model.c']},commands=commands,device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__': main()
