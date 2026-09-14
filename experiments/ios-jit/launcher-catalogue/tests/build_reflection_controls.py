#!/usr/bin/env python3
"""Compile a deliberately absent signature dependency and verify the CoreCLR contract."""
import hashlib,json,subprocess,os
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit';O=B/'launcher-catalogue-reflection-controls';O.mkdir(parents=True,exist_ok=True)
SDK=B/'managed-runtime/dotnet-sdk-8.0.422';refs=sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
compile=O/'compile';runtime=O/'runtime';compile.mkdir(exist_ok=True);runtime.mkdir(exist_ok=True)
(compile/'MissingSignature.cs').write_text('namespace MissingSignature { public sealed class Type {} }\n')
(compile/'Runner.cs').write_text('static class Runner { static void Main() { ReflectionFlagsTests.Run(); } }\n')
def build(name,sources,extra,output,exe=False):
 rsp=compile/(name+'.rsp');rsp.write_text('\n'.join(['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:'+('exe' if exe else 'library'),'-out:"'+str(output)+'"']+['-r:"'+str(p)+'"' for p in refs+extra]+['"'+str(p)+'"' for p in sources])+'\n')
 subprocess.run([str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)],check=True)
build('missing',[compile/'MissingSignature.cs'],[],compile/'MissingSignature.dll')
build('signatures',[S/'tests/ReflectionSignatures.cs'],[compile/'MissingSignature.dll'],runtime/'ReflectionSignatures.dll')
build('runner',[compile/'Runner.cs',S/'tests/ReflectionFlagsTests.cs'],[],runtime/'Runner.dll',True)
(runtime/'Runner.runtimeconfig.json').write_text(json.dumps(dict(runtimeOptions=dict(tfm='net8.0',framework=dict(name='Microsoft.NETCore.App',version='8.0.28')))))
env=dict(os.environ,CJIT_REFLECTION_SIGNATURES=str(runtime/'ReflectionSignatures.dll'))
p=subprocess.run([str(SDK/'dotnet'),str(runtime/'Runner.dll')],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/'coreclr.log').write_text(p.stdout)
assert p.returncode==0,p.stdout
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'receipt.json').write_text(json.dumps(dict(status='PASS_CORECLR_MISSING_SIGNATURE_ATTRIBUTE_CONTRACT',checks=p.stdout.count('REFLECTION_FLAGS_PASS '),fixture_sha256=sha(runtime/'ReflectionSignatures.dll'),source_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),S/'tests/ReflectionSignatures.cs',S/'tests/ReflectionFlagsTests.cs']}),indent=2)+'\n');print('PASS_CORECLR_MISSING_SIGNATURE_ATTRIBUTE_CONTRACT')
