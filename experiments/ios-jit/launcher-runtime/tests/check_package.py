#!/usr/bin/env python3
"""Bind the final native installer IPA to its new gates and pinned rebuilt Everest and accepted renderer/runtime."""
import argparse,hashlib,importlib.util,json,os,plistlib,re,subprocess,zipfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit'
p=argparse.ArgumentParser();p.add_argument('--build-id',default='launcher-runtime-20260913-27');args=p.parse_args();A=R/'artifacts/ios-jit'/args.build_id
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
def matches(values):
 for name,digest in values.items():assert sha(R/name)==digest,name
r=read(A/'build-receipt.json');base=read(R/'artifacts/ios-jit/launcher-backbuffer-20260912-24/build-receipt.json');ipa=A/'CelesteJITEverest-unsigned.ipa'
assert r['version']=='0.14.0' and r['build_number']=='27' and not r['simulator']
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
 assert info['CFBundleVersion']=='27' and info['CFBundleShortVersionString']=='0.14.0'
 assert 'UIInterfaceOrientationPortrait' in info['UISupportedInterfaceOrientations']
 build=json.loads(z.read(pre+'BuildInfo.json'));binary=z.read(pre+'CelesteJITEverest')
 assert all(r[k]==v for k,v in build.items())
 assert hashlib.sha256(binary).hexdigest()==r['executable_sha256']
 assert b'--launcher-install-ui-fixture' not in binary and b'mods.example.org' not in binary
 assert builder.read_compiled_protocol(binary)==r['compiled_protocol']==base['compiled_protocol']
 assert r['bytes_per_arena']==268435456 and r['aot_disabled'] and r['interpreter_disabled']
 for filename,key in [('RuntimeCompatibleReleases.json','runtime_compatible_releases_sha256'),('CompatibilityDownloads.json','compatibility_downloads_sha256'),('celeste-jit-probe.js','script_template_sha256'),('FMOD-LICENSE.txt','fmod_license_sha256'),('SJReleaseManifest.json','sj_release_manifest_sha256'),('GameContentManifest.json','game_content_manifest_sha256')]:assert hashlib.sha256(z.read(pre+filename)).hexdigest()==r[key]
 for key in ['framework_assembly_sha256','everest_assembly_sha256']:
  changed = {'System.Private.CoreLib.dll', 'Celeste.dll', 'Celeste.Mod.mm.dll', 'MMHOOK_Celeste.dll', 'CelesteJITEverest.dll'}
  assert {n:h for n,h in r[key].items() if n not in changed}=={n:h for n,h in base[key].items() if n not in changed}
  for n,d in r[key].items():assert hashlib.sha256(z.read(pre+'Managed/'+n)).hexdigest()==d
 assert len(r['framework_assembly_sha256'])==168
 assert not any('InstallTests' in n or 'RealUpdateTests' in n or 'FnaGraphicsTests' in n or 'ReflectionSignatures' in n or 'ReflectionFlagsTests' in n or 'MissingSignature' in n for n in names)
 assert r['bundled_content_files']==0 and r['private_prepared_game_il'] and not r['private_owner_content']
 assert hashlib.sha256(z.read(pre+'Managed/orig/Celeste.exe')).hexdigest()=='fd73f8a2311fa5737ded550cbad4b75c85b7686b36432f59185e940fcb65fcfe'
 assert r['game_content_aggregate_sha256']==base['game_content_aggregate_sha256']
 pins=json.loads(z.read(pre+'CompatibilityDownloads.json'))
 assert sorted(m['name'] for p in pins for m in p['modules'])==['CollabUtils2','FemtoHelper','GravityHelper']
 for pin in pins:
  expected=next(v for v in r['mod_download_manifest'].values() if v['sha256']==pin['pinnedSHA256'])
  assert pin['url']==expected['url'] and pin['bytes']==expected['bytes'] and pin['hashes']==[]
