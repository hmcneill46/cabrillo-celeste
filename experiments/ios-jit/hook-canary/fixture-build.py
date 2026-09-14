#!/usr/bin/env python3
"""Compile the imported IL hook fixture; --development is for local runtime debugging."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,zipfile

source=Path(__file__).resolve().parent;root=source.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--development',action='store_true');p.add_argument('--build-id',default='hook-canary-20260911-09');a=p.parse_args()
base=root/'.build/ios-jit/hook-runtime';sdk=root/'.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'
out=root/('artifacts/ios-jit/'+a.build_id) if not a.development else base/'development-fixture'
out.mkdir(parents=True,exist_ok=True);stage=base/'fixture-compile';stage.mkdir(exist_ok=True)
ipa=out/'CelesteJITHooks-unsigned.ipa'
if not a.development:assert ipa.is_file(),'Package the IPA before compiling the delivered external fixture'
dependencies=json.loads((base/'dependencies-receipt.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
libraries=[base/'managed-libraries'/name for name in dependencies['assemblies_sha256']]
for f in libraries:assert sha(f)==dependencies['assemblies_sha256'][f.name]
refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'));assert len(refs)>100
files=[source.parent/'managed-canary/fixtures/Canary.cs',source/'fixtures/HookCanary.cs']
dll=out/'HookCanary-v0.3.0.dll'
args=['-nologo','-noconfig','-nostdlib+','-nullable:enable','-optimize+','-deterministic+','-target:library','-out:"'+str(dll)+'"']
args += ['-r:"'+str(f)+'"' for f in [*refs,*libraries]]+['"'+str(f)+'"' for f in files]
rsp=stage/'fixture.rsp';rsp.write_text('\n'.join(args)+'\n')
env=dict(os.environ,DOTNET_ROOT=str(sdk),DOTNET_CLI_HOME=str(base/'cli-home'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
command=[str(sdk/'dotnet'),'exec',str(sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)]
r=subprocess.run(command,env=env,cwd=stage,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(stage/'compile.log').write_text(r.stdout)
if r.returncode:print(r.stdout);raise SystemExit(r.returncode)
if not a.development:
 assert dll.stat().st_mtime_ns>ipa.stat().st_mtime_ns
 with zipfile.ZipFile(ipa) as z:assert not any('HookCanary' in name and name.endswith('.dll') for name in z.namelist())
receipt={'schema':1,'compile_started_utc':started,'development_fixture':a.development,'compiled_after_ipa_packaging':not a.development,
 'ipa_sha256':sha(ipa) if not a.development else None,'dll_sha256':sha(dll),'dll_bytes':dll.stat().st_size,
 'source_sha256':{str(f.relative_to(root)):sha(f) for f in files},'dependencies_sha256':dependencies['assemblies_sha256'],
 'sdk':'8.0.422','target':'net8.0 IL','host_mono_tested':False,'device_tested':False,'command':command}
(out/'fixture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'dll':str(dll),'sha256':sha(dll),'bytes':dll.stat().st_size},indent=2))
