#!/usr/bin/env python3
"""Compile the external IL fixture after packaging the IPA, then check its logic on the host."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,zipfile
source=Path(__file__).resolve().parent;root=source.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='managed-canary-20260911-06');a=p.parse_args()
base=root/'.build/ios-jit/managed-runtime';sdk=base/'dotnet-sdk-8.0.422'
out=root/'artifacts/ios-jit'/a.build_id;ipa=out/'CelesteJITCanary-unsigned.ipa'
assert ipa.exists(),'Package the IPA first'
stage=root/'.build/ios-jit/managed-canary'/a.build_id/'fixture';stage.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',DOTNET_ROOT=str(sdk),DOTNET_CLI_HOME=str(base/'cli-home'),
         NUGET_PACKAGES=str(base/'nuget'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_MULTILEVEL_LOOKUP='0')
refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'));assert len(refs)>100
def run(args):
 result=subprocess.run(list(map(str,args)),env=env,cwd=stage,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 with (stage/'host-check.log').open('a') as f:f.write(result.stdout)
 if result.returncode:raise RuntimeError(result.stdout)
 return result.stdout
def compile(output,files,extra_refs=(),executable=False):
 rsp=output.with_suffix('.rsp')
 args=['-nologo','-noconfig','-nostdlib+','-nullable:enable','-optimize+','-debug:portable','-deterministic+',
       '-target:'+('exe' if executable else 'library'),'-out:"'+str(output)+'"']
 args += ['-r:"'+str(r)+'"' for r in [*refs,*extra_refs]] + ['"'+str(f)+'"' for f in files]
 rsp.write_text('\n'.join(args)+'\n')
 run([sdk/'dotnet','exec',sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)])
(stage/'host-check.log').write_text('')
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
dll=stage/'Canary-v0.2.2.dll';compile(dll,[source/'fixtures/Canary.cs'])
assert dll.stat().st_mtime_ns > ipa.stat().st_mtime_ns
with zipfile.ZipFile(ipa) as z:
 assert not any('Canary-v0.2.2.dll' in name for name in z.namelist())
runner=stage/'HostCheck.dll';compile(runner,[source/'fixtures/HostCheck.cs'],[dll],True)
runner.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
run(['xcrun','clang','-dynamiclib','-O2',source/'src/CanaryNative.c','-o',stage/'libCJCanaryNative.dylib'])
result=run([sdk/'dotnet','exec',runner]);print(result,end='')
shutil.copy2(dll,out/dll.name)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
receipt={'schema':1,'compile_started_utc':started,'compiled_after_ipa_packaging':True,'ipa_sha256':sha(ipa),
         'dll_sha256':sha(dll),'dll_bytes':dll.stat().st_size,'fixture_source_sha256':sha(source/'fixtures/Canary.cs'),
         'sdk':'8.0.422','target':'net8.0 IL','host_logic_checks':40,'static_switch_il_confirmed':True,'host_runtime':'CoreCLR 8.0.28 macOS x64',
         'device_mono_jit_tested':False,'result':result.strip()}
(out/'fixture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