for key in ['source_sha256','native_library_sha256','launcher_native_libraries']:matches(r[key])
for key in ['native_library_sha256','runtime_config_sha256','graphics_native_receipt_sha256','mono_compatibility_receipt_sha256','ios_support','script_template_sha256']:assert r[key]==base[key],key
reflection=read(B/'launcher-resolution-reflection/receipt.json');matches(reflection['source_sha256'])
assert r['reflection_flags']['receipt_sha256']==sha(B/'launcher-resolution-reflection/receipt.json')
assert r['framework_assembly_sha256']['System.Private.CoreLib.dll']==reflection['targets']['ios']['output_sha256']
assert base['framework_assembly_sha256']['System.Private.CoreLib.dll']==reflection['targets']['ios']['input_sha256']
for target in reflection['targets'].values():
 assert sha(R/target['input'])==target['input_sha256'] and sha(R/target['output'])==target['output_sha256']
 assert target['patch']['original_methods']-target['patch']['unchanged_methods']==3 and target['patch']['fields_resources_references_unchanged']
assert 'LC_CODE_SIGNATURE' not in (A/'macho-load-commands.txt').read_text()
assert not any('CJ_HOOK_HOST_TEST' in word or 'CJ_GRAPHICS_HOST_TEST' in word for cmd in r['build_commands'] for word in cmd)
# Accepted native bridge sources that should not change in this product step.
for name in ['CJGraphicsPlatform.m','CJHookCodeArena.c','CJHookNative.c','CJSession.c','CJContentImport.m','CJFrameMetrics.c','CJEventStore.m','VMRange.c','VMRangeDarwin.c']:
 assert sha(S/'src'/name)==sha(R/'experiments/ios-jit/launcher-backbuffer/src'/name),name
# Only the reviewed flag accessor and its registration differ in the managed bridge.
bridge=(S/'src/CJGraphicsManaged.m').read_text()
additions=["""// CoreLib attribute queries need flags, without loading absent signature types.
// Mono's public accessor reads method flags without constructing managed Types.
static uint32_t CJITImplementationFlags(MonoMethod *method) {
    uint32_t flags=0; mono_method_get_flags(method,&flags); return flags;
}
""", """    mono_add_internal_call("System.Reflection.MonoMethodInfo::CJITGetImplementationFlags",(const void *)CJITImplementationFlags);
    gLog(@"mono_reflection_flags_registered",@{@"abi":@1});
"""]
for addition in additions:
 assert bridge.count(addition)==1
 bridge=bridge.replace(addition,'',1)
assert bridge==(R/'experiments/ios-jit/launcher-backbuffer/src/CJGraphicsManaged.m').read_text()
exports=set(read(B/'launcher-runtime'/args.build_id/'native-export-table.json'));internal=set();lua=set()
for name in ['Celeste.dll','FNA.dll','KeraLua.dll']:
 text=subprocess.check_output(['monodis','--implmap',str(B/'launcher-runtime-managed'/name)],text=True)
 internal.update(re.findall(r'\((\w+) __Internal\)$',text,re.M));lua.update(re.findall(r'\((\w+) lua54\)$',text,re.M))
assert len(internal)>=1294 and internal<=exports and len(lua)>=80 and lua<=exports
# All new native source gates bind to their actual tested sources.
gates={}
for path in [B/'launcher-runtime-install-tests/receipt.json',B/'launcher-runtime-real-updates/receipt.json',B/'launcher-runtime-ui-tests/receipt.json',B/'launcher-runtime-blocked-ui/receipt.json',B/'launcher-runtime-spring-install/receipt.json',B/'launcher-resolution-reflection-controls/receipt.json',B/'launcher-runtime-validation/host-fresh-spring/receipt.json',B/'launcher-runtime-validation/host-updated-paint/receipt.json']:
 g=read(path);assert g['status'].startswith('PASS_');matches(g.get('source_sha256',{}));gates[str(path.relative_to(R))]={'status':g['status'],'sha256':sha(path)}
 for filename,d in g.get('results',{}).items():assert sha(path.parent/filename)==d
