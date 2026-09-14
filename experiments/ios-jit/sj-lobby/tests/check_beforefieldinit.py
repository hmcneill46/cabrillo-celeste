#!/usr/bin/env python3
"""Test Mono member visibility grants with original-runtime and denied-access controls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

source = Path(__file__).resolve().parents[1]
g1=source.parent/'managed-canary'
root = source.parents[2]
base = root / '.build/ios-jit/managed-runtime'
build = base / 'mono-build-host-coop'
stage = root / '.build/ios-jit/sj-lobby-bfi-tests'
stage.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
native = base / 'pack-ios-8.0.28/runtimes/ios-arm64/native'
# Use framework IL from the matching macOS Mono pack for this host architecture,
# and a purpose-built visibility fixture. No device execution is claimed.
framework = stage / 'Managed'
framework.mkdir(exist_ok=True)
pack = base / 'pack-osx-8.0.28/runtimes/osx-x64'
for file in list((pack / 'lib/net8.0').glob('*.dll')) + [pack / 'native/System.Private.CoreLib.dll']:
    shutil.copy2(file, framework / file.name)
sdk=base/'dotnet-sdk-8.0.422'
fixture=stage/'FemtoHelper.dll'
refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
rsp=stage/'compile.rsp';rsp.write_text('\n'.join(['-nologo','-target:library','-nostdlib+','-deterministic+','-optimize+','-out:"'+str(fixture)+'"']+['-r:"'+str(p)+'"' for p in refs]+['"'+str(source/'tests/BeforeFieldInitFixture.cs')+'"']))
subprocess.run([str(sdk/'dotnet'),'exec',str(sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)],env=env,check=True)
shutil.copy2(fixture,framework/fixture.name)
env['CJIT_TEST_TPA'] = ':'.join(str(p) for p in sorted(framework.glob('*.dll')))
system_native = pack / 'native/libSystem.Native.dylib'
libraries = [build / 'mono/mini/libmonosgen-2.0.a']
libraries += [build / ('mono/mini/libmono-component-' + name + '-static.a') for name in
              ('marshal-ilgen', 'debugger-stub', 'hot_reload-stub', 'diagnostics_tracing-stub')]
config = (build / 'config.h').read_text()
assert '#define ENABLE_COOP_SUSPEND 1' in config
assert '#define DISABLE_INTERPRETER 1' in config and '#define DISABLE_AOT 1' in config
binary = stage / 'mono-visibility-test'
command = ['xcrun', 'clang', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
    '-I' + str(g1 / 'src'), '-I' + str(native / 'include/mono-2.0'),
    str(source / 'tests/host_page_model.c'), str(source / 'tests/visibility_host.c'), str(g1 / 'src/CJMonoThread.c'),
    str(g1 / 'src/CJNativeResolver.c'), str(g1 / 'src/CanaryNative.c'), *map(str, libraries),
    '-lc++', '-liconv', '-lz', '-framework', 'CoreFoundation', '-framework', 'Foundation', '-framework', 'Security', '-o', str(binary)]
results={}
original=root/'.build/ios-jit/sj-budget-runtime/host/libmonosgen-2.0.a'
patched=root/'.build/ios-jit/sj-lobby-runtime/host/libmonosgen-2.0.a'
for mode,archive in [('0',original),('1',patched)]:
    cmd=[str(archive) if x==str(libraries[0]) else x for x in command]
    subprocess.run(cmd,env=env,check=True)
    result=subprocess.run([binary,system_native,framework,fixture,mode],env=env,cwd=stage,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
    (stage/(mode+'.log')).write_text(result.stdout)
    assert result.returncode==0 and ('original eager initialization reproduced' if mode=='0' else 'PASS_BFI_13_CASES') in result.stdout,(result.returncode,result.stdout[-5000:])
    results[mode]=dict(log_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),command=cmd)
    print(result.stdout[-500:])
# A differently named assembly must retain the old Mono initialization policy.
other=framework/'OtherHelper.dll';other_rsp=stage/'other.rsp';other_rsp.write_text(rsp.read_text().replace(str(fixture),str(other)))
subprocess.run([str(sdk/'dotnet'),'exec',str(sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(other_rsp)],env=env,check=True)
env['CJIT_TEST_TPA']=':'.join(str(p) for p in sorted(framework.glob('*.dll')))
control=subprocess.run([binary,system_native,framework,other,'0'],env=env,cwd=stage,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
assert control.returncode==0 and 'original eager initialization reproduced' in control.stdout,control.stdout[-2000:]
(stage/'unrelated-assembly.log').write_text(control.stdout)
results['unrelated_assembly']=dict(sha256=hashlib.sha256(other.read_bytes()).hexdigest(),log_sha256=hashlib.sha256(control.stdout.encode()).hexdigest(),runtime_sha256=hashlib.sha256(patched.read_bytes()).hexdigest())
receipt=dict(status='PASS_SCOPED_BEFOREFIELDINIT_ORIGINAL_CONTROL_AND_13_CASES',patched_cases=13,results=results,source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),source/'tests/BeforeFieldInitFixture.cs',source/'tests/visibility_host.c',source/'tests/host_page_model.c']},device_tested=False)
(stage/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
