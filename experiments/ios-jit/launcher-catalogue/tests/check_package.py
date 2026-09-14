#!/usr/bin/env python3
"""Validate build28 bytes, browser gates and unchanged physically accepted27 runtime."""
import argparse,hashlib,importlib.util,json,os,plistlib,re,subprocess,zipfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit'
p=argparse.ArgumentParser();p.add_argument('--build-id',default='launcher-catalogue-20260913-28');a=p.parse_args();A=R/'artifacts/ios-jit'/a.build_id
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def matches(values):
 for name,digest in values.items():assert sha(R/name)==digest,name
r=read(A/'build-receipt.json');accepted=R/'artifacts/ios-jit/launcher-runtime-20260913-27';base=read(accepted/'build-receipt.json')
ipa=A/'CelesteJITEverest-unsigned.ipa'
assert r['version']=='0.15.0' and r['build_number']=='28' and not r['simulator']
assert sha(ipa)==r['ipa_sha256'] and ipa.stat().st_size<50000000
matches(base['source_sha256']);assert sha(accepted/'CelesteJITEverest-unsigned.ipa')==base['ipa_sha256']
assert read(accepted/'package-validation.json')['status']=='PASS_BUILD27_UNSIGNED_PACKAGE_AND_EVEREST_UPGRADE_GATES'
spec=importlib.util.spec_from_file_location('builder',S/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
with zipfile.ZipFile(ipa) as z:
 assert z.testzip() is None
 names=z.namelist();pre='Payload/CelesteJITEverest.app/'
 builder.validate_payload_members((n,z.read(n)) for n in names)
 assert all(n.startswith(pre) for n in names)
 assert not any('.dSYM/' in n or '_CodeSignature' in n or n.endswith('.mobileprovision') or '/Content/' in n or 'Fixtures/' in n for n in names)
 assert [n for n in names if n.endswith('.zip')]==[pre+'CJITCodeCanary-v1.0.0.zip']
 info=plistlib.loads(z.read(pre+'Info.plist'));assert info['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.everest'
 assert info['CFBundleVersion']=='28' and info['CFBundleShortVersionString']=='0.15.0'
 assert 'UIInterfaceOrientationPortrait' in info['UISupportedInterfaceOrientations']
 build=json.loads(z.read(pre+'BuildInfo.json'));binary=z.read(pre+'CelesteJITEverest')
 assert all(r[k]==v for k,v in build.items());assert hashlib.sha256(binary).hexdigest()==r['executable_sha256']
 for marker in [b'--catalogue-ui-fixture',b'--catalogue-ui-offline',b'--launcher-install-ui-fixture',b'mods.example.org',b'Catalogue test fixture',b'catalogue-fixture']:
  assert marker not in binary,marker
 assert builder.read_compiled_protocol(binary)==r['compiled_protocol']==base['compiled_protocol']
 assert r['bytes_per_arena']==268435456 and r['aot_disabled'] and r['interpreter_disabled']
 for key in ['framework_assembly_sha256','everest_assembly_sha256']:
  assert r[key]==base[key],key
  for name,digest in r[key].items():assert hashlib.sha256(z.read(pre+'Managed/'+name)).hexdigest()==digest
 assert len(r['framework_assembly_sha256'])==168 and len(r['everest_assembly_sha256'])==33
 with zipfile.ZipFile(accepted/'CelesteJITEverest-unsigned.ipa') as old:
  assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in names if n.startswith(pre+'Managed/')}=={n:hashlib.sha256(old.read(n)).hexdigest() for n in old.namelist() if n.startswith(pre+'Managed/')}
 for filename,key in [('RuntimeCompatibleReleases.json','runtime_compatible_releases_sha256'),('CompatibilityDownloads.json','compatibility_downloads_sha256'),('celeste-jit-probe.js','script_template_sha256'),('GameContentManifest.json','game_content_manifest_sha256')]:assert hashlib.sha256(z.read(pre+filename)).hexdigest()==r[key]==base[key]
 assert r['bundled_content_files']==0 and r['private_prepared_game_il'] and not r['private_owner_content']
for key in ['source_sha256','native_library_sha256','launcher_native_libraries']:matches(r[key])
for key in ['native_library_sha256','runtime_config_sha256','graphics_native_receipt_sha256','mono_compatibility_receipt_sha256','ios_support','script_template_sha256','reflection_flags','bundled_runtime_identity','game_receipt_sha256']:
 assert r[key]==base[key],key
for path in (S/'src').iterdir():
 if path.is_file() and path.name!='main.m':assert sha(path)==sha(R/'experiments/ios-jit/launcher-runtime/src'/path.name),path.name
assert 'LC_CODE_SIGNATURE' not in (A/'macho-load-commands.txt').read_text()
assert not any('CJ_HOOK_HOST_TEST' in w or 'CJ_GRAPHICS_HOST_TEST' in w for cmd in r['build_commands'] for w in cmd)
gates={}
for path in [B/'launcher-catalogue-install-tests/receipt.json',B/'launcher-catalogue-tests/receipt.json',B/'launcher-catalogue-ui-tests/receipt.json',B/'launcher-catalogue-browser-ui/receipt.json',B/'launcher-catalogue-host-test/receipt.json']:
 g=read(path);assert g['status'].startswith('PASS_');matches(g.get('source_sha256',{}))
 for name,digest in g.get('results',{}).items():assert sha(path.parent/name)==digest
 gates[str(path.relative_to(R))]={'status':g['status'],'sha256':sha(path)}
sim=R/'artifacts/ios-jit'/(a.build_id+'-simulator')/'CelesteJITEverest.app';sr=read(sim/'BuildInfo.json')
assert sr['source_sha256']==r['source_sha256']
for path in [B/'launcher-catalogue-ui-tests/receipt.json',B/'launcher-catalogue-browser-ui/receipt.json']:
 g=read(path);assert g['simulator_build_info_sha256']==sha(sim/'BuildInfo.json') and g['simulator_executable_sha256']==sha(sim/'CelesteJITEverest')
smoke=B/'launcher-catalogue'/(a.build_id+'-simulator')/'smoke/receipt.json';assert read(smoke)['status'].startswith('PASS_')
gates[str(smoke.relative_to(R))]={'status':read(smoke)['status'],'sha256':sha(smoke)}
host=read(B/'launcher-catalogue-host-test/receipt.json')
assert host['fixture_sha256']==r['game_fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
assert host['reflection_flags_checks']==30 and host['normal_selection_test'] and host['session_contract_checks']==37
log=(B/'launcher-catalogue-host-test/run.log').read_text();assert sha(B/'launcher-catalogue-host-test/run.log')==host['log_sha256']
for marker in ['everest_selection_module_verified Cateline 0.1.0;', 'everest_selection_module_verified memorialHelper 1.0.4;', 'phase=after_resume','runtime_identity_pass version=1.6531.0-cjit-d72e94f']:assert marker in log,marker
live=read(B/'launcher-catalogue-tests/live-results.json');assert live['status']=='PASS_LIVE_CATALOGUE_TO_VERIFIED_INSTALL' and len(live['listResponses'])==5
assert not live['index'].get('cached') and live['skinReport']['applicationState']=='applied'
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
symbol=next(A.glob('*.dSYM'));uuid=subprocess.check_output(['xcrun','dwarfdump','--uuid',str(symbol)],env=env,text=True).split(' (')[0];assert uuid==r['executable_uuid']
result=dict(status='PASS_BUILD28_UNSIGNED_PACKAGE_CATALOGUE_AND_RUNTIME_GATES',build_id=a.build_id,ipa_sha256=sha(ipa),ipa_bytes=ipa.stat().st_size,executable_uuid=r['executable_uuid'],source_count=len(r['source_sha256']),validation_receipts=gates,accepted27_managed_native_renderer_protocol_unchanged=True,managed_assemblies=201,no_fixture_transport_in_device=True,phone_build28_acceptance=False,game_content_bundled=False)
(A/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
