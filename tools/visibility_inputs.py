"""Require the exact build35 payload plus the restored Mono visibility object."""
import json
from pathlib import Path
from platform_inputs import ROOT, owned, sha, archive_floor, validate_managed
from platform_inputs import validate_native as validate_base
from build_visibility_runtime import members, ORIGINAL, PATCHED
from collections import Counter

SOURCE = ROOT / 'experiments/ios-jit/launcher-visibility'


def validate_native():
    base, old_libraries = validate_base()
    pin = json.loads((SOURCE / 'NativePayload.json').read_text())
    path = owned(pin['receipt'])
    if sha(path) != pin['receipt_sha256']: raise ValueError('Visibility receipt changed')
    receipt = json.loads(path.read_text())
    if receipt['status'] != 'PASS_SCOPED_VISIBILITY_RUNTIME_RESTORE' or receipt['deployment_target'] != '15.0':
        raise ValueError('Expected the scoped iOS15 visibility correction')
    if sha(owned(receipt['base_receipt'])) != receipt['base_receipt_sha256']:
        raise ValueError('Native baseline receipt changed')
    if json.loads(owned(receipt['base_receipt']).read_text()) != base:
        raise ValueError('Unexpected native baseline')
    if (receipt['original_class_sha256'], receipt['patched_class_sha256']) != (ORIGINAL, PATCHED):
        raise ValueError('Unexpected visibility source change')
    for n, h in receipt['source_sha256'].items():
        if sha(owned(n)) != h: raise ValueError('Changed runtime builder input: ' + n)
    for target in ['ios', 'host_control', 'host_fixed']:
        t = receipt[target]
        if sha(owned(t['path'])) != t['sha256']: raise ValueError('Changed visibility archive: ' + target)
        if sha(owned(t['compile_database'])) != t['compile_database_sha256']: raise ValueError('Changed compiler database')
        for n, h in t['dependencies'].items():
            if sha(owned(n)) != h: raise ValueError('Changed compiler dependency: ' + n)
    if receipt['libraries'].keys() != base['libraries'].keys(): raise ValueError('Changed native library set')
    if {n for n in base['libraries'] if receipt['libraries'][n] != base['libraries'][n]} != {'libmonosgen-2.0.a'}:
        raise ValueError('Visibility repair must replace only Mono')
    original = members(owned(base['libraries']['libmonosgen-2.0.a']['path']))
    changed = members(owned(receipt['ios']['path']))
    if sum(n == 'class.c.o' for n, _ in changed) != 1 or sum(n == 'class.c.o' for n, _ in original) != 1:
        raise ValueError('Missing or duplicate Mono metadata object')
    if Counter((n, h) for n, h in original if n != 'class.c.o') != Counter((n, h) for n, h in changed if n != 'class.c.o'):
        raise ValueError('Unrelated Mono objects changed')
    gates = json.loads((SOURCE / 'RuntimeValidation.json').read_text())
    expected = {'visibility':'PASS_VISIBILITY_FIELDS_METHODS_AND_DENIED_CONTROLS',
                'motion_control':'PASS_MOTION_VISIBILITY_ORIGINAL_CONTROL',
                'motion_fixed':'PASS_MOTION_VISIBILITY_RESTORED_HOST',
                'source_audit':'PASS_NINE_ACCEPTED_MONO_PATCH_SOURCES'}
    if gates.keys() != expected.keys(): raise ValueError('Missing native regression gates')
    for name, status in expected.items():
        gate = gates[name]; gp = owned(gate['receipt'])
        if sha(gp) != gate['sha256']: raise ValueError('Changed native regression receipt: ' + name)
        g = json.loads(gp.read_text())
        if g['status'] != status: raise ValueError('Native regression did not pass: ' + name)
        if name != 'source_audit' and g['runtime_receipt_sha256'] != sha(path):
            raise ValueError('Regression used another native correction')
        for n, h in g.get('source_sha256', {}).items():
            if sha(owned(n)) != h: raise ValueError('Changed regression source: ' + n)
        if name == 'source_audit':
            if len(g['checks']) != 9: raise ValueError('Incomplete accepted Mono patch audit')
            for row in g['checks']:
                if sha(owned(row['input'])) != row['sha256']: raise ValueError('Accepted Mono patch source changed')
    selected = []
    for old in old_libraries:
        row = dict(old)
        if Path(row['path']).name == 'libmonosgen-2.0.a':
            row.update(receipt['libraries']['libmonosgen-2.0.a'])
            row['deployment'] = archive_floor(owned(row['path']))
        selected.append(row)
    return receipt, selected
