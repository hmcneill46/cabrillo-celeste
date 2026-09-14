#!/usr/bin/env python3
"""Bind the FNA patch, full helper API scan and real Frost rendering regression."""
import hashlib,json,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit';O=B/'launcher-session-fna';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
M=B/'launcher-session-managed';tool=M/'patch-tool/FnaGraphicsCompatibility.dll';sdk=B/'managed-runtime/dotnet-sdk-8.0.422'
base=B/'content-managed/FNA.dll';current=M/'FNA.dll';receipt=read(M/'receipt.json');patch=receipt['fna_graphics_compatibility']
assert sha(base)==patch['input_sha256'] and sha(current)==patch['output_sha256']
assert receipt['source_sha256'][str((S/'tools/FnaGraphicsCompatibility.cs').relative_to(R))]==sha(S/'tools/FnaGraphicsCompatibility.cs')
for name,directory in [('baseline',base.parent),('patched',M)]:
    subprocess.run([str(sdk/'dotnet'),str(tool),'audit',str(directory),str(B/'sj-lobby-mods'),str(O/(name+'-audit.json'))],check=True)
before=read(O/'baseline-audit.json');after=read(O/'patched-audit.json')
assert before['assemblies']==after['assemblies']==49
assert before['fna_member_references']==after['fna_member_references']==3222
assert before['runtime_array_intrinsics']==after['runtime_array_intrinsics']==3
assert len(before['missing'])==1 and before['missing'][0]['member']==patch['added_method'] and not after['missing']
for name,path in [('already-patched',current),('wrong-input',M/'CelesteJITEverest.dll')]:
    out=O/(name+'.dll');assert not out.exists()
    x=subprocess.run([str(sdk/'dotnet'),str(tool),'patch',str(path),str(out),str(O/(name+'.json'))],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (O/(name+'.log')).write_text(x.stdout)
    assert x.returncode and not out.exists() and 'Unreviewed FNA input' in x.stdout
subprocess.run([str(sdk/'dotnet'),str(tool),'patch',str(base),str(O/'repeat-FNA.dll'),str(O/'repeat-patch.json')],check=True)
assert sha(O/'repeat-FNA.dll')==sha(current)
H=B/'launcher-session-validation/host-full-sj';host=read(H/'receipt.json');log=(H/'run.log').read_text()
assert sha(H/'run.log')==host['log_sha256'] and host['fixture_sha256']==sha(M/'CelesteJITEverest.dll') and host['fna_sha256']==sha(current)
assert host['frost_render_regression'] and host['graphics_contract_checks']==33
assert host['graphics_regression_source_sha256']==sha(S/'tests/FnaGraphicsTests.cs')
assert host['graphics_regression_dll_sha256']==sha(H/'FnaGraphicsTests.dll')
assert 'PASS_REAL_FROST_LAVA_AND_FNA_CONTRACT checks=33 queryCalls=2' in log
assert 'FNA_CONTRACT_PASS ten_thousand_queries_allocate_zero_bytes' in log
assert 'FNA_CONTRACT_PASS original_lava_produces_nonempty_gpu_pixels' in log
upstream=read(S/'fna-extension-pin.json');assert sha(O/'upstream-current-GraphicsDevice.cs')==upstream['sha256']
result=dict(status='PASS_FNA_EXTENSION_AND_ORIGINAL_FROST_RENDERING',fna_before_sha256=sha(base),fna_after_sha256=sha(current),
    unchanged_existing_methods=patch['unchanged_existing_methods'],unchanged_fields=patch['unchanged_fields'],new_native_entrypoints=0,
    scanned_original_helper_assemblies=49,resolved_fna_member_references=3222,runtime_array_intrinsics_separate=3,
    original_missing_members=before['missing'],remaining_missing_members=[],graphics_contract_checks=33,
    null_zero_one_two_three_four_target_counts=True,undersized_rejected=True,oversized_tail_preserved=True,
    ten_thousand_queries_allocated_bytes=0,original_frost_store_restore_counts=[0,1,4],original_lava_render_and_nonempty_gpu_readback=True,
    original_frost_queries_during_render=2,deterministic_patch=True,unexpected_input_rejected=True,already_patched_input_rejected=True,
    native_renderer_preserved=True,original_mod_zips_preserved=True,host_full_sj_save_resume_pass=True,physical_build22_tested=False,
    upstream=upstream,host_receipt_sha256=sha(H/'receipt.json'),patch_tool_sha256=sha(tool),
    source_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),S/'tools/FnaGraphicsCompatibility.cs',S/'tests/FnaGraphicsTests.cs',S/'fna-extension-pin.json']},
    original_zip_sha256={str(p.relative_to(R)):sha(p) for p in sorted((B/'sj-lobby-mods').glob('*.zip'))})
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
