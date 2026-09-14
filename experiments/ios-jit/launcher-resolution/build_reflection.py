#!/usr/bin/env python3
"""Patch isolated Mono CoreLib copies; never modify the accepted runtime packs."""
import hashlib,json,subprocess,shutil
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2];B=R/'.build/ios-jit';O=B/'launcher-resolution-reflection';O.mkdir(parents=True,exist_ok=True)
SDK=B/'managed-runtime/dotnet-sdk-8.0.422';refs=sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
receipt=O/'receipt.json'
if receipt.exists():
 old=read(receipt)
 if all(sha(R/n)==v for n,v in old['source_sha256'].items()) and all(sha(R/v['input'])==v['input_sha256'] and sha(R/v['output'])==v['output_sha256'] for v in old['targets'].values()):
  print('PASS_ISOLATED_MONO_REFLECTION_FLAGS_PATCH_READ_ONLY');raise SystemExit(0)
 if (R/'artifacts/ios-jit/launcher-resolution-20260913-26/delivery-receipt.json').exists():raise RuntimeError('Preserve delivered build26; use a new isolated lane.')
tool=O/'PatchReflectionFlags.dll';cecil=B/'launcher-backbuffer-managed/Mono.Cecil.dll'
(O/'compile.rsp').write_text('\n'.join(['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:exe','-out:"'+str(tool)+'"']+['-r:"'+str(p)+'"' for p in refs+[cecil]]+['"'+str(S/'tools/PatchReflectionFlags.cs')+'"'])+'\n')
subprocess.run([str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(O/'compile.rsp')],check=True)
shutil.copy2(cecil,O/cecil.name);(O/'PatchReflectionFlags.runtimeconfig.json').write_text(json.dumps(dict(runtimeOptions=dict(tfm='net8.0',framework=dict(name='Microsoft.NETCore.App',version='8.0.28')))))
targets={};base=read(R/'artifacts/ios-jit/launcher-backbuffer-20260912-24/build-receipt.json')
for name,pack in [('host','pack-osx-8.0.28/runtimes/osx-x64'),('ios','pack-ios-8.0.28/runtimes/ios-arm64')]:
 source=B/'managed-runtime'/pack/'native/System.Private.CoreLib.dll';expected=sha(source)
 if name=='ios':assert expected==base['framework_assembly_sha256']['System.Private.CoreLib.dll']
 target=O/name;target.mkdir(exist_ok=True);out=target/source.name;receipt=target/'patch.json'
 subprocess.run([str(SDK/'dotnet'),str(tool),str(source),expected,str(out),str(receipt)],check=True)
 assert sha(source)==expected
 targets[name]=dict(input=str(source.relative_to(R)),input_sha256=expected,output=str(out.relative_to(R)),output_sha256=sha(out),patch=read(receipt),patch_receipt_sha256=sha(receipt))
result=dict(status='PASS_ISOLATED_MONO_REFLECTION_FLAGS_PATCH',abi=1,targets=targets,source_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),S/'tools/PatchReflectionFlags.cs']},mono_native_archives_changed=False,physical_execution=False)
(O/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