ui=read(B/'launcher-runtime-ui-tests/receipt.json');sim=R/'artifacts/ios-jit'/(args.build_id+'-simulator')/'CelesteJITEverest.app'
assert sha(sim/'BuildInfo.json')==ui['simulator_build_info_sha256'] and sha(sim/'CelesteJITEverest')==ui['simulator_executable_sha256']
assert read(sim/'BuildInfo.json')['source_sha256']==r['source_sha256']
blocked_ui=read(B/'launcher-runtime-blocked-ui/receipt.json')
assert sha(sim/'BuildInfo.json')==blocked_ui['simulator_build_info_sha256'] and sha(sim/'CelesteJITEverest')==blocked_ui['simulator_executable_sha256']
smoke=B/'launcher-runtime'/(args.build_id+'-simulator')/'smoke/receipt.json';assert read(smoke)['status'].startswith('PASS_');gates[str(smoke.relative_to(R))]={'status':read(smoke)['status'],'sha256':sha(smoke)}
host=read(B/'launcher-runtime-validation/host-fresh-spring/receipt.json')
assert host['real_spring_dependency_selection'] and host['spring_map_gameplay'] and host['normal_selection_test'] and host['fixture_sha256']==r['game_fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
assert host['reflection_corelib_sha256']==reflection['targets']['host']['output_sha256'] and host['reflection_flags_checks']==30
assert host['reflection_receipt_sha256']==r['reflection_flags']['receipt_sha256']
paint_now=read(B/'launcher-runtime-validation/host-updated-paint/receipt.json')
assert paint_now['paint_regression'] and paint_now['frost_render_regression'] and paint_now['real_updated_mod_selection'] and paint_now['reflection_flags_checks']==30
assert paint_now['reflection_corelib_sha256']==host['reflection_corelib_sha256'] and paint_now['reflection_receipt_sha256']==r['reflection_flags']['receipt_sha256']
# Accepted graphics implementation controls remain evidence for identical FNA/native bytes.
# The changed game/runtime adapter must pass the new complete session matrix below.
inherited={}
for path in [R/'artifacts/ios-jit/launcher-backbuffer-20260912-24/package-validation.json',R/'docs/ios-jit/BUILD_24_GRAPHICS_ACCEPTANCE_EVIDENCE.json',B/'launcher-dependencies-validation/host-updated-paint/receipt.json']:
 g=read(path);assert g['status'].startswith('PASS_');inherited[str(path.relative_to(R))]={'sha256':sha(path),'status':g['status']}
paint=read(B/'launcher-dependencies-validation/host-updated-paint/receipt.json')
assert paint['real_updated_mod_selection'] and paint['paint_regression'] and paint['frost_render_regression'] and paint['fna_sha256']==r['fna_assembly_sha256']
for module in ['EeveeHelper','FrostHelper']:
 old=sorted((B/'launcher-dependencies-real-updates/Profile/Mods').glob(module+'-*.zip'))
 new=sorted((B/'launcher-runtime-real-updates/Profile/Mods').glob(module+'-*.zip'))
 assert [(p.name,sha(p)) for p in old]==[(p.name,sha(p)) for p in new],module
# Bind the actual runtime source/preparation and every replaced assembly.
identity=read(S/'RuntimeIdentity.json');managed=read(B/'launcher-runtime-managed/receipt.json')
assert r['bundled_runtime_identity']==identity==managed['runtime_identity']
assert r['bundled_runtime_identity_sha256']==sha(S/'RuntimeIdentity.json')==managed['runtime_identity_sha256']
assert r['game_receipt_sha256']==sha(B/'launcher-runtime-managed/receipt.json')
matches(managed['source_sha256'])
assert r['everest_assembly_sha256']=={n:h for n,h in managed['managed_sha256'].items() if n!='EverestSplash.dll'}
assert set(managed['replaced_assemblies'])=={'Celeste.dll','Celeste.Mod.mm.dll','MMHOOK_Celeste.dll','CelesteJITEverest.dll'}
for name in managed['replaced_assemblies']:assert r['everest_assembly_sha256'][name]!=base['everest_assembly_sha256'][name]
with zipfile.ZipFile(ipa) as z:assert z.read(pre+'RuntimeIdentity.json')==(S/'RuntimeIdentity.json').read_bytes()
source=B/'launcher-runtime-everest-source';deps=B/'launcher-runtime-everest-dependencies';game=B/'launcher-runtime-everest-game'
assert read(source/'source-receipt.json')['pins']['Everest'][1]==identity['everestSourceCommit']
assert subprocess.check_output(['git','-C',str(source/'Everest'),'rev-parse','HEAD'],text=True).strip()==identity['everestSourceCommit']
patch=read(source/'embedded-source-patch.json')
for name, value in patch['files'].items():assert sha(source/'Everest'/name)==value['patched_sha256'],name
assert read(deps/'receipt.json')['embedded_source_patch_sha256']==sha(source/'embedded-source-patch.json')
assert read(game/'preparation-receipt.json')['dependencies_receipt_sha256']==sha(deps/'receipt.json')
assert managed['preparation_receipt_sha256']==sha(game/'preparation-receipt.json')
for name,digest in read(deps/'receipt.json')['managed_sha256'].items():assert sha(deps/'managed'/name)==digest
for name,digest in read(game/'preparation-receipt.json')['output_sha256'].items():assert sha(game/'prepared'/name)==digest
for case in ['host-fresh-spring','host-spring-reload','host-updated-paint','host-full-sj-frost','host-quit-title','host-quit-busy']:
 path=B/'launcher-runtime-validation'/case/'receipt.json';v=read(path);matches(v['source_sha256'])
 assert v['status'].startswith('PASS_') and v['fixture_sha256']==r['game_fixture_sha256'] and v['fna_sha256']==r['fna_assembly_sha256']
 assert v['reflection_flags_checks']==30 and v['session_contract_checks']==37
 assert v['mono_compatibility_receipt_sha256']==r['mono_compatibility_receipt_sha256']
 assert v['reflection_receipt_sha256']==r['reflection_flags']['receipt_sha256']
 assert sha(path.parent/'run.log')==v['log_sha256']
 log=(path.parent/'run.log').read_text()
 assert 'runtime_identity_pass version=1.6531.0-cjit-d72e94f' in log and 'PASS_REAL_EVEREST_6531_SOURCE_CONTROLS' in log
 if case=='host-spring-reload':assert v['spring_session_reloaded'] and 'fresh process reloads the saved Spring session' in log
 if case=='host-updated-paint':
  for name,version in [('EeveeHelper','1.12.6'),('FrostHelper','1.80.2'),('ExtendedVariantMode','0.51.0'),('MaxHelpingHand','1.40.10')]:assert 'everest_selection_module_verified '+name+' '+version+';' in log
 if case=='host-full-sj-frost':assert v['all_52_modules_verified'] and v['frost_render_regression'] and v['original_sj_music_playing']
 if case=='host-quit-title':assert v['quit_title']
 if case=='host-quit-busy':assert v['quit_busy']
 gates[str(path.relative_to(R))]={'status':v['status'],'sha256':sha(path)}
assert read(B/'launcher-runtime-real-updates/result.json')['status']=='PASS_REAL_FOUR_MOD_UPDATE_TRANSACTION'
cache=read(B/'launcher-runtime-install-tests/runtime-cache.json')
assert cache['status']=='PASS_RUNTIME_CACHE_UPGRADE_DOWNGRADE_OFFLINE_POLICY' and len(cache['cases'])==6
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
symbol=next(A.glob('*.dSYM'));uuid=subprocess.check_output(['xcrun','dwarfdump','--uuid',str(symbol)],env=env,text=True).split(' (')[0]
assert uuid==r['executable_uuid']
result=dict(status='PASS_BUILD27_UNSIGNED_PACKAGE_AND_EVEREST_UPGRADE_GATES',build_id=args.build_id,ipa_sha256=r['ipa_sha256'],ipa_bytes=ipa.stat().st_size,executable_uuid=r['executable_uuid'],source_count=len(r['source_sha256']),native_imports=len(internal),lua_imports=len(lua),validation_receipts=gates,inherited_validation=inherited,accepted_native_runtime_renderer_fna_support_identical=True, actual_everest_runtime=identity, replaced_managed_assemblies=managed["replaced_assemblies"],scoped_corelib_reflection_correction=r['reflection_flags'],no_simulator_fixture_in_device_binary=True,game_content_bundled=False,phone_build27_acceptance=False,script_template_sha256=r['script_template_sha256'])
(A/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
