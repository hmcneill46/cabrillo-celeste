#!/usr/bin/env python3
"""Bind the final native installer IPA to its new gates and unchanged accepted game."""
import argparse,hashlib,importlib.util,json,os,plistlib,re,subprocess,zipfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit'
p=argparse.ArgumentParser();p.add_argument('--build-id',default='launcher-dependencies-20260912-25');args=p.parse_args();A=R/'artifacts/ios-jit'/args.build_id
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def matches(values):
 for name,digest in values.items():assert sha(R/name)==digest,name
r=read(A/'build-receipt.json');base=read(R/'artifacts/ios-jit/launcher-backbuffer-20260912-24/build-receipt.json');ipa=A/'CelesteJITEverest-unsigned.ipa'
assert r['version']=='0.13.0' and r['build_number']=='25' and not r['simulator']
assert sha(ipa)==r['ipa_sha256'] and ipa.stat().st_size<50000000
spec=importlib.util.spec_from_file_location('builder',S/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
with zipfile.ZipFile(ipa) as z:
 assert z.testzip() is None
 names=z.namelist();pre='Payload/CelesteJITEverest.app/'
 assert all(n.startswith(pre) for n in names)
 builder.validate_payload_members((n,z.read(n)) for n in names)
 assert not any('.dSYM/' in n or '_CodeSignature' in n or n.endswith('.mobileprovision') or '/Content/' in n or 'InstallerFixtures/' in n for n in names)
 assert [n for n in names if n.endswith('.zip')]==[pre+'CJITCodeCanary-v1.0.0.zip']
 info=plistlib.loads(z.read(pre+'Info.plist'));assert info['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.everest'
 assert info['CFBundleVersion']=='25' and info['CFBundleShortVersionString']=='0.13.0'
 assert 'UIInterfaceOrientationPortrait' in info['UISupportedInterfaceOrientations']
 build=json.loads(z.read(pre+'BuildInfo.json'));binary=z.read(pre+'CelesteJITEverest')
 assert all(r[k]==v for k,v in build.items())
 assert hashlib.sha256(binary).hexdigest()==r['executable_sha256']
 assert b'--launcher-install-ui-fixture' not in binary and b'mods.example.org' not in binary
 assert builder.read_compiled_protocol(binary)==r['compiled_protocol']==base['compiled_protocol']
 assert r['bytes_per_arena']==268435456 and r['aot_disabled'] and r['interpreter_disabled']
 for filename,key in [('CompatibilityDownloads.json','compatibility_downloads_sha256'),('celeste-jit-probe.js','script_template_sha256'),('FMOD-LICENSE.txt','fmod_license_sha256'),('SJReleaseManifest.json','sj_release_manifest_sha256'),('GameContentManifest.json','game_content_manifest_sha256')]:assert hashlib.sha256(z.read(pre+filename)).hexdigest()==r[key]
 for key in ['framework_assembly_sha256','everest_assembly_sha256']:
  assert r[key]==base[key]
  for n,d in r[key].items():assert hashlib.sha256(z.read(pre+'Managed/'+n)).hexdigest()==d
 assert len(r['framework_assembly_sha256'])==168
 assert not any('InstallTests' in n or 'RealUpdateTests' in n or 'FnaGraphicsTests' in n for n in names)
 assert r['bundled_content_files']==0 and r['private_prepared_game_il'] and not r['private_owner_content']
 assert hashlib.sha256(z.read(pre+'Managed/orig/Celeste.exe')).hexdigest()=='fd73f8a2311fa5737ded550cbad4b75c85b7686b36432f59185e940fcb65fcfe'
 assert r['game_content_aggregate_sha256']==base['game_content_aggregate_sha256']
 pins=json.loads(z.read(pre+'CompatibilityDownloads.json'))
 assert sorted(m['name'] for p in pins for m in p['modules'])==['CollabUtils2','FemtoHelper','GravityHelper']
 for pin in pins:
  expected=next(v for v in r['mod_download_manifest'].values() if v['sha256']==pin['pinnedSHA256'])
  assert pin['url']==expected['url'] and pin['bytes']==expected['bytes'] and pin['hashes']==[]
for key in ['source_sha256','native_library_sha256','launcher_native_libraries']:matches(r[key])
for key in ['framework_assembly_sha256','everest_assembly_sha256','native_library_sha256','runtime_config_sha256','graphics_native_receipt_sha256','mono_compatibility_receipt_sha256','ios_support','script_template_sha256']:assert r[key]==base[key],key
assert 'LC_CODE_SIGNATURE' not in (A/'macho-load-commands.txt').read_text()
assert not any('CJ_HOOK_HOST_TEST' in word or 'CJ_GRAPHICS_HOST_TEST' in word for cmd in r['build_commands'] for word in cmd)
# Accepted native bridge sources that should not change in this product step.
for name in ['CJGraphicsManaged.m','CJGraphicsPlatform.m','CJHookCodeArena.c','CJHookNative.c','CJSession.c','CJContentImport.m','CJFrameMetrics.c','CJEventStore.m','VMRange.c','VMRangeDarwin.c']:
 assert sha(S/'src'/name)==sha(R/'experiments/ios-jit/launcher-backbuffer/src'/name),name
exports=set(read(B/'launcher-dependencies'/args.build_id/'native-export-table.json'));internal=set();lua=set()
for name in ['Celeste.dll','FNA.dll','KeraLua.dll']:
 text=subprocess.check_output(['monodis','--implmap',str(B/'launcher-backbuffer-managed'/name)],text=True)
 internal.update(re.findall(r'\((\w+) __Internal\)$',text,re.M));lua.update(re.findall(r'\((\w+) lua54\)$',text,re.M))
assert len(internal)>=1294 and internal<=exports and len(lua)>=80 and lua<=exports
# All new native source gates bind to their actual tested sources.
gates={}
for path in [B/'launcher-dependencies-install-tests/receipt.json',B/'launcher-dependencies-real-updates/receipt.json',B/'launcher-dependencies-ui-tests/receipt.json',B/'launcher-dependencies-validation/host-updated-paint/receipt.json']:
 g=read(path);assert g['status'].startswith('PASS_');matches(g.get('source_sha256',{}));gates[str(path.relative_to(R))]={'status':g['status'],'sha256':sha(path)}
 for filename,d in g.get('results',{}).items():assert sha(path.parent/filename)==d
ui=read(B/'launcher-dependencies-ui-tests/receipt.json');sim=R/'artifacts/ios-jit'/(args.build_id+'-simulator')/'CelesteJITEverest.app'
assert sha(sim/'BuildInfo.json')==ui['simulator_build_info_sha256'] and sha(sim/'CelesteJITEverest')==ui['simulator_executable_sha256']
assert read(sim/'BuildInfo.json')['source_sha256']==r['source_sha256']
smoke=B/'launcher-dependencies'/(args.build_id+'-simulator')/'smoke/receipt.json';assert read(smoke)['status'].startswith('PASS_');gates[str(smoke.relative_to(R))]={'status':read(smoke)['status'],'sha256':sha(smoke)}
host=read(B/'launcher-dependencies-validation/host-updated-paint/receipt.json')
assert host['real_updated_mod_selection'] and host['paint_regression'] and host['frost_render_regression'] and host['fixture_sha256']==r['game_fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
# Complete original backbuffer and session matrices are inherited by identity.
inherited={}
for path in [R/'artifacts/ios-jit/launcher-backbuffer-20260912-24/package-validation.json',R/'docs/ios-jit/BUILD_24_GRAPHICS_ACCEPTANCE_EVIDENCE.json']:
 g=read(path);assert g['status'].startswith('PASS_');inherited[str(path.relative_to(R))]={'sha256':sha(path),'status':g['status']}
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
symbol=next(A.glob('*.dSYM'));uuid=subprocess.check_output(['xcrun','dwarfdump','--uuid',str(symbol)],env=env,text=True).split(' (')[0]
assert uuid==r['executable_uuid']
result=dict(status='PASS_BUILD25_UNSIGNED_PACKAGE_AND_NATIVE_INSTALL_GATES',build_id=args.build_id,ipa_sha256=r['ipa_sha256'],ipa_bytes=ipa.stat().st_size,executable_uuid=r['executable_uuid'],source_count=len(r['source_sha256']),native_imports=len(internal),lua_imports=len(lua),validation_receipts=gates,inherited_validation=inherited,accepted_build24_game_runtime_renderer_identical=True,no_simulator_fixture_in_device_binary=True,game_content_bundled=False,phone_build25_acceptance=False,script_template_sha256=r['script_template_sha256'])
(A/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
