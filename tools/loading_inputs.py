"""Validate the exact four managed replacements used by the new loading lane."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-loading'
REPLACEMENTS={'Managed/CelesteJITEverest.dll','Managed/Celeste.Mod.mm.dll','Managed/Celeste.dll','Managed/MMHOOK_Celeste.dll'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def local(name):
    path=ROOT/name
    if path.resolve()!=path.absolute() or ROOT not in path.parents:raise ValueError('Expected an unaliased Cabrillo path: '+str(name))
    return path
def validate_managed(receipt_path):
    receipt_path=local(receipt_path)
    receipt=json.loads(receipt_path.read_text())
    lock=json.loads((SOURCE/'ManagedDependencies.json').read_text())
    if receipt['status']!='PASS_LOADING_MANAGED_BUILD' or receipt['input_manifest_sha256']!=lock['manifest_sha256']:raise ValueError('Unverified managed build inputs')
    if sha(ROOT/'.private/loading-inputs/manifest.json')!=lock['manifest_sha256']:raise ValueError('Changed managed input manifest')
    if set(receipt['replaced_resources'])!=REPLACEMENTS:raise ValueError('Unexpected managed replacement set')
    if not all(receipt[k] is True for k in ['fna_semantics_unchanged','original_content_assembly_unchanged','unchanged_native_runtime']):raise ValueError('Unverified preserved runtime contracts')
    for name,digest in receipt['public_source_sha256'].items():
        if sha(local(name))!=digest:raise ValueError('Managed source changed: '+name)
    resources=local(receipt['resource_root'])
    if ROOT/'.build' not in resources.parents:raise ValueError('Managed output must be in .build')
    files={str(p.relative_to(resources)):sha(local(p)) for p in resources.rglob('*') if p.is_file()}
    baseline=ROOT/'.private/resources/build28'
    expected={str(p.relative_to(baseline)):sha(p) for p in baseline.rglob('*') if p.is_file()}
    if files!=receipt['resources'] or files.keys()!=expected.keys():raise ValueError('Changed/missing/extra managed resource')
    for name,digest in expected.items():
        if name not in REPLACEMENTS and files[name]!=digest:raise ValueError('Unrelated accepted resource changed: '+name)
    if not all(files[n]!=expected[n] for n in REPLACEMENTS):raise ValueError('Expected cooperative loading assembly was not rebuilt')
    return receipt,resources
