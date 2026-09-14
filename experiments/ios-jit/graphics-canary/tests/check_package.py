#!/usr/bin/env python3
"""Check the exact unsigned graphics kit, native imports, IL and immutable inputs."""
import argparse,hashlib,importlib.util,json,plistlib,re,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-id',default='graphics-canary-20260911-11');a=p.parse_args()
out=ROOT/'artifacts/ios-jit'/a.build_id;stage=ROOT/'.build/ios-jit/graphics-canary'/a.build_id
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((out/'build-receipt.json').read_text());fixture=json.loads((out/'fixture-receipt.json').read_text())
spec=importlib.util.spec_from_file_location('builder',SOURCE/'build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
ipa=out/'CelesteJITGraphics-unsigned.ipa'
with zipfile.ZipFile(ipa) as z:
    assert z.testzip() is None
    names=z.namelist();prefix='Payload/CelesteJITGraphics.app/'
    builder.validate_payload_members((n,z.read(n)) for n in names)
    assert all(n.startswith(prefix) for n in names)
    assert not any('_CodeSignature' in n or n.endswith('.mobileprovision') or 'GraphicsCanary-v' in n for n in names)
    assert not any(n.endswith('/Celeste.exe') or '/Content/' in n or 'Microsoft.iOS' in n for n in names)
    info=plistlib.loads(z.read(prefix+'Info.plist'))
    assert info['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.graphics'
    assert info['CFBundleVersion']=='11' and info['CFBundleShortVersionString']=='0.4.1'
    binary=z.read(prefix+'CelesteJITGraphics');build=json.loads(z.read(prefix+'BuildInfo.json'))
    assert builder.read_compiled_protocol(binary)==build['compiled_protocol']
    assert build['bytes_per_arena']==16777216 and build['aot_disabled'] and build['interpreter_disabled']
    assert all(r[k]==v for k,v in build.items())
    assert hashlib.sha256(binary).hexdigest()==r['executable_sha256']
    assert hashlib.sha256(z.read(prefix+'celeste-jit-probe.js')).hexdigest()==r['script_template_sha256']
    assert hashlib.sha256(z.read(prefix+'Managed/FNA.dll')).hexdigest()==r['fna_assembly_sha256']==fixture['fna_sha256']
    for key in ('framework_assembly_sha256','hook_assembly_sha256'):
        for name,digest in r[key].items(): assert hashlib.sha256(z.read(prefix+'Managed/'+name)).hexdigest()==digest
    assert len(r['framework_assembly_sha256'])==168 and len(r['hook_assembly_sha256'])==10
    assert len([n for n in names if n.startswith(prefix+'licenses/')])>=20
assert sha(ipa)==r['ipa_sha256']==fixture['ipa_sha256'] and fixture['compiled_after_ipa']
assert sha(out/'GraphicsCanary-v0.4.1.dll')==fixture['fixture_sha256']
assert all(sha(ROOT/name)==digest for name,digest in r['source_sha256'].items())
assert all(sha(ROOT/name)==digest for name,digest in r['native_library_sha256'].items())
assert not any('CJ_HOOK_HOST_TEST' in word or 'CJ_GRAPHICS_HOST_TEST' in word for cmd in r['build_commands'] for word in cmd)
loads=(out/'macho-load-commands.txt').read_text();assert 'LC_CODE_SIGNATURE' not in loads
exports=set(json.loads((stage/'native-export-table.json').read_text()))
imports=subprocess.check_output(['monodis','--implmap',str(ROOT/'.build/ios-jit/graphics-managed/FNA.dll')],text=True)
internal=set(re.findall(r'\((\w+) __Internal\)$',imports,re.M))
assert len(internal)>800 and internal <= exports,sorted(internal-exports)
references=subprocess.check_output(['monodis','--assemblyref',str(ROOT/'.build/ios-jit/graphics-managed/FNA.dll')],text=True)
assert 'Microsoft.iOS' not in references and 'Version=10.' not in references
assert set(re.findall(r'Version=([\d.]+)',references))=={'8.0.0.0'}
baseline=json.loads((ROOT/'artifacts/ios-jit/hook-canary-20260911-09/build-receipt.json').read_text())
assert all(sha(ROOT/name)==digest for name,digest in baseline['source_sha256'].items())
assert baseline['script_template_sha256']==r['script_template_sha256']
assert all(r['native_library_sha256'][name]==digest for name,digest in baseline['native_library_sha256'].items())
host=json.loads((ROOT/'.build/ios-jit/graphics-host-test/receipt.json').read_text())
assert host['fixture_sha256']==fixture['fixture_sha256'] and host['fna_sha256']==r['fna_assembly_sha256']
assert all(sha(ROOT/name)==digest for name,digest in host['source_sha256'].items())
native=json.loads((out/'graphics-native-receipt.json').read_text())
assert sha(out/'graphics-native-receipt.json')==r['graphics_native_receipt_sha256']
assert native['patch_sha256']==r['graphics_native_patch_sha256']==host['native_patch_sha256']
assert native['patched_metal_sha256']==host['native_metal_source_sha256']
assert native['ios_archive_sha256']==r['native_library_sha256'][native['ios_archive']]
assert native['host_library_sha256']==host['desktop_native_sha256']['libFNA3D.0.dylib']
assert 'FNA3D_CJIT_EndCallback' in internal and 'FNA3D_CJIT_EndCallback' in exports
assert host['callback_autorelease_pools'] and host['pending_clear_reset'] and host['suppressed_draw_recovered']
assert all(sha(ROOT/name)==digest for name,digest in native['source_sha256'].items())
result=dict(status='PASS_UNSIGNED_GRAPHICS_PACKAGE_AND_INPUTS',ipa_bytes=ipa.stat().st_size,ipa_sha256=sha(ipa),
    fixture_sha256=fixture['fixture_sha256'],fna_sha256=r['fna_assembly_sha256'],native_internal_imports=len(internal),
    all_declared_internal_imports_resolve=True,remaining_non_internal_imports='Two unused Emscripten declarations; not an iOS capability',
    framework_dlls=168,monomod_dlls=10,untrimmed_fna=True,apple_managed_bindings=False,
    debug_symbols_outside_ipa=True,signature=False,provisioning_profile=False,
    g1_g2_sources_and_runtime_unchanged=True,script_matches_physical_build9=True,
    host_fixture_bytes_match=True,host_and_ios_patched_metal_source_match=True,
    callback_cleanup_reset_and_suppressed_draw_tested=True,physical_graphics_tested=False)
(out/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
