#!/usr/bin/env python3
"""Validate the private full-SJ candidate against actual payload and test identities."""
import argparse,hashlib,importlib.util,json,plistlib,re,subprocess,zipfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='launcher-session-20260912-23');a=p.parse_args()
O=R/'artifacts/ios-jit'/a.build_id;stage=B/'launcher-session'/a.build_id
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def matches(mapping):
 for name,digest in mapping.items():assert sha(R/name)==digest,name
r=read(O/'build-receipt.json');managed=read(B/'launcher-session-managed/receipt.json')
spec=importlib.util.spec_from_file_location('builder',S/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
ipa=O/'CelesteJITEverest-unsigned.ipa';own='CJITCodeCanary-v1.0.0.zip'
with zipfile.ZipFile(ipa) as z:
 assert z.testzip() is None
 prefix='Payload/CelesteJITEverest.app/';names=z.namelist()
 builder.validate_payload_members((n,z.read(n)) for n in names)
 assert all(n.startswith(prefix) for n in names)
 assert not any('_CodeSignature' in n or n.endswith('.mobileprovision') or 'Microsoft.iOS' in n for n in names)
 assert [n for n in names if n.endswith('.zip')]==[prefix+own]
 assert hashlib.sha256(z.read(prefix+own)).hexdigest()==r['mod_zip_files'][own]['sha256']=='d30cc5b1d28d7821764fb18a35a182aa808cee56f4d0c4c778d9fa7bd4ef450b'
 info=plistlib.loads(z.read(prefix+'Info.plist'))
 assert info['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.everest'
 assert info['CFBundleVersion']=='23' and info['CFBundleShortVersionString']=='0.12.0'
 assert 'UIInterfaceOrientationPortrait' in info['UISupportedInterfaceOrientations']
 binary=z.read(prefix+'CelesteJITEverest');build=json.loads(z.read(prefix+'BuildInfo.json'))
 assert builder.read_compiled_protocol(binary)==build['compiled_protocol']
 assert build['bytes_per_arena']==268435456 and build['aot_disabled'] and build['interpreter_disabled']
 assert all(r[k]==v for k,v in build.items())
 assert hashlib.sha256(binary).hexdigest()==r['executable_sha256']
 for filename,key in [('celeste-jit-probe.js','script_template_sha256'),('FMOD-LICENSE.txt','fmod_license_sha256'),('SJReleaseManifest.json','sj_release_manifest_sha256')]:
  assert hashlib.sha256(z.read(prefix+filename)).hexdigest()==r[key]
 for key in ('framework_assembly_sha256','everest_assembly_sha256'):
  for name,digest in r[key].items():assert hashlib.sha256(z.read(prefix+'Managed/'+name)).hexdigest()==digest
 assert len(r['framework_assembly_sha256'])==168
 assert r['everest_assembly_sha256']['CelesteJITEverest.dll']==r['game_fixture_sha256']
 assert r['everest_assembly_sha256']['FNA.dll']==r['fna_assembly_sha256']
 assert 'Celeste.Mod.mm.dll' in r['everest_assembly_sha256']
 assert hashlib.sha256(z.read(prefix+'Managed/orig/Celeste.exe')).hexdigest()=='fd73f8a2311fa5737ded550cbad4b75c85b7686b36432f59185e940fcb65fcfe'
 raw=z.read(prefix+'GameContentManifest.json');assert hashlib.sha256(raw).hexdigest()==r['game_content_manifest_sha256']
 content=json.loads(raw);aggregate=hashlib.sha256();assert len(content['files'])==1216
 assert not any(n.startswith(prefix+'Content/') for n in names)
 assert build['bundled_content_files']==0 and not build['private_owner_content']
 assert build['private_prepared_game_il'] and build['persistent_content_import'] and ipa.stat().st_size<50000000
 for item in content['files']:aggregate.update(item['path'].encode()+b'\0'+str(item['bytes']).encode()+b'\0'+item['sha256'].encode()+b'\n')
 assert aggregate.hexdigest()==content['aggregate_sha256']==r['game_content_aggregate_sha256']=='30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46'
assert sha(ipa)==r['ipa_sha256']
for mapping in [r['source_sha256'],r['native_library_sha256'],managed['source_sha256']]:matches(mapping)
assert not any('CJ_HOOK_HOST_TEST' in word or 'CJ_GRAPHICS_HOST_TEST' in word for cmd in r['build_commands'] for word in cmd)
assert 'LC_CODE_SIGNATURE' not in (O/'macho-load-commands.txt').read_text()
exports=set(read(stage/'native-export-table.json'));internal=set();lua=set()
for name in ['Celeste.dll','FNA.dll','KeraLua.dll']:
 imports=subprocess.check_output(['monodis','--implmap',str(B/'launcher-session-managed'/name)],text=True)
 internal.update(re.findall(r'\((\w+) __Internal\)$',imports,re.M));lua.update(re.findall(r'\((\w+) lua54\)$',imports,re.M))
assert len(internal)>=1294 and internal<=exports,sorted(internal-exports)
assert len(lua)>=80 and lua<=exports,sorted(lua-exports)
assert 'FMOD_DSP_GetCPUUsage' not in internal and 'FNA3D_CJIT_EndCallback' in internal
pins=read(S/'sj-pins.json');original=read(B/'sj-lobby-inputs/receipt.json');mods=read(B/'sj-lobby-mods/receipt.json')
assert len(pins['nodes'])==len(r['original_helper_files'])==52 and len(r['mod_zip_files'])==53
assert sum(n['zipBytes'] for n in pins['nodes'])==1237284560
assert sha(S/'sj-pins.json')==r['sj_release_manifest_sha256']
assert r['original_helper_files']==original['files'] and mods['files']==r['mod_zip_files']
for name,row in r['mod_zip_files'].items():
 file=B/'sj-lobby-mods'/name;assert sha(file)==row['sha256'] and file.stat().st_size==row['bytes']
 with zipfile.ZipFile(file) as z:assert any(n.lower() in ['everest.yaml','everest.yml'] for n in z.namelist())
 if name==own:assert sha(O/name)==row['sha256'] and r['mod_download_manifest'][name]['url'] is None
 else:
  pin=next(n for n in pins['nodes'] if n['zipSha256']==row['sha256'])
  assert pin['zipBytes']==row['bytes'] and r['mod_download_manifest'][name]['url']==pin['publicUrl']
  assert not (O/name).exists(),'Large original ZIP must not be copied into the small handoff kit.'
host=read(B/'launcher-session-validation/host-full-sj/receipt.json')
assert host['fixture_sha256']==r['game_fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
matches(host['source_sha256']);matches(host['input_sha256'])
assert host['callback_autorelease_pools'] and host['status']=='PASS_HOST_REAL_SJ_LOBBY_BING_SAVES_AND_RESUME'
assert host['frost_render_regression'] and host['graphics_contract_checks']>=30
assert host['graphics_regression_source_sha256']==sha(S/'tests/FnaGraphicsTests.cs')
assert not any(n.endswith('FnaGraphicsTests.dll') for n in names)
fna=managed['fna_graphics_compatibility'];assert fna==r['fna_graphics_compatibility']
assert fna['input_sha256']=='dfd000f1a1eff08d41451099c63a9de9363047a6c0025812fb9ff19d8d53ed6d'
assert fna['output_sha256']==r['fna_assembly_sha256'] and fna['unchanged_existing_methods']==5243
assert fna['unchanged_fields']==4469 and not fna['native_renderer_changed'] and not fna['mod_zip_changes']
assert all(host[k] for k in ['original_sj_lobby_and_bing','original_femto_particle_values','original_sj_music_playing','all_52_modules_verified','gravity_optional_transform','gravity_optional_absence_handled'])
assert sha(B/'launcher-session-validation/host-full-sj/run.log')==host['log_sha256']
native=read(O/'graphics-native-receipt.json')
assert sha(O/'graphics-native-receipt.json')==r['graphics_native_receipt_sha256']
assert native['patch_sha256']==r['graphics_native_patch_sha256']==host['native_patch_sha256']
assert native['ios_archive_sha256']==r['native_library_sha256'][native['ios_archive']]
assert native['host_library_sha256']==host['desktop_native_sha256']['libFNA3D.0.dylib'];matches(native['source_sha256'])
compat=read(O/'mono-compatibility-receipt.json');inherited=read(B/'sj-budget-runtime/receipt.json')
assert sha(O/'mono-compatibility-receipt.json')==r['mono_compatibility_receipt_sha256']==host['mono_compatibility_receipt_sha256']
assert compat['targets']['ios']['sha256']==r['native_library_sha256'][compat['targets']['ios']['archive']]
assert compat['targets']['host']['sha256']==host['mono_compatibility_archive_sha256']
assert compat['inherited_receipt_sha256']==sha(B/'sj-budget-runtime/receipt.json')
assert sha(S.parent/'sj-lobby/build_runtime.py')==compat['builder_sha256'] and sha(S/'src/cjit-bfi-policy.h')==compat['policy_header_sha256']
assert sha(B/'sj-lobby-runtime/mono8-femto-beforefieldinit.patch')==compat['patch_sha256']
for target,record in compat['targets'].items():
 assert record['unchanged_members']==256 and record['replaced_members']==['method-to-ir.c.o','mini-runtime.c.o','mini.c.o','mono-codeman.c.o']
 assert record['original_sha256']==inherited['targets'][target]['sha256']
 assert sha(R/record['archive'])==record['sha256']
 for name,obj in record['objects'].items():assert sha(B/'sj-lobby-runtime'/name)==obj['patched_source_sha256']
assert r['mono_ordinary_chunk_minimum_bytes']==16384
assert host['code_manager_model']==dict(page_bytes=16384,granule_bytes=16384,bind_room_divisor=4,minimum_chunk_bytes=16384)
assert inherited['inherited_visibility_receipt_sha256']==r['inherited_mono_visibility_receipt_sha256']
assert managed['mono8_utils_compatibility']==r['mono8_utils_compatibility']
assert r['everest_assembly_sha256']['MonoMod.Utils.dll']==managed['mono8_utils_compatibility']['output_sha256']
receipts={}
for directory in ['sj-lobby-bfi-tests','sj-lobby-collab-tests','sj-lobby-chunk-tests','sj-lobby-capacity-tests','sj-lobby-vm-tests','sj-lobby-store-tests','sj-lobby-vmlog-tests']:
 path=B/directory/'receipt.json';test=read(path);assert test['status'].startswith('PASS_')
 for key in ['source_sha256','input_sha256','files']:
  if key in test:matches(test[key])
 receipts[directory]=sha(path)
bfi=read(B/'sj-lobby-bfi-tests/receipt.json');assert bfi['patched_cases']==13 and 'unrelated_assembly' in bfi['results']
assert bfi['results']['1']['archive_sha256']==host['mono_compatibility_archive_sha256']
collab=read(B/'sj-lobby-collab-tests/receipt.json');assert collab['mono_archive_sha256']==host['mono_compatibility_archive_sha256']
for name in ['GravityOptionalIntegration.cs','CollabOptionalIntegration.cs','MonoTypeDiscovery.cs','ContentLibrary.cs','ContentStore.cs']:
 assert (S/'managed'/name).read_bytes()==(S.parent/'sj-lobby/managed'/name).read_bytes()
for i,record in enumerate(collab['results']):
 assert sha(R/record['input_path'])==record['input_sha256'];assert sha(B/'sj-lobby-collab-tests'/(str(i)+'.log'))==record['log_sha256']
 assert 'checks=1073 methods=1062' in (B/'sj-lobby-collab-tests'/(str(i)+'.log')).read_text()
capacity=read(B/'sj-lobby-capacity-tests/receipt.json')
assert capacity['status']=='PASS_BUILD15_EXACT_FAILURE_AND_BUILD19_DEVICE_SIZED_ALIAS_REPLAY'
assert capacity['budget_bytes']==536870912 and capacity['page_bytes']==16384 and capacity['full_traces']==2
assert capacity['extra_native_reserve_bytes']==16777216 and capacity['host_chunks']>10000
assert r['vm_range_policy']=='intersected_os_pages_v1' and r['vm_range_source_sha256']==sha(S/'src/VMRange.c')
assert {word for cmd in r['build_commands'] for word in cmd if word.endswith('/VMRange.c')}=={str(S/'src/VMRange.c')}
previous=read(R/'artifacts/ios-jit/sj-memory-check-20260912-18/build-receipt.json')
assert previous['framework_assembly_sha256']==r['framework_assembly_sha256']
assert {k:v for k,v in previous['everest_assembly_sha256'].items() if k not in ['CelesteJITEverest.dll','CelesteIOS.dll','FNA.dll','MonoMod.Utils.dll']}=={k:v for k,v in r['everest_assembly_sha256'].items() if k not in ['CelesteJITEverest.dll','CelesteIOS.dll','FNA.dll','MonoMod.Utils.dll']}
assert {k:v for k,v in previous['native_library_sha256'].items() if not k.endswith('/libmonosgen-2.0.a')}=={k:v for k,v in r['native_library_sha256'].items() if not k.endswith('/libmonosgen-2.0.a')}
launcher_native=read(O/'launcher-native-receipt.json');matches(launcher_native['source_sha256']);matches(launcher_native['libraries'])
assert sha(O/'launcher-native-receipt.json')==r['launcher_native_receipt_sha256']
assert r['launcher_native_libraries']==launcher_native['libraries'] and r['diagnostics_policy']=='bounded_v1'
for name in ['host-title-quit','host-busy-quit','host-normal-reload']:
 test=read(B/'launcher-session-validation'/name/'receipt.json')
 assert test['fixture_sha256']==r['game_fixture_sha256'] and test['normal_selection_test']
 assert sha(B/'launcher-session-validation'/name/'run.log')==test['log_sha256']
 assert test['status']=='PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME'
 receipts[name]=sha(B/'launcher-session-validation'/name/'receipt.json')
for name,path in [('fna-graphics',B/'launcher-reflection-fna/result.json'),('mod-library',B/'launcher-session-mod-library-tests/result.json'),('native-services',B/'launcher-session-native-services-tests/result.json'),('ui',B/'launcher-session-ui-tests/receipt.json')]:
 test=read(path);assert test['status'].startswith('PASS_');receipts[name]=sha(path)
fna_tests=read(B/'launcher-reflection-fna/result.json');matches(fna_tests['source_sha256']);matches(fna_tests['original_zip_sha256'])
assert fna_tests['fna_after_sha256']==r['fna_assembly_sha256'] and fna_tests['graphics_contract_checks']==33
sim_app=R/'artifacts/ios-jit/launcher-session-20260912-23-simulator/CelesteJITEverest.app'
ui=read(B/'launcher-session-ui-tests/receipt.json')
assert sha(sim_app/'BuildInfo.json')==ui['simulator_build_info_sha256']
assert sha(sim_app/'CelesteJITEverest')==ui['simulator_executable_sha256']
assert read(sim_app/'BuildInfo.json')['source_sha256']==r['source_sha256']
assert 'PASS_REAL_DESKTOP_MENU_QUIT_WITHOUT_SAVE_SLOT' in (B/'launcher-session-validation/host-title-quit/run.log').read_text()
assert 'PASS_REAL_REPEATED_QUIT_DURING_QUEUED_MOD_SAVE' in (B/'launcher-session-validation/host-busy-quit/run.log').read_text()
assert 'existing=True' in (B/'launcher-session-validation/host-normal-reload/run.log').read_text()
literal=read(B/'launcher-reflection-literal-tests/result.json');matches(literal['source_sha256'])
assert literal['status']=='PASS_ACTUAL_MONO_LITERAL_FIELDS_AND_ORIGINAL_FAILURE' and literal['results']['1']['checks']==137
assert literal['patch']['output_sha256']==r['everest_assembly_sha256']['MonoMod.Utils.dll']
assert literal['patch']==managed['mono8_utils_compatibility']['literal_fields']
assert literal['runtime_archive_sha256']==host['mono_compatibility_archive_sha256']
assert not any(n.endswith(('LiteralFieldTests.dll','LiteralFieldEmitter.dll')) for n in names)
receipts['literal-fields']=sha(B/'launcher-reflection-literal-tests/result.json')
# Prior Paint coverage is inherited only for the unchanged runtime/FNA/Utils
# inputs; it is not presented as execution of the new session adapter.
for case in ['host-paint-original','host-paint-fixed','host-paint-reload']:
 t=read(B/'launcher-reflection-validation'/case/'receipt.json');matches(t['source_sha256']);matches(t['input_sha256'])
 assert t['paint_regression'] and t['fna_sha256']==r['fna_assembly_sha256']
 assert t['mono_compatibility_archive_sha256']==host['mono_compatibility_archive_sha256']
 assert sha(B/'launcher-reflection-validation'/case/'run.log')==t['log_sha256']
 if case!='host-paint-original':assert t['monomod_utils_sha256']==r['everest_assembly_sha256']['MonoMod.Utils.dll']
 receipts['inherited-build22-'+case]=sha(B/'launcher-reflection-validation'/case/'receipt.json')
support=r['ios_support']
assert support==dict(id='CelesteIOS',version='1.0.0',abi=1,required=True,sha256=r['everest_assembly_sha256']['CelesteIOS.dll'])
assert support['sha256']==host['support_module_sha256']
assert not any(n.endswith(('SessionIntegrationTests.dll','LiteralFieldTests.dll','LiteralFieldEmitter.dll')) for n in names)
contract=read(B/'launcher-session-validation/session-contract.json');matches(contract['source_sha256'])
assert contract['status']=='PASS_SESSION_ABI_ORDER_CONCURRENT_QUIT_AND_CLOSED_LIFETIME'
assert r['session_protocol_source_sha256']==sha(S/'src/CJSession.c')
receipts['session-contract']=sha(B/'launcher-session-validation/session-contract.json')
for case in ['host-title-quit','host-busy-quit','host-normal-reload','host-full-sj']:
 t=read(B/'launcher-session-validation'/case/'receipt.json');matches(t['source_sha256']);matches(t['input_sha256'])
 assert t['support_module_sha256']==support['sha256'] and t['session_contract_checks']>=30
 log=(B/'launcher-session-validation'/case/'run.log').read_text()
 assert 'GAME game_shutdown_stage_started stage=8' in log and 'graphics_main_thread_detached' in log
 assert 'game_checks_pass' in log and 'game_checks_incomplete' not in log
 receipts[case]=sha(B/'launcher-session-validation'/case/'receipt.json')
full_quit=read(B/'launcher-session-validation/host-full-quit/receipt.json')
assert full_quit['status']=='PASS_FULL_SJ_MOD_SET_NORMAL_QUIT_QUEUED_SAVE_AND_RELOAD'
matches(full_quit['source_sha256']);matches(full_quit['input_sha256'])
assert full_quit['fixture_sha256']==r['game_fixture_sha256'] and full_quit['support_module_sha256']==support['sha256']
assert sha(B/'launcher-session-validation/host-full-quit/run.log')==full_quit['log_sha256']
receipts['full-mod-set-normal-quit']=sha(B/'launcher-session-validation/host-full-quit/receipt.json')
assert ui['native_closing_presentation'] and ui['closing_state_is_simulator_fixture']
result=dict(status='PASS_BUILD23_IOS_SUPPORT_QUIT_SAVE_AND_LAUNCHER_GATES' ,ipa_bytes=ipa.stat().st_size,ipa_sha256=sha(ipa),adapter_sha256=r['game_fixture_sha256'],native_internal_imports=len(internal),native_lua_imports=len(lua),all_declared_game_fna_lua_static_imports_resolve=True,bundled_content_files=0,import_manifest_files=1216,import_content_bytes=r['game_content_bytes'],original_sj_downloads=52,original_sj_zip_bytes=1237284560,bundled_own_mods=1,framework_dlls=168,everest_managed_dlls=len(r['everest_assembly_sha256']),private_prepared_game_il=True,public_original_il_importer_complete=False,debug_symbols_outside_ipa=True,signature=False,provisioning_profile=False,accepted_renderer_reused=True,code_budget_bytes=536870912,mono_chunk_floor_bytes=16384,host_adapter_bytes_match=True,test_receipt_sha256=receipts,original_mod_zips_preserved=True,private_owner_kit=True,physical_full_sj_tested_in_build19=True,physical_build23_tested=False,required_support_module=support,normal_quit_tested_on_host=True,queued_mod_saves_tested=True,inherited_paint_coverage_build22=True,current_adapter_paint_tested=False,native_launcher_and_mod_selection=True,normal_play=True,portrait_launcher=True,metrics="callback FPS and callback wall time; not GPU timing",bounded_diagnostics=True)
(O/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
