#!/usr/bin/env python3
"""Reuse accepted Everest IL; patch isolated MonoMod and build the helper adapter."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[2]
ACCEPTED=ROOT/'.build/ios-jit/content-managed';STAGE=ROOT/'.build/ios-jit/launcher-backbuffer-managed'
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
 env=dict(os.environ,DOTNET_ROOT=str(SDK),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
 tools=STAGE/'patch-tool';tools.mkdir(exist_ok=True)
 tool_source=SOURCE/'tools/PatchMonoMod.cs'
 tool=tools/'PatchMonoMod.dll'
 tool_args=['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:exe','-out:"'+str(tool)+'"']
 tool_args+=['-r:"'+str(p)+'"' for p in refs+[STAGE/'Mono.Cecil.dll']]+['"'+str(tool_source)+'"']
 (tools/'compile.rsp').write_text('\n'.join(tool_args)+'\n')
 tool_compile=[str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(tools/'compile.rsp')]
 subprocess.run(tool_compile,env=env,check=True)
 shutil.copy2(STAGE/'Mono.Cecil.dll',tools/'Mono.Cecil.dll')
 (tools/'PatchMonoMod.runtimeconfig.json').write_text(json.dumps(dict(runtimeOptions=dict(tfm='net8.0',framework=dict(name='Microsoft.NETCore.App',version='8.0.28')))))
 utils=STAGE/'MonoMod.Utils.dll'
 assert sha(utils)=='3fc0b9c537032738ee445023a15c738b5fab4726e60a17f769b46d9afa2f9dda'
 original_utils_sha256=sha(utils)
 patched=STAGE/'MonoMod.Utils.patched.dll'
 literal_source=SOURCE/'tools/LiteralFieldEmitter.cs'
 literal=tools/'LiteralFieldEmitter.dll'
 literal_args=['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:library','-out:"'+str(literal)+'"']
 literal_args+=['-r:"'+str(p)+'"' for p in refs+[STAGE/'Mono.Cecil.dll',utils]]+['"'+str(literal_source)+'"']
 (tools/'literal.rsp').write_text('\n'.join(literal_args)+'\n')
 literal_compile=[str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(tools/'literal.rsp')]
 subprocess.run(literal_compile,env=env,check=True)
 tool_run=[str(SDK/'dotnet'),str(tool),str(utils),str(literal),str(patched),str(STAGE/'monomod-literal-fields.json')]
 subprocess.run(tool_run,env=env,check=True)
 patched.replace(utils)
 graphics_source=SOURCE/'tools/FnaGraphicsCompatibility.cs'
 graphics_tool=tools/'FnaGraphicsCompatibility.dll'
 graphics_args=['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:exe','-out:"'+str(graphics_tool)+'"']
 graphics_args+=['-r:"'+str(p)+'"' for p in refs+[STAGE/'Mono.Cecil.dll']]+['"'+str(graphics_source)+'"']
 (tools/'graphics.rsp').write_text('\n'.join(graphics_args)+'\n')
 graphics_compile=[str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(tools/'graphics.rsp')]
 subprocess.run(graphics_compile,env=env,check=True)
 shutil.copy2(tools/'PatchMonoMod.runtimeconfig.json',tools/'FnaGraphicsCompatibility.runtimeconfig.json')
 graphics_run=[str(SDK/'dotnet'),str(graphics_tool),'patch',str(STAGE/'FNA.dll'),str(STAGE/'FNA.extended.dll'),str(STAGE/'fna-graphics-compatibility.json')]
 subprocess.run(graphics_run,env=env,check=True)
 (STAGE/'FNA.extended.dll').replace(STAGE/'FNA.dll')
 graphics_receipt=json.loads((STAGE/'fna-graphics-compatibility.json').read_text())
 base_fna=json.loads((STAGE/'fna-compatibility.json').read_text())
 (STAGE/'fna-compatibility.json').write_text(json.dumps(dict(base=base_fna,graphics=graphics_receipt,output_sha256=sha(STAGE/'FNA.dll')),indent=2)+'\n')
 backbuffer_guard=SOURCE/'tools/BackbufferReadGuard.cs'
 backbuffer_source=SOURCE/'tools/PatchFnaBackbuffer.cs'
 for name,source,is_exe in [('BackbufferReadGuard',backbuffer_guard,False),('PatchFnaBackbuffer',backbuffer_source,True)]:
  out=tools/(name+'.dll');rsp=tools/(name+'.rsp')
  rsp.write_text('\n'.join(['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:'+('exe' if is_exe else 'library'),'-out:"'+str(out)+'"']+['-r:"'+str(p)+'"' for p in refs+([STAGE/'Mono.Cecil.dll'] if is_exe else [])]+['"'+str(source)+'"'])+'\n')
  subprocess.run([str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)],env=env,check=True)
 shutil.copy2(tools/'PatchMonoMod.runtimeconfig.json',tools/'PatchFnaBackbuffer.runtimeconfig.json')
 backbuffer_run=[str(SDK/'dotnet'),str(tools/'PatchFnaBackbuffer.dll'),str(STAGE/'FNA.dll'),str(tools/'BackbufferReadGuard.dll'),str(STAGE/'FNA.backbuffer.dll'),str(STAGE/'fna-backbuffer-compatibility.json')]
 subprocess.run(backbuffer_run,env=env,check=True)
 (STAGE/'FNA.backbuffer.dll').replace(STAGE/'FNA.dll')
 backbuffer_receipt=json.loads((STAGE/'fna-backbuffer-compatibility.json').read_text())
 full_fna=json.loads((STAGE/'fna-compatibility.json').read_text());full_fna['backbuffer']=backbuffer_receipt;full_fna['output_sha256']=sha(STAGE/'FNA.dll')
 (STAGE/'fna-compatibility.json').write_text(json.dumps(full_fna,indent=2)+'\n')
 names=['Celeste.dll','FNA.dll','MMHOOK_Celeste.dll','MonoMod.Core.dll','MonoMod.RuntimeDetour.dll','MonoMod.Utils.dll','Mono.Cecil.dll','NLua.dll','KeraLua.dll','Newtonsoft.Json.dll']
 module_sources=sorted((SOURCE/'support-module').glob('*.cs'))
 module_args=['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:library','-out:"'+str(STAGE/'CelesteIOS.dll')+'"']
 module_args+=['-r:"'+str(p)+'"' for p in refs+[STAGE/n for n in names]]+['"'+str(p)+'"' for p in module_sources]
 (STAGE/'support.rsp').write_text('\n'.join(module_args)+'\n')
 module_compile=[str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(STAGE/'support.rsp')]
 subprocess.run(module_compile,env=env,check=True)
 names+=['CelesteIOS.dll']
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
 receipt=dict(schema=1,status='PASS_LAUNCHER_SESSION_SUPPORT_ADAPTER_BUILD',accepted_everest_receipt_sha256=sha(ACCEPTED/'receipt.json'),preparation_receipt_sha256=prior['preparation_receipt_sha256'],platform_patch_sha256=sha(STAGE/'platform-patch.json'),fna_compatibility_sha256=sha(STAGE/'fna-compatibility.json'),fna_graphics_compatibility=graphics_receipt,fna_backbuffer_compatibility=backbuffer_receipt,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [*sources,*module_sources,tool_source,literal_source,graphics_source,backbuffer_guard,backbuffer_source]},managed_sha256={p.name:sha(p) for p in STAGE.glob('*.dll')},mono8_utils_compatibility=dict(input_sha256=original_utils_sha256,output_sha256=sha(utils),legacy_native_struct_write_removed=True,literal_fields=json.loads((STAGE/'monomod-literal-fields.json').read_text())),commands=[tool_compile,literal_compile,tool_run,graphics_compile,graphics_run,module_compile,cmd],host_tested=False,device_tested=False)
 (STAGE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
