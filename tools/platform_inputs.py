"""Validate the explicit iOS15 native overlay and every selected archive's OS floor."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/launcher-platforms'
REBUILT = {'libmonosgen-2.0.a', 'libmono-component-marshal-ilgen-static.a',
           'libmono-component-debugger-stub-static.a', 'libmono-component-hot_reload-stub-static.a',
           'libmono-component-diagnostics_tracing-stub-static.a', 'libFNA3D.a', 'liblua54.a'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def owned(name):
    p = ROOT / name
    if p.resolve() != p.absolute() or ROOT not in p.parents:
        raise ValueError('Unowned or aliased native input: ' + str(name))
    return p


def archive_floor(path):
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    architectures = subprocess.check_output(['xcrun', 'lipo', '-archs', path], env=env, text=True).split()
    if 'arm64' not in architectures:
        raise ValueError('Native archive lacks arm64: ' + str(path))
    output = subprocess.check_output(['xcrun', 'otool', '-arch', 'arm64', '-l', path], env=env, text=True)
    # LC_VERSION_MIN_IPHONEOS and LC_BUILD_VERSION encode the minimum OS per
    # object, independently of the final app's Info.plist and linker target.
    floors = re.findall(r'cmd LC_VERSION_MIN_IPHONEOS\s+cmdsize \d+\s+version ([\d.]+)', output)
    builds = re.findall(r'cmd LC_BUILD_VERSION\s+cmdsize \d+\s+platform (\w+)\s+minos ([\d.]+)', output)
    if any(platform not in {'2', 'IOS'} for platform, _ in builds):
        raise ValueError('Non-iOS object in native archive: ' + str(path))
    floors += [version for _, version in builds]
    def version(s): return tuple((list(map(int, s.split('.'))) + [0, 0])[:3])
    if not floors or any(version(v) > (15, 0, 0) for v in floors):
        raise ValueError('Native archive requires newer than iOS15: ' + str(path))
    return dict(versioned_objects=len(floors), maximum_minimum_os=max(floors, key=version), arm64=True)


def validate_native():
    pin = json.loads((SOURCE / 'NativePayload.json').read_text())
    receipt_path = owned(pin['receipt'])
    if sha(receipt_path) != pin['receipt_sha256']:
        raise ValueError('Native rebuild receipt changed')
    receipt = json.loads(receipt_path.read_text())
    if receipt['status'] != 'PASS_NATIVE_IOS15_REBUILD' or receipt['deployment_target'] != '15.0' or set(receipt['libraries']) != REBUILT:
        raise ValueError('Incomplete iOS15 rebuild')
    if sha(owned(receipt['input_manifest'])) != receipt['input_manifest_sha256']:
        raise ValueError('Private native source manifest changed')
    for name, expected in receipt['source_sha256'].items():
        if sha(owned(name)) != expected:
            raise ValueError('Native build source changed: ' + name)
    baseline = json.loads((SOURCE / 'Dependencies.json').read_text())['native_libraries']
    selected = []
    for old in baseline:
        name = Path(old['path']).name
        row = dict(receipt['libraries'].get(name, old))
        path = owned(row['path'])
        if sha(path) != row['sha256']:
            raise ValueError('Native library changed: ' + name)
        row.update(rebuilt=name in REBUILT, baseline_sha256=old['sha256'], deployment=archive_floor(path))
        selected.append(row)
    if len(selected) != 16:
        raise ValueError('Native archive set changed')
    return receipt, selected


def validate_managed(receipt_path):
    from save_transfer_inputs import validate_managed as validate_precision
    path=owned(receipt_path)
    receipt=json.loads(path.read_text())
    if receipt.get('status')!='PASS_PLATFORM_ADAPTER_BUILD' or receipt.get('schema')!=1:
        raise ValueError('Expected the verified platform adapter')
    base=owned(receipt['base_receipt'])
    expected='80bb0a19d7f63944aa6fe23379338c747db776cae51744c73482a390425b13aa'
    if sha(base)!=expected or receipt['base_receipt_sha256']!=expected:
        raise ValueError('Precision baseline changed')
    previous,_=validate_precision(base)
    for name,h in receipt['source_sha256'].items():
        if sha(owned(name))!=h:raise ValueError('Platform managed source changed: '+name)
    resources=owned(receipt['resource_root'])
    if ROOT/'.build' not in resources.parents:raise ValueError('Unexpected managed output root')
    actual={str(f.relative_to(resources)):sha(owned(f)) for f in resources.rglob('*') if f.is_file()}
    if actual!=receipt['resources'] or actual.keys()!=previous['resources'].keys():raise ValueError('Managed file set changed')
    if {n for n,h in actual.items() if h!=previous['resources'][n]}!={'Managed/CelesteJITEverest.dll'}:
        raise ValueError('Unexpected platform managed replacement')
    if sha(path.parent/'repair.json')!=previous['repair_sha256'] or receipt['repair_sha256']!=previous['repair_sha256']:
        raise ValueError('Precision provenance changed')
    return receipt,resources
