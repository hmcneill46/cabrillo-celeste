#!/usr/bin/env python3
"""Build the pinned MonoMod IL closure in its isolated net8.0 hosting configuration."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess

source=Path(__file__).resolve().parent;root=source.parents[2]
base=root/'.build/ios-jit/hook-runtime';repo=base/'MonoMod';sdk=base/'dotnet-sdk-9.0.300'
pin=json.loads((source/'dependencies-pin.json').read_text())
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==pin['commit']
assert subprocess.check_output(['git','-C',str(repo/'external/iced'),'rev-parse','HEAD'],text=True).strip()==pin['iced_commit']
patch=json.loads((base/'monomod-patch-receipt.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,item in patch['files'].items():assert sha(repo/name)==item['patched_sha256'],name
archive=base/pin['sdk']['url'].rsplit('/',1)[1]
assert hashlib.sha512(archive.read_bytes()).hexdigest()==pin['sdk']['hash']
env=dict(os.environ,DOTNET_ROOT=str(sdk),DOTNET_CLI_HOME=str(base/'cli-home'),NUGET_PACKAGES=str(base/'nuget'),
 NUGET_HTTP_CACHE_PATH=str(base/'http-cache'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_MULTILEVEL_LOOKUP='0',
 DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
command=[str(sdk/'dotnet'),'build','src/MonoMod.RuntimeDetour/MonoMod.RuntimeDetour.csproj','-c','Release','-f','net8.0',
 '-p:CJAppleJitCanary=true','-p:DoNotAddSuffix=true','-p:RestoreLockedMode=false','-p:NuGetAudit=false','-p:BuildInParallel=false','-p:CopyLocalLockFileAssemblies=true','--nologo']
with (base/'monomod-build.log').open('w') as log:r=subprocess.run(command,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
if r.returncode:
 print((base/'monomod-build.log').read_text()[-14000:]);raise SystemExit(r.returncode)
output=repo/'artifacts/bin/MonoMod.RuntimeDetour/release_net8.0'
assert (output/'MonoMod.RuntimeDetour.dll').exists(),output
closure=base/'managed-libraries';closure.mkdir(exist_ok=True)
files={}
for file in sorted(output.glob('*.dll')):
 shutil.copy2(file,closure/file.name);files[file.name]=sha(file)
assert all(n in files for n in ['MonoMod.RuntimeDetour.dll','MonoMod.Core.dll','MonoMod.Utils.dll','Mono.Cecil.dll'])
packages={}
for assets in (repo/'artifacts/obj').rglob('project.assets.json'):
 for key,v in json.loads(assets.read_text()).get('libraries',{}).items():
  if v.get('type')=='package':packages[key]=v.get('sha512')
receipt={'status':'PASS_PINNED_MONOMOD_NET8_BUILD','pin':pin,'patch':patch,'assemblies_sha256':files,'restored_packages_sha512':packages,
 'command':command,'runtime_target':'net8.0 IL','native_desktop_helpers_bundled':False,'device_tested':False}
(base/'dependencies-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'assemblies':files,'restored_package_count':len(packages)},indent=2))
