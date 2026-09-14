#!/usr/bin/env python3
"""Verify actual native request generation, packaged ARM64 constants and script compatibility."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,subprocess,zipfile
source=Path(__file__).resolve().parents[1];root=source.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='celeste-canary-20260911-12');a=p.parse_args()
out=root/'artifacts/ios-jit'/a.build_id;stage=root/'.build/ios-jit/celeste-canary'/a.build_id/'protocol-test';stage.mkdir(parents=True,exist_ok=True)
sample=root/'.build/ios-jit/celeste-canary'/(a.build_id+'-simulator')/'smoke/native-generated-request.json';assert sample.exists()
old=json.loads((root/'artifacts/ios-jit/hook-canary-20260911-07/build-receipt.json').read_text())
old_source=root/'.build/ios-jit/device-evidence/2026-09-11/build-7-ready/source-snapshot/experiments/ios-jit/hook-canary/src/main.m'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old_source)==old['source_sha256']['experiments/ios-jit/hook-canary/src/main.m']
args=[];skip=False
for word in old['compile_command']:
 if skip:skip=False;continue
 if word=='-o':skip=True;continue
 if word=='-c':args+=['-E','-dM'];continue
 if word.endswith('/hook-canary/src/main.m'):word=str(old_source)
 args.append(word)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
r=subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
(stage/'build7-native-macros.txt').write_text(r.stdout)
old_length=int(re.search(r'^#define CJ_ARENA_LENGTH (\d+)$',r.stdout,re.M)[1]);assert old_length==65536
with zipfile.ZipFile(out/'CelesteJITGame-unsigned.ipa') as z:
 prefix='Payload/CelesteJITGame.app/'
 binary=z.read(prefix+'CelesteJITGame');script=z.read(prefix+'celeste-jit-probe.js');info=json.loads(z.read(prefix+'BuildInfo.json'))
spec=importlib.util.spec_from_file_location('hook_builder',source/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
compiled=builder.read_compiled_protocol(binary);assert compiled==info['compiled_protocol']==json.loads(sample.read_text())['compiled_protocol']
assert compiled['bytes_per_arena']==info['bytes_per_arena']==16777216
script_path=stage/'packaged-script.js';script_path.write_bytes(script)
node=subprocess.check_output(['which','node'],text=True).strip()
r=subprocess.run([node,str(source.parent/'hook-canary/tests/request_protocol.test.cjs'),str(sample),str(script_path),str(old_length)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(stage/'request-script-test.log').write_text(r.stdout)
assert r.returncode==0,r.stdout
result=json.loads(r.stdout);result.update(build_id=a.build_id,ipa_sha256=sha(out/'CelesteJITGame-unsigned.ipa'),
 packaged_script_sha256=hashlib.sha256(script).hexdigest(),native_request_sample_sha256=sha(sample),
 preserved_build7_source_sha256=sha(old_source),build7_resolved_length=old_length,compiled_protocol=compiled,
 old_preprocessor_command=args,source_sha256={str(f.relative_to(root)):sha(f) for f in [source/'src/main.m',source.parent/'hook-canary/src/CJHookProtocol.h',source.parent/'hook-canary/tests/request_protocol.test.cjs',source/'tests/check_request_protocol.py']})
(out/'request-protocol-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
