#!/usr/bin/env python3
"""Validate the actual unsigned IPA, paired IL fixture and pinned build inputs."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,zipfile
source=Path(__file__).resolve().parents[1];root=source.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='hook-canary-20260911-09');a=p.parse_args()
out=root/'artifacts/ios-jit'/a.build_id;receipt=json.loads((out/'build-receipt.json').read_text())
fixture=json.loads((out/'fixture-receipt.json').read_text());ipa=out/'CelesteJITHooks-unsigned.ipa'
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(ipa.read_bytes()) == receipt['ipa_sha256'] == fixture['ipa_sha256']
assert sha((out/'HookCanary-v0.3.0.dll').read_bytes()) == fixture['dll_sha256']
assert fixture['compiled_after_ipa_packaging'] and not fixture['development_fixture']
for name,value in receipt['source_sha256'].items(): assert sha((root/name).read_bytes())==value,name
for name,value in receipt['native_library_sha256'].items(): assert sha((root/name).read_bytes())==value,name
spec=importlib.util.spec_from_file_location('canary_build',source/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
prefix='Payload/CelesteJITHooks.app/'
with zipfile.ZipFile(ipa) as z:
 assert z.testzip() is None
 assert all(name.startswith(prefix) for name in z.namelist())
 builder.validate_payload_members((name,z.read(name)) for name in z.namelist())
 assert not any('_CodeSignature' in name or 'embedded.mobileprovision' in name or 'HookCanary-v0.3.0.dll' in name for name in z.namelist())
 binary=z.read(prefix+'CelesteJITHooks')
 magic,cpu,subtype,kind,count,commands,flags,reserved=struct.unpack_from('<8I',binary)
 assert magic==0xfeedfacf and cpu==0x100000c and kind==2
 cursor=32
 for _ in range(count):
  cmd,length=struct.unpack_from('<2I',binary,cursor);assert cmd!=0x1d,'LC_CODE_SIGNATURE present';assert length>=8;cursor+=length
 assert cursor==32+commands
 assert sha(binary)==receipt['executable_sha256']
 assert builder.read_compiled_protocol(binary)==receipt['compiled_protocol']
 assert receipt['compiled_protocol']['bytes_per_arena']==16777216
 assert receipt['resolved_protocol_header']=='experiments/ios-jit/managed-canary/src/ProbeProtocol.h'
 build=json.loads(z.read(prefix+'BuildInfo.json'))
 assert build['source_sha256']==receipt['source_sha256'] and build['aot_disabled'] and build['interpreter_disabled']
 assert build['runtime_pin']['runtime_commit']=='46295af5828b062bbbf93a9cef50fd8cb9fbcb09'
 assert len(build['framework_assembly_sha256'])==168
 assert len(build['hook_assembly_sha256'])==10 and build['hook_assembly_sha256']==fixture['dependencies_sha256']
 assert build['monomod_pin']['commit']=='dfc30a1506d37fb88a2c2be004f525205f46a24c'
 assert set(n.rsplit('/',1)[-1] for n in z.namelist() if n.startswith(prefix+'Managed/'))==set(build['framework_assembly_sha256'])|set(build['hook_assembly_sha256'])
 for name,value in build['hook_assembly_sha256'].items():assert sha(z.read(prefix+'Managed/'+name))==value
 for name,value in build['framework_assembly_sha256'].items():assert sha(z.read(prefix+'Managed/'+name))==value
 assert sha(z.read(prefix+'celeste-jit-probe.js'))==build['script_template_sha256']
 for name in ['licenses/MonoMod-LICENSE.txt','licenses/Iced-LICENSE.txt','licenses/Mono.Cecil-LICENSE.txt','licenses/MonoMod-Backports-ILHelpers-LICENSE.txt']:assert z.read(prefix+name)
 for name in ['LICENSE.TXT','THIRD-PARTY-NOTICES.TXT','THIRD_PARTY_NOTICES.md','REPOSITORY_LICENSE.txt']:assert z.read(prefix+name)
result={'status':'PASS_UNSIGNED_HOOK_IPA_AND_EXTERNAL_FIXTURE','ipa_bytes':ipa.stat().st_size,'ipa_sha256':receipt['ipa_sha256'],
        'dll_sha256':fixture['dll_sha256'],'framework_assembly_count':len(build['framework_assembly_sha256']),'hook_assembly_count':len(build['hook_assembly_sha256']),
        'compiled_protocol':receipt['compiled_protocol'],'correct_protocol_header_verified':True,
        'dsym_inside_ipa':False,'code_signature':False,'runtime_and_sources_match_receipt':True,'external_fixture_not_in_ipa':True,'device_execution':False}
(out/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
