#!/usr/bin/env python3
"""Validate the exact private Everest IPA, ZIPs, original assets and native closure."""
import argparse,hashlib,importlib.util,json,plistlib,re,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='sj-memory-check-20260912-18');a=p.parse_args()
out=ROOT/'artifacts/ios-jit'/a.build_id;stage=ROOT/'.build/ios-jit/sj-memory-check'/a.build_id
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((out/'build-receipt.json').read_text())
managed=json.loads((ROOT/'.build/ios-jit/sj-gravity-managed/receipt.json').read_text())
spec=importlib.util.spec_from_file_location('builder',SOURCE/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
ipa=out/'CelesteJITEverest-unsigned.ipa'
with zipfile.ZipFile(ipa) as z:
    assert z.testzip() is None
    names=z.namelist();prefix='Payload/CelesteJITEverest.app/'
    builder.validate_payload_members((n,z.read(n)) for n in names)
    assert all(n.startswith(prefix) for n in names)
    assert not any('_CodeSignature' in n or n.endswith('.mobileprovision') or 'Microsoft.iOS' in n for n in names)
    assert not any(n.endswith('.zip') for n in names), 'Test mods must be separately imported.'
    info=plistlib.loads(z.read(prefix+'Info.plist'))
    assert info['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.everest'
    assert info['CFBundleVersion']=='18' and info['CFBundleShortVersionString']=='0.9.1'
    binary=z.read(prefix+'CelesteJITEverest');build=json.loads(z.read(prefix+'BuildInfo.json'))
    assert builder.read_compiled_protocol(binary)==build['compiled_protocol']
    assert build['bytes_per_arena']==134217728 and build['aot_disabled'] and build['interpreter_disabled']
    assert all(r[k]==v for k,v in build.items())
    assert hashlib.sha256(binary).hexdigest()==r['executable_sha256']
    assert hashlib.sha256(z.read(prefix+'celeste-jit-probe.js')).hexdigest()==r['script_template_sha256']
    assert hashlib.sha256(z.read(prefix+'FMOD-LICENSE.txt')).hexdigest()==r['fmod_license_sha256']
    for key in ('framework_assembly_sha256','everest_assembly_sha256'):
        for name,digest in r[key].items():assert hashlib.sha256(z.read(prefix+'Managed/'+name)).hexdigest()==digest
    assert len(r['framework_assembly_sha256'])==168
    assert r['everest_assembly_sha256']['CelesteJITEverest.dll']==r['game_fixture_sha256']
    assert r['everest_assembly_sha256']['FNA.dll']==r['fna_assembly_sha256']
    assert 'Celeste.Mod.mm.dll' in r['everest_assembly_sha256'], 'Runtime relinker needs its genuine rules.'
    assert hashlib.sha256(z.read(prefix+'Managed/orig/Celeste.exe')).hexdigest()=='fd73f8a2311fa5737ded550cbad4b75c85b7686b36432f59185e940fcb65fcfe'
    raw=z.read(prefix+'GameContentManifest.json');assert hashlib.sha256(raw).hexdigest()==r['game_content_manifest_sha256']
    content=json.loads(raw);aggregate=hashlib.sha256()
    assert len(content['files'])==1216
    assert not any(n.startswith(prefix+'Content/') for n in names)
    assert build['bundled_content_files']==0 and not build['private_owner_content']
    assert build['private_prepared_game_il'] and build['persistent_content_import']
    assert ipa.stat().st_size<50000000
    for item in content['files']:
        aggregate.update(item['path'].encode()+b'\0'+str(item['bytes']).encode()+b'\0'+item['sha256'].encode()+b'\n')
    assert aggregate.hexdigest()==content['aggregate_sha256']==r['game_content_aggregate_sha256']=='30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46'
assert sha(ipa)==r['ipa_sha256']
for mapping in [r['source_sha256'],r['native_library_sha256'],managed['source_sha256']]:
    assert all(sha(ROOT/name)==digest for name,digest in mapping.items())
assert not any('CJ_HOOK_HOST_TEST' in word or 'CJ_GRAPHICS_HOST_TEST' in word for cmd in r['build_commands'] for word in cmd)
assert 'LC_CODE_SIGNATURE' not in (out/'macho-load-commands.txt').read_text()
exports=set(json.loads((stage/'native-export-table.json').read_text()));internal=set();lua=set()
for name in ['Celeste.dll','FNA.dll','KeraLua.dll']:
    imports=subprocess.check_output(['monodis','--implmap',str(ROOT/'.build/ios-jit/sj-gravity-managed'/name)],text=True)
    internal.update(re.findall(r'\((\w+) __Internal\)$',imports,re.M))
    lua.update(re.findall(r'\((\w+) lua54\)$',imports,re.M))
assert len(internal)>=1294 and internal<=exports,sorted(internal-exports)
assert len(lua)>=80 and lua<=exports,sorted(lua-exports)
assert 'FMOD_DSP_GetCPUUsage' not in internal and 'FNA3D_CJIT_EndCallback' in internal
for name,record in r['mod_zip_files'].items():
    assert sha(out/name)==record['sha256'] and (out/name).stat().st_size==record['bytes']
    with zipfile.ZipFile(out/name) as z:assert z.testzip() is None and 'everest.yaml' in z.namelist()
host=json.loads((ROOT/'.build/ios-jit/sj-memory-check-host-test/receipt.json').read_text())
assert host['fixture_sha256']==r['game_fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
assert all(sha(ROOT/name)==digest for name,digest in host['source_sha256'].items())
assert all(sha(ROOT/name)==digest for name,digest in host['input_sha256'].items())
assert host['callback_autorelease_pools'] and host['ns_zombie_enabled'] and host['metal_api_validation_confirmed']
native=json.loads((out/'graphics-native-receipt.json').read_text())
assert sha(out/'graphics-native-receipt.json')==r['graphics_native_receipt_sha256']
assert native['patch_sha256']==r['graphics_native_patch_sha256']==host['native_patch_sha256']
assert native['ios_archive_sha256']==r['native_library_sha256'][native['ios_archive']]
assert native['host_library_sha256']==host['desktop_native_sha256']['libFNA3D.0.dylib']
assert all(sha(ROOT/name)==digest for name,digest in native['source_sha256'].items())
compat=json.loads((out/'mono-compatibility-receipt.json').read_text())
assert sha(out/'mono-compatibility-receipt.json')==r['mono_compatibility_receipt_sha256']==host['mono_compatibility_receipt_sha256']
assert compat['targets']['ios']['sha256']==r['native_library_sha256'][compat['targets']['ios']['archive']]
assert compat['targets']['host']['sha256']==host['mono_compatibility_archive_sha256']
assert all(t['unchanged_members']==259 and t['replaced_member']=='mono-codeman.c.o' for t in compat['targets'].values())
visibility=json.loads((ROOT/'.build/ios-jit/sj-budget-visibility-tests/receipt.json').read_text())
assert visibility['cases_per_runtime']==15 and visibility['results']['1']['archive_sha256']==compat['targets']['host']['sha256']
assert all(sha(ROOT/name)==digest for name,digest in visibility['source_sha256'].items())
assert compat['ordinary_chunk_minimum_bytes']==r['mono_ordinary_chunk_minimum_bytes']==65536
assert host['code_manager_model']==dict(page_bytes=16384,granule_bytes=16384,bind_room_divisor=4,minimum_chunk_bytes=65536)
assert compat['inherited_visibility_receipt_sha256']==r['inherited_mono_visibility_receipt_sha256']
assert managed['mono8_utils_compatibility']==r['mono8_utils_compatibility']
assert r['everest_assembly_sha256']['MonoMod.Utils.dll']==managed['mono8_utils_compatibility']['output_sha256']
assert len(r['mod_zip_files'])==7 and len(r['original_helper_files'])==3
assert 'GravityHelper-v1.2.28.zip' in r['mod_zip_files']
for name,record in r['original_helper_files'].items():
    assert r['mod_zip_files'][name]['sha256']==record['zipSha256']
    with zipfile.ZipFile(out/name) as archive:
        for dll in record['distributedDlls']:
            dll_path=record['actual_dll_paths'][dll['path']]
            assert hashlib.sha256(archive.read(dll_path)).hexdigest()==dll['sha256']
            imports=subprocess.check_output(['monodis','--implmap',str(ROOT/'.build/ios-jit/sj-gravity-inputs'/dll['path'])],text=True)
            assert imports.strip()=='ImplMap Table (1..0)'
assert host['status']=='PASS_HOST_REAL_GRAVITY_LUACUTSCENES_MAXHELPINGHAND_SAVES_AND_RESUME'
assert all(host[k] for k in ['gravity_optional_transform', 'gravity_optional_absence_handled',
    'gravity_inverted_and_normal_checks', 'gravity_platform_check'])
gravity_tests_path=ROOT/'.build/ios-jit/sj-gravity-compat-tests/receipt.json'
gravity_tests=json.loads(gravity_tests_path.read_text())
assert gravity_tests['status']=='PASS_GRAVITY_OPTIONAL_TRANSFORM_AND_POLICY_CONTROLS_ON_MONO'
assert gravity_tests['cases_per_input']==17 and len(gravity_tests['results'])==2
assert gravity_tests['adapter_sha256']==r['game_fixture_sha256']
assert gravity_tests['mono_archive_sha256']==host['mono_compatibility_archive_sha256']
assert all(sha(ROOT/name)==digest for name,digest in gravity_tests['source_sha256'].items())
for index,record in enumerate(gravity_tests['results']):
    assert sha(ROOT/record['input_path'])==record['input_sha256']
    assert sha(gravity_tests_path.parent/(str(index)+'.log'))==record['log_sha256']
capacity_path=ROOT/'.build/ios-jit/sj-memory-check-capacity-tests/receipt.json'
capacity=json.loads(capacity_path.read_text())
assert capacity['status']=='PASS_BUILD15_EXACT_FAILURE_AND_BUILD18_DEVICE_SIZED_ALIAS_REPLAY'
assert capacity['budget_bytes']==268435456 and capacity['page_bytes']==16384
assert capacity['full_traces']==1 and capacity['extra_chunk_count']>1000
assert capacity['extra_native_reserve_bytes']==16777216
assert all(sha(ROOT/name)==digest for name,digest in capacity['input_sha256'].items())

vm_path=ROOT/'.build/ios-jit/sj-memory-check-vm-tests/receipt.json'
vm=json.loads(vm_path.read_text())
assert vm['status']=='PASS_PHYSICAL_BUILD17_LIMIT_CONTROL_AND_PAGE_SIZED_VM_CHECKER'
assert all(sha(ROOT/name)==digest for name,digest in vm['input_sha256'].items())
assert r['vm_range_policy']=='intersected_os_pages_v1'
assert r['vm_range_source_sha256']==sha(SOURCE/'src/VMRange.c')
compiled_sources={word for cmd in r['build_commands'] for word in cmd if word.endswith('/VMRange.c')}
assert compiled_sources=={str(SOURCE/'src/VMRange.c')}
previous=json.loads((ROOT/'artifacts/ios-jit/sj-gravity-20260912-17/build-receipt.json').read_text())
for key in ['mod_zip_files','everest_assembly_sha256','framework_assembly_sha256','native_library_sha256','script_template_sha256']:
    assert previous[key]==r[key],key
preparation=json.loads((ROOT/'.build/ios-jit/everest-game/preparation-receipt.json').read_text())
assert preparation['accepted_fna_input_sha256']=='802b6dd2fe0a6c386d1b29b48dfea358ce85fe4f2530332410bcfaa015bfcbf0'
result=dict(status='PASS_BUILD18_VM_CHECKER_AND_UNCHANGED_GRAVITY_PAYLOAD',ipa_bytes=ipa.stat().st_size,ipa_sha256=sha(ipa),
    adapter_sha256=r['game_fixture_sha256'],fna_sha256=r['fna_assembly_sha256'],native_internal_imports=len(internal),native_lua_imports=len(lua),
    all_declared_game_fna_lua_static_imports_resolve=True,bundled_content_files=0,import_manifest_files=1216,import_content_bytes=r['game_content_bytes'],
    content_aggregate_sha256=aggregate.hexdigest(),framework_dlls=168,everest_managed_dlls=len(r['everest_assembly_sha256']),
    original_il_not_reconstructed=True,untrimmed_game_and_fna=True,apple_managed_bindings=False,
    debug_symbols_outside_ipa=True,signature=False,provisioning_profile=False,
    accepted_renderer_reused=True,isolated_mono_member_visibility_fix=True,script_geometry_matches_build=True,code_budget_bytes=268435456,
    host_adapter_bytes_match=True,vm_range_test_receipt_sha256=sha(vm_path),vm_range_policy=r['vm_range_policy'],unchanged_build17_payload_verified=True,gravity_optional_compatibility_checks=34,
    gravity_compatibility_test_receipt_sha256=sha(gravity_tests_path),capacity_receipt_sha256=sha(capacity_path),
    original_mod_zips_preserved=True,private_owner_kit=True,physical_gravity_helper_tested=False)
(out/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
