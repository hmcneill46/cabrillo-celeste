#!/usr/bin/env python3
"""Validate the exact private Everest IPA, ZIPs, original assets and native closure."""
import argparse,hashlib,importlib.util,json,plistlib,re,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='everest-canary-20260911-13');a=p.parse_args()
out=ROOT/'artifacts/ios-jit'/a.build_id;stage=ROOT/'.build/ios-jit/everest-canary'/a.build_id
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((out/'build-receipt.json').read_text())
managed=json.loads((ROOT/'.build/ios-jit/everest-managed/receipt.json').read_text())
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
    assert info['CFBundleVersion']=='13' and info['CFBundleShortVersionString']=='0.6.0'
    binary=z.read(prefix+'CelesteJITEverest');build=json.loads(z.read(prefix+'BuildInfo.json'))
    assert builder.read_compiled_protocol(binary)==build['compiled_protocol']
    assert build['bytes_per_arena']==33554432 and build['aot_disabled'] and build['interpreter_disabled']
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
    for item in content['files']:
        data=z.read(prefix+'Content/'+item['path']);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],item['path']
        aggregate.update(item['path'].encode()+b'\0'+str(item['bytes']).encode()+b'\0'+item['sha256'].encode()+b'\n')
    assert aggregate.hexdigest()==content['aggregate_sha256']==r['game_content_aggregate_sha256']=='30a1c147d1a3ab0aa45762094e393ed7fd69951dd66e5af063447641e0699c46'
assert sha(ipa)==r['ipa_sha256']
for mapping in [r['source_sha256'],r['native_library_sha256'],managed['source_sha256']]:
    assert all(sha(ROOT/name)==digest for name,digest in mapping.items())
assert not any('CJ_HOOK_HOST_TEST' in word or 'CJ_GRAPHICS_HOST_TEST' in word for cmd in r['build_commands'] for word in cmd)
assert 'LC_CODE_SIGNATURE' not in (out/'macho-load-commands.txt').read_text()
exports=set(json.loads((stage/'native-export-table.json').read_text()));internal=set();lua=set()
for name in ['Celeste.dll','FNA.dll','KeraLua.dll']:
    imports=subprocess.check_output(['monodis','--implmap',str(ROOT/'.build/ios-jit/everest-managed'/name)],text=True)
    internal.update(re.findall(r'\((\w+) __Internal\)$',imports,re.M))
    lua.update(re.findall(r'\((\w+) lua54\)$',imports,re.M))
assert len(internal)>=1294 and internal<=exports,sorted(internal-exports)
assert len(lua)>=80 and lua<=exports,sorted(lua-exports)
assert 'FMOD_DSP_GetCPUUsage' not in internal and 'FNA3D_CJIT_EndCallback' in internal
for name,record in r['mod_zip_files'].items():
    assert sha(out/name)==record['sha256'] and (out/name).stat().st_size==record['bytes']
    with zipfile.ZipFile(out/name) as z:assert z.testzip() is None and 'everest.yaml' in z.namelist()
host=json.loads((ROOT/'.build/ios-jit/everest-host-test/receipt.json').read_text())
assert host['fixture_sha256']==r['game_fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
assert all(sha(ROOT/name)==digest for name,digest in host['source_sha256'].items())
assert host['callback_autorelease_pools'] and host['ns_zombie_enabled'] and host['metal_api_validation_confirmed']
native=json.loads((out/'graphics-native-receipt.json').read_text())
assert sha(out/'graphics-native-receipt.json')==r['graphics_native_receipt_sha256']
assert native['patch_sha256']==r['graphics_native_patch_sha256']==host['native_patch_sha256']
assert native['ios_archive_sha256']==r['native_library_sha256'][native['ios_archive']]
assert native['host_library_sha256']==host['desktop_native_sha256']['libFNA3D.0.dylib']
assert all(sha(ROOT/name)==digest for name,digest in native['source_sha256'].items())
preparation=json.loads((ROOT/'.build/ios-jit/everest-game/preparation-receipt.json').read_text())
assert preparation['accepted_fna_input_sha256']=='802b6dd2fe0a6c386d1b29b48dfea358ce85fe4f2530332410bcfaa015bfcbf0'
result=dict(status='PASS_PRIVATE_EVEREST_PACKAGE_AND_INPUTS',ipa_bytes=ipa.stat().st_size,ipa_sha256=sha(ipa),
    adapter_sha256=r['game_fixture_sha256'],fna_sha256=r['fna_assembly_sha256'],native_internal_imports=len(internal),native_lua_imports=len(lua),
    all_declared_game_fna_lua_static_imports_resolve=True,content_files=1216,content_bytes=r['game_content_bytes'],
    content_aggregate_sha256=aggregate.hexdigest(),framework_dlls=168,everest_managed_dlls=len(r['everest_assembly_sha256']),
    original_il_not_reconstructed=True,untrimmed_game_and_fna=True,apple_managed_bindings=False,
    debug_symbols_outside_ipa=True,signature=False,provisioning_profile=False,
    accepted_runtime_and_renderer_reused=True,script_geometry_matches_build=True,code_budget_bytes=67108864,
    host_adapter_bytes_match=True,private_owner_kit=True,physical_everest_tested=False)
(out/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
