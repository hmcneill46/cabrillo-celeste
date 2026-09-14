#!/usr/bin/env python3
"""Reuse accepted Everest IL; compile only the content-import adapter."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[2]
ACCEPTED=ROOT/'.build/ios-jit/everest-managed';STAGE=ROOT/'.build/ios-jit/content-managed'
SDK=ROOT/'.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 STAGE.mkdir(parents=True,exist_ok=True)
 prior=json.loads((ACCEPTED/'receipt.json').read_text())
 for name,digest in prior['managed_sha256'].items():
  assert sha(ACCEPTED/name)==digest,name;shutil.copy2(ACCEPTED/name,STAGE/name)
 for name in ['platform-patch.json','fna-compatibility.json']:shutil.copy2(ACCEPTED/name,STAGE/name)
 shutil.copytree(ACCEPTED/'orig',STAGE/'orig',dirs_exist_ok=True)
 refs=sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
 names=['Celeste.dll','FNA.dll','MMHOOK_Celeste.dll','MonoMod.Core.dll','MonoMod.RuntimeDetour.dll','MonoMod.Utils.dll','Mono.Cecil.dll','NLua.dll','KeraLua.dll']
 sources=sorted((SOURCE/'managed').glob('*.cs'))+[ROOT/'modern-ios/CelesteIOSFoundation'/n for n in ['PlatformPolicies.cs','TouchControlsPolicy.cs']]
 args=['-nologo','-nostdlib+','-unsafe+','-nullable:annotations','-optimize+','-deterministic+','-target:library','-out:"'+str(STAGE/'CelesteJITEverest.dll')+'"']
 args+=['-r:"'+str(p)+'"' for p in refs+[STAGE/n for n in names]]
 args+=['"'+str(p)+'"' for p in sources]
 args+=['-resource:"'+str(p)+'",Celeste.IOSTouchControls.'+p.name for p in sorted((ROOT/'.build/ios-jit/celeste-game/touch-assets').glob('*.a8'))]
 rsp=STAGE/'adapter.rsp';rsp.write_text('\n'.join(args)+'\n')
 cmd=[str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)]
 env=dict(os.environ,DOTNET_ROOT=str(SDK),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
 result=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(STAGE/'compile-adapter.log').write_text(result.stdout)
 if result.returncode:raise RuntimeError(result.stdout)
 receipt=dict(schema=1,status='PASS_CONTENT_IMPORT_ADAPTER_BUILD',accepted_everest_receipt_sha256=sha(ACCEPTED/'receipt.json'),preparation_receipt_sha256=prior['preparation_receipt_sha256'],platform_patch_sha256=sha(STAGE/'platform-patch.json'),fna_compatibility_sha256=sha(STAGE/'fna-compatibility.json'),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},managed_sha256={p.name:sha(p) for p in STAGE.glob('*.dll')},commands=[cmd],host_tested=False,device_tested=False)
 (STAGE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
