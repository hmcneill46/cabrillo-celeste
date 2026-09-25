"""Verify the new Everest source payload and preserve the corrected native runtime."""
import json
from pathlib import Path
from platform_inputs import ROOT, owned, sha
from platform_inputs import validate_managed as validate_base_managed
from visibility_inputs import validate_native as validate_visibility

SOURCE = ROOT / 'experiments/ios-jit/launcher-everest6580'
REPLACEMENTS = {'Managed/Celeste.dll', 'Managed/Celeste.Mod.mm.dll',
                'Managed/MMHOOK_Celeste.dll', 'Managed/CelesteJITEverest.dll'}
COMMIT = '082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75'


def validate_native():
    if (SOURCE/'NativePayload.json').read_bytes() != (ROOT/'experiments/ios-jit/launcher-visibility/NativePayload.json').read_bytes():
        raise ValueError('Everest upgrade must preserve the exact build36 native runtime')
    return validate_visibility()


def validate_managed(receipt_path):
    p = owned(receipt_path); r = json.loads(p.read_text())
    lock = json.loads((SOURCE/'ManagedDependencies.json').read_text())
    if r.get('status') != 'PASS_EVEREST_6580_MANAGED_BUILD' or r.get('schema') != 1:
        raise ValueError('Expected verified Everest1.6580 source build')
    if r['upstream_commit'] != COMMIT or r['upstream_version'] != '1.6580.0':
        raise ValueError('Unexpected Everest identity')
    for key, file in [('input_manifest_sha256','.private/loading-inputs/manifest.json'),
                      ('everest_manifest_sha256',lock['everest_manifest'])]:
        if r[key] != sha(owned(file)): raise ValueError('Changed managed source manifest')
    if r['input_manifest_sha256'] != lock['manifest_sha256'] or r['everest_manifest_sha256'] != lock['everest_manifest_sha256']:
        raise ValueError('Unpinned managed source manifest')
    base_path = owned(r['base_receipt'])
    if sha(base_path) != r['base_receipt_sha256'] or r['base_receipt_sha256'] != 'e03d75eb1377a81a71d596c7e47567b431e2c67103eb2af1346f5bc315943fcc':
        raise ValueError('Changed managed baseline')
    base, _ = validate_base_managed(base_path)
    for n, h in r['public_source_sha256'].items():
        if sha(owned(n)) != h: raise ValueError('Changed managed build source: '+n)
    resources = owned(r['resource_root'])
    if ROOT/'.build' not in resources.parents: raise ValueError('Managed output must be private')
    files = {str(f.relative_to(resources)):sha(owned(f)) for f in resources.rglob('*') if f.is_file()}
    if files != r['resources'] or files.keys() != base['resources'].keys(): raise ValueError('Changed managed resource set')
    if {n for n, h in files.items() if h != base['resources'][n]} != REPLACEMENTS or set(r['replaced_resources']) != REPLACEMENTS:
        raise ValueError('Unrelated managed resource changed')
    if not all(r[k] for k in ['fna_semantics_unchanged','original_content_assembly_unchanged','unchanged_native_runtime']):
        raise ValueError('Unverified runtime preservation')
    fna = p.parent/'fna-reuse-audit.json'
    if sha(fna) != r['fna_reuse_audit_sha256'] or json.loads(fna.read_text())['status'] != 'PASS_EXISTING_FNA_SEMANTICS_UNCHANGED':
        raise ValueError('Changed FNA semantic audit')
    repair = json.loads((p.parent/'repair.json').read_text())
    if sha(p.parent/'repair.json') != r['repair_sha256'] or repair != r['repair']:
        raise ValueError('Changed precision repair provenance')
    if repair['status'] != 'PASS_SCOPED_PLAYER_PRECISION_REPAIR' or len(repair['changed_methods']) != 4 or repair['preserved_double_precision_sites'] != 10 or repair['mixed_after'] or repair['float_sinks_after']:
        raise ValueError('Precision repairs were not preserved')
    return r, resources


def validate_upgrade_gates(managed_sha256):
    gates = json.loads((SOURCE/'EverestValidation.json').read_text())
    statuses = {'profiles':'PASS_PROFILE_BACKUPS', 'game':'PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT',
                'motion':'PASS_MOTION_VISIBILITY_RESTORED_HOST', 'vanilla':'PASS_CABRILLO_VANILLA_EVEREST_SAVE_ROUNDTRIP'}
    if gates.keys() != statuses.keys(): raise ValueError('Missing Everest upgrade gates')
    loaded = {}
    for name, status in statuses.items():
        pin = gates[name]; path = owned(pin['receipt'])
        if sha(path) != pin['sha256']: raise ValueError('Upgrade receipt changed: '+name)
        r = json.loads(path.read_text()); loaded[name] = r
        if r['status'] != status: raise ValueError('Upgrade gate did not pass: '+name)
        for n, h in r['source_sha256'].items():
            if sha(owned(n)) != h: raise ValueError('Upgrade check source changed: '+n)
        if name in {'game','motion'} and r['managed_receipt_sha256'] != managed_sha256:
            raise ValueError('Upgrade checked a different managed payload')
    if loaded['profiles']['checks'] != 119 or loaded['game']['everest_version'] != '1.6580.0':
        raise ValueError('Incomplete profile/runtime upgrade checks')
    if {(r['fps'],r['renderer']) for r in loaded['motion']['results']} != {(60,'Fast'),(120,'Fast'),(60,'Fancy'),(120,'Fancy')}:
        raise ValueError('Incomplete Motion Smoothing upgrade checks')
    if loaded['vanilla']['game_receipt_sha256'] != gates['game']['sha256']:
        raise ValueError('Vanilla roundtrip used a different game build')
