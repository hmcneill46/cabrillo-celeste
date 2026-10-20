#!/usr/bin/env python3
"""Audit build59's compiled runtime and complete schema2 game-input catalogue.

Validate all four schema2 sources first. The unchanged, frozen Cecil auditor
then checks the actual assemblies/tool hashes using an explicit schema1 view
of the legacy source. That view is audit-only; production resources stay intact.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'experiments/ios-jit/launcher-everest6642'
BASE = ROOT / 'experiments/ios-jit/launcher-shortcut-cellular'
UNIFIED = ROOT / 'experiments/ios-jit/launcher-input-fixes59'
ORIGINAL = UNIFIED / 'OriginalGameIdentity.json'
LEGACY_ORIGINAL = ROOT / 'experiments/ios-jit/launcher-owned-game/OriginalGameIdentity.json'
LOCAL_CATALOGUE = ROOT / 'experiments/ios-jit/launcher-input-preferences/OriginalGameIdentity.json'
SOURCE = OVERLAY / 'tests/Everest6642Audit.cs'
COMMIT = '5abd7876821223c20711c1844a5187321d6e904c'
SOURCE_ARCHIVE_SHA256 = 'e5b4b25d332390e53c46e33115629ab9bbdb38ef408000a81ada2698a6aa988e'
PREVIOUS_PUBLIC54_SHA256 = 'e3520bced1ff72886d2b1796ee1420f797df71a514ee9b9e0430fd933e18a583'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def regular(path):
    if not path.is_file() or path.is_symlink() or path.resolve() != path:
        raise ValueError('Expected a regular, unaliased input: ' + str(path))
    return path


def local(name):
    path = (ROOT / name).absolute()
    if ROOT not in path.parents or path.resolve() != path:
        raise ValueError('Expected a repository input: ' + str(name))
    return regular(path)


def catalogue_projection(recipe, catalogue, legacy):
    """Check every actual schema2 input; return a view for the frozen Cecil audit."""
    if (not isinstance(recipe, dict) or set(recipe) != {'schema', 'legacy_source_id', 'sources', 'tools'}
            or recipe.get('schema') != 2 or not isinstance(recipe.get('tools'), dict)):
        raise ValueError('Expected the complete schema2 preparation recipe')
    if {name: value for name, value in recipe.items() if name != 'tools'} != catalogue:
        raise ValueError('Preparation recipe differs from the selected input catalogue')
    sources = recipe['sources']
    if not isinstance(sources, list) or len(sources) != 4:
        raise ValueError('Build59 must preserve all four supported game input combinations')
    expected_names = {
        'standard': {'Celeste.exe', 'Celeste.Content.dll', 'FNA.dll'},
        'empty-content': {'Celeste.exe', 'FNA.dll'},
        'steam': {'Celeste.exe', 'Celeste.Content.dll', 'FNA.dll', 'Steamworks.NET.dll'},
    }
    seen = set()
    kinds = []
    for source in sources:
        if not isinstance(source, dict) or set(source) != {'source_id', 'kind', 'inputs'}:
            raise ValueError('Unexpected source catalogue fields')
        kind = source['kind']; pins = source['inputs']
        if kind not in expected_names or not isinstance(pins, dict) or set(pins) != expected_names[kind]:
            raise ValueError('Unsupported original game input adaptation or files')
        canonical = ''
        for name, row in sorted(pins.items()):
            if (not isinstance(row, dict) or set(row) != {'bytes', 'sha256'}
                    or type(row['bytes']) is not int or not 0 < row['bytes'] <= 32 * 1024 * 1024
                    or not isinstance(row['sha256'], str) or len(row['sha256']) != 64
                    or any(c not in '0123456789abcdef' for c in row['sha256'])):
                raise ValueError('Invalid original game file pin')
            canonical += name + '\0' + str(row['bytes']) + '\0' + row['sha256'] + '\n'
        source_id = hashlib.sha256(canonical.encode()).hexdigest()
        if source['source_id'] != source_id or source_id in seen:
            raise ValueError('Game source identity is not unique and canonical')
        seen.add(source_id); kinds.append(kind)
    if sorted(kinds) != ['empty-content', 'standard', 'steam', 'steam']:
        raise ValueError('Build59 lost a supported input adaptation')
    old = next((source for source in sources if source['source_id'] == recipe['legacy_source_id']), None)
    if (old is None or old['kind'] != 'standard' or legacy.get('schema') != 1
            or old['source_id'] != legacy.get('source_id') or old['inputs'] != legacy.get('inputs')):
        raise ValueError('The original schema1 game identity was not preserved')
    # Do not edit the actual recipe or pretend the projection is a runtime input.
    projection = dict(schema=1, source_id=old['source_id'], inputs=old['inputs'], tools=recipe['tools'])
    return projection, dict(schema=2, source_count=len(sources), source_ids=sorted(seen),
                            canonical_source_ids=True, legacy_identity_preserved=True,
                            kinds=sorted(kinds), source_catalogue_matches=True)


def native_identity():
    original = read(BASE / 'RuntimeIdentity.json')
    expected = json.loads(json.dumps(original))
    expected['everestSourceCommit'] = COMMIT
    expected['builtins']['Everest'] = expected['builtins']['EverestCore'] = '1.6642.0'
    manifest = OVERLAY / 'RuntimeIdentity.json'
    if read(manifest) != expected:
        raise ValueError('The retained runtime manifest differs from its selected stable source/policy')
    old_commit = original['everestSourceCommit']
    old_version = original['builtins']['Everest']
    for relative in ['native/RuntimeIdentity.swift', 'managed/RuntimeIdentity.cs']:
        generated = (BASE / relative).read_text()
        generated = generated.replace(sha(BASE / 'RuntimeIdentity.json'), sha(manifest))
        generated = generated.replace(old_commit, COMMIT)
        generated = generated.replace(old_version + '-cjit-' + old_commit[:7], '1.6642.0-cjit-5abd787')
        generated = generated.replace(old_version, '1.6642.0')
        if (OVERLAY / relative).read_text() != generated:
            raise ValueError('Generated native/managed identity differs: ' + relative)
    for relative in ['RuntimeIdentity.json', 'native/RuntimeIdentity.swift', 'managed/RuntimeIdentity.cs']:
        if (UNIFIED / relative).read_bytes() != (OVERLAY / relative).read_bytes():
            raise ValueError('Selected build59 runtime identity differs: ' + relative)
    return UNIFIED / 'RuntimeIdentity.json'


def previous_recipe(ipa, current):
    regular(ipa)
    if sha(ipa) != PREVIOUS_PUBLIC54_SHA256:
        raise ValueError('Use the exact published v0.24.3/build54 IPA for the previous-recipe comparison')
    prefix = 'Payload/CelesteJITEverest.app/'
    with zipfile.ZipFile(ipa) as archive:
        info = json.loads(archive.read(prefix + 'BuildInfo.json'))
        settings = plistlib.loads(archive.read(prefix + 'Info.plist'))
        previous_bytes = archive.read(prefix + 'OwnedGameRecipe.json')
    previous = json.loads(previous_bytes)
    if (info['build_number'] != '54' or settings['CFBundleVersion'] != '54'
            or settings['CFBundleIdentifier'] != 'io.github.hmcneill46.celeste.everest.jit.everest'
            or info['game_code_recipe_sha256'] != hashlib.sha256(previous_bytes).hexdigest()):
        raise ValueError('Previous public IPA identity or preparation recipe differs')
    if previous['source_id'] != current['source_id'] or previous['inputs'] != current['inputs']:
        raise ValueError('The upgrade changed original game input/source identities')
    changed = sorted(name for name in previous['tools'].keys() | current['tools'].keys()
                     if previous['tools'].get(name) != current['tools'].get(name))
    if ('Celeste.Mod.mm.dll' not in changed or not changed
            or previous == current):
        raise ValueError('The upgrade did not change the patch/preparation recipe')
    return dict(status='PASS_PREVIOUS54_RECIPE_COMPARISON', ipa_sha256=sha(ipa),
                original_source_and_inputs_unchanged=True, changed_tools=changed,
                previous_recipe_sha256=hashlib.sha256(previous_bytes).hexdigest())


def main():
    from compile_release59 import validate_overlay, IDENTITY
    validate_overlay(read(IDENTITY / 'Dependencies.json'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--managed', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--previous-ipa', type=Path)
    args = parser.parse_args()
    managed_receipt = regular(args.managed.absolute())
    managed_receipt_hash = sha(managed_receipt)
    receipt = read(managed_receipt)
    if receipt.get('status') != 'PASS_PUBLIC_GAME_FREE_MANAGED_BUILD' or receipt.get('game_files_used') is not False or receipt.get('private_capsule_used') is not False:
        raise ValueError('Expected a fresh public game-free managed receipt')
    inputs_receipt = regular(Path(receipt['input_receipt']).absolute())
    inputs_receipt_hash = sha(inputs_receipt)
    inputs = inputs_receipt.parent
    if sha(inputs_receipt) != receipt['input_receipt_sha256']:
        raise ValueError('Managed input receipt changed')
    public = read(inputs_receipt)
    if public.get('status') != 'PASS_PUBLIC_SOURCE_INPUTS' or public['dependencies']['Everest']['commit'] != COMMIT or public['dependencies']['Everest']['sha256'] != SOURCE_ARCHIVE_SHA256:
        raise ValueError('Managed build did not use the pinned stable6642 public source')
    arch = public['sdk_arch']
    if arch not in {'x64', 'arm64'}:
        raise ValueError('Unsupported pinned SDK host')
    sdk_name = 'sdk8.0-osx-' + arch
    lock = read(ROOT / 'release/owned-game-dependencies.json')['dependencies']
    if public['dependencies'][sdk_name] != lock[sdk_name]:
        raise ValueError('The managed build changed the pinned SDK8 input')
    from verify_release_nuget import verify_packages
    verify_packages(receipt['nuget_packages'], arch)
    resources = managed_receipt.parent / 'resources'
    actual_resources = {str(path.relative_to(resources)): sha(regular(path))
                        for path in resources.rglob('*') if path.is_file()}
    if actual_resources != receipt['resources']:
        raise ValueError('Managed resources differ from their fresh build receipt')
    for name, digest in receipt['source_sha256'].items():
        if sha(local(name)) != digest:
            raise ValueError('Managed source changed: ' + name)
    runtime = native_identity()
    managed = resources / 'Managed'
    recipe = regular(resources / 'OwnedGameRecipe.json')
    catalogue = read(ORIGINAL)
    if catalogue != read(LOCAL_CATALOGUE):
        raise ValueError('Build59 changed the preserved local game-input catalogue')
    projection, catalogue_audit = catalogue_projection(read(recipe), catalogue, read(LEGACY_ORIGINAL))
    cecil = regular(managed / 'Mono.Cecil.dll')
    sdk = inputs / sdk_name
    dotnet = regular(sdk / 'dotnet')
    compiler = regular(sdk / 'sdk/8.0.422/Roslyn/bincore/csc.dll')
    references = sorted((sdk / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    if len(references) < 100:
        raise ValueError('The pinned SDK8 reference pack is missing')
    for path in [dotnet, compiler, *references]:
        relative = str(path.relative_to(inputs))
        if public['files'].get(relative) != sha(regular(path)):
            raise ValueError('Pinned SDK8 compiler/reference changed: ' + relative)
    work = args.work.absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Choose a fresh, unaliased work directory under .build')
    sources = [Path(__file__).resolve(), SOURCE, runtime, ORIGINAL, LEGACY_ORIGINAL, LOCAL_CATALOGUE,
               UNIFIED / 'native/RuntimeIdentity.swift', UNIFIED / 'managed/RuntimeIdentity.cs',
               OVERLAY / 'native/RuntimeIdentity.swift', OVERLAY / 'managed/RuntimeIdentity.cs',
               BASE / 'RuntimeIdentity.json', BASE / 'native/RuntimeIdentity.swift', BASE / 'managed/RuntimeIdentity.cs',
               ROOT / 'release/owned-game-dependencies.json', ROOT / 'tools/verify_release_nuget.py',
               ROOT / 'release/owned-game-nuget.json', ROOT / 'release/nuget-hosts.json']
    hashes = {str(path.relative_to(ROOT)): sha(regular(path)) for path in sources}
    work.mkdir(parents=True)
    audit_recipe = work / 'legacy-audit-view.json'
    audit_recipe.write_text(json.dumps(projection, indent=2) + '\n')
    shutil.copyfile(cecil, work / 'Mono.Cecil.dll')
    auditor = work / 'Everest6642Audit.dll'
    def quote(path):
        value = str(path)
        if any(character in value for character in ['"', '\n', '\r']):
            raise ValueError('Unsupported compiler input path')
        return '"' + value + '"'
    response = work / 'audit.rsp'
    response.write_text('\n'.join(['-nologo', '-nostdlib+', '-target:exe', '-optimize+',
                                  '-deterministic+', '-out:' + quote(auditor)] +
                                 ['-r:' + quote(path) for path in [*references, cecil]] + [quote(SOURCE)]) + '\n')
    auditor.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': {
        'tfm': 'net8.0', 'framework': {'name': 'Microsoft.NETCore.App', 'version': '8.0.28'}}}) + '\n')
    env = dict(os.environ, DOTNET_ROOT=str(sdk), DOTNET_CLI_HOME=str(work / 'cli-home'), DOTNET_CLI_TELEMETRY_OPTOUT='1',
               DOTNET_MULTILEVEL_LOOKUP='0', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', DOTNET_GENERATE_ASPNET_CERTIFICATE='false')
    commands = []
    def run(command, label, reject=None):
        command = list(map(str, command)); commands.append(command)
        result = subprocess.run(command, env=env, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (work / (label + '.log')).write_text(result.stdout)
        if reject:
            if result.returncode != 2 or reject not in result.stdout:
                raise RuntimeError('The ' + label + ' failure control did not reject its intended defect')
        elif result.returncode:
            raise RuntimeError(label + ' failed; see ' + str(work / (label + '.log')))
        print('PASS ' + label, flush=True)
    run([dotnet, 'exec', compiler, '-noconfig', '@' + str(response)], 'compile-auditor')
    command = [dotnet, auditor]
    run([*command, managed, audit_recipe, runtime, LEGACY_ORIGINAL, work / 'audit.json'], 'audit-actual-managed')
    report = read(work / 'audit.json')
    bad_recipe = read(audit_recipe)
    bad_recipe['tools']['Celeste.Mod.mm.dll'] = '0' * 64
    stale = work / 'stale-recipe.json'
    stale.write_text(json.dumps(bad_recipe) + '\n')
    run([*command, managed, stale, runtime, LEGACY_ORIGINAL, work / 'unexpected-stale-report.json'],
        'reject-stale-recipe', 'Recipe hash matches: Celeste.Mod.mm.dll')
    control = work / 'wrong-version-managed'
    control.mkdir()
    for path in managed.glob('*.dll'):
        if path.name != 'Celeste.Mod.mm.dll':
            shutil.copyfile(path, control / path.name)
    run([*command, 'rewrite-version-control', managed / 'Celeste.Mod.mm.dll', control / 'Celeste.Mod.mm.dll'], 'create-wrong-version-control')
    run([*command, control, audit_recipe, runtime, LEGACY_ORIGINAL, work / 'unexpected-version-report.json'],
        'reject-wrong-version', 'Everest VersionString matches stable6642')
    comparison = previous_recipe(args.previous_ipa.absolute(), projection) if args.previous_ipa else None
    if (hashes != {name: sha(ROOT / name) for name in hashes}
            or sha(managed_receipt) != managed_receipt_hash or sha(inputs_receipt) != inputs_receipt_hash):
        raise RuntimeError('Audit source or managed receipt changed during verification')
    if actual_resources != {str(path.relative_to(resources)): sha(path) for path in resources.rglob('*') if path.is_file()}:
        raise RuntimeError('The audit changed production managed resources')
    result = dict(status='PASS_BUILD59_COMPILED_MANAGED_PAYLOAD', source_sha256=hashes,
                  managed_receipt_sha256=managed_receipt_hash, input_receipt_sha256=inputs_receipt_hash,
                  runtime_manifest_sha256=sha(runtime), sdk_arch=arch, cecil_sha256=sha(cecil),
                  actual_recipe_sha256=sha(recipe), catalogue=catalogue_audit,
                  legacy_audit_view_sha256=sha(audit_recipe), legacy_view_is_audit_only=True,
                  audit_report_sha256=sha(work / 'audit.json'), checks=len(report['checks']),
                  negative_controls=['wrong_compiled_everest_version', 'stale_preparation_tool_hash'],
                  previous54_recipe=comparison, commands=commands,
                  native_generated_identity_agrees=True, native_objects_tested=False,
                  auditor_executed=True, game_or_adapter_executed=False,
                  ios_jit_executed=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
