#!/usr/bin/env python3
"""Exact phone failure and literal/ordinary-field controls on the accepted host Mono."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit';O=B/'launcher-session-literal-tests';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rt=B/'managed-runtime';sdk=rt/'dotnet-sdk-8.0.422';pack=rt/'pack-osx-8.0.28/runtimes/osx-x64';mono=rt/'mono-build-host-coop';managed=B/'launcher-session-managed';old=B/'launcher-compat-managed/MonoMod.Utils.dll'
framework=O/'Managed';framework.mkdir(exist_ok=True)
for f in [*list((pack/'lib/net8.0').glob('*.dll')),pack/'native/System.Private.CoreLib.dll',*list(managed.glob('*.dll'))]:shutil.copy2(f,framework/f.name)
refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
fixture=O/'LiteralFieldTests.dll';rsp=O/'literal.rsp'
rsp.write_text('\n'.join(['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:library','-out:"'+str(fixture)+'"']+['-r:"'+str(p)+'"' for p in refs+[managed/n for n in ['Celeste.dll','FNA.dll','MonoMod.Utils.dll']]]+['"'+str(S/'tests/LiteralFieldTests.cs')+'"'])+'\n')
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',DOTNET_ROOT=str(sdk),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
commands=[]
def run(cmd):
 commands.append(list(map(str,cmd)));subprocess.run(cmd,env=env,check=True)
run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)])
g1=S.parent/'managed-canary';lib=B/'sj-lobby-runtime/host/libmonosgen-2.0.a'
accepted=json.loads((B/'sj-lobby-runtime/receipt.json').read_text());assert sha(lib)==accepted['targets']['host']['sha256']
libs=[lib]+[mono/('mono/mini/libmono-component-'+n+'-static.a') for n in ['marshal-ilgen','debugger-stub','hot_reload-stub','diagnostics_tracing-stub']]
files=[S/'tests/literal_fields_host.c',S/'tests/host_page_model.c',g1/'src/CJMonoThread.c',g1/'src/CJNativeResolver.c',g1/'src/CanaryNative.c']
binary=O/'literal-fields-test'
run(['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-I'+str(g1/'src'),'-I'+str(rt/'pack-ios-8.0.28/runtimes/ios-arm64/native/include/mono-2.0'),*files,*libs,'-lc++','-liconv','-lz','-framework','CoreFoundation','-framework','Foundation','-framework','Security','-o',binary])
env['CJIT_TEST_TPA']=':'.join(str(p) for p in sorted(framework.glob('*.dll')))
results={}
prior=json.loads((B/'launcher-compat-managed/receipt.json').read_text());assert sha(old)==prior['managed_sha256']['MonoMod.Utils.dll']
for mode,utils in [(0,old),(1,managed/'MonoMod.Utils.dll')]:
 shutil.copy2(utils,framework/'MonoMod.Utils.dll')
 cmd=[str(p) for p in [binary,pack/'native/libSystem.Native.dylib',framework,fixture,str(mode)]]
 p=subprocess.run(cmd,env=env,cwd=O,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);log=O/('original.log' if mode==0 else 'fixed.log');log.write_text(p.stdout)
 if p.returncode:print(p.stdout[-5000:]);raise RuntimeError(('Mono literal test',mode,p.returncode))
 assert 'PASS_REAL_MONO_LITERAL_CONTROL mode='+str(mode) in p.stdout
 results[str(mode)]=dict(utils_sha256=sha(utils),log_sha256=sha(log),returncode=p.returncode,checks=p.stdout.count('LITERAL_FIELD_PASS '),run=cmd)
 print(p.stdout[-500:])
# Repeat generation and reject an already-patched input before any output is written.
patch=managed/'patch-tool/PatchMonoMod.dll';emitter=managed/'patch-tool/LiteralFieldEmitter.dll'
repeat=O/'repeat.dll';repeatReceipt=O/'repeat.json'
run([sdk/'dotnet',patch,B/'content-managed/MonoMod.Utils.dll',emitter,repeat,repeatReceipt]);assert sha(repeat)==sha(managed/'MonoMod.Utils.dll')
for bad in [managed/'MonoMod.Utils.dll',managed/'FNA.dll']:
 out=O/('rejected-'+bad.name);p=subprocess.run([str(x) for x in [sdk/'dotnet',patch,bad,emitter,out,O/'rejected.json']],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 assert p.returncode and 'Unreviewed MonoMod.Utils input' in p.stdout and not out.exists()
 (O/('rejected-'+bad.name+'.log')).write_text(p.stdout)
result=dict(status='PASS_ACTUAL_MONO_LITERAL_FIELDS_AND_ORIGINAL_FAILURE',runtime_archive_sha256=sha(lib),fixture_sha256=sha(fixture),source_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),S/'tests/LiteralFieldTests.cs',*files,S/'tools/PatchMonoMod.cs',S/'tools/LiteralFieldEmitter.cs']},results=results,patch=json.loads((managed/'monomod-literal-fields.json').read_text()),deterministic_repeat=True,wrong_or_patched_input_rejected=True,original_game_sha256=sha(managed/'Celeste.dll'),device_execution=False,commands=commands)
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
