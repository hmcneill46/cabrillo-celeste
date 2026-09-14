#!/usr/bin/env python3
"""Prepare the new Everest game while preserving accepted runtime components."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
B = ROOT / '.build/ios-jit'
STAGE = B / 'launcher-runtime-managed'
GAME = B / 'launcher-runtime-everest-game'
ACCEPTED = B / 'launcher-backbuffer-managed'
SDK = B / 'managed-runtime/dotnet-sdk-8.0.422'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())

def main():
    assert not (ROOT / 'artifacts/ios-jit/launcher-runtime-20260913-27/delivery-receipt.json').exists(), 'Preserve delivered outputs.'
    subprocess.run(['python3', str(SOURCE / 'generate_runtime_identity.py')], check=True)
    STAGE.mkdir(parents=True, exist_ok=True)
    prior = read(ACCEPTED / 'receipt.json')
    for name, digest in prior['source_sha256'].items(): assert sha(ROOT / name) == digest, name
    for name, digest in prior['managed_sha256'].items():
        assert sha(ACCEPTED / name) == digest, name
        shutil.copy2(ACCEPTED / name, STAGE / name)
    preparation = read(GAME / 'preparation-receipt.json')
    for name, digest in preparation['output_sha256'].items(): assert sha(GAME / 'prepared' / name) == digest, name
    original_preparation = read(B / 'everest-game/preparation-receipt.json')
    for name in ['Celeste.Content.dll']:
        assert preparation['output_sha256'][name] == original_preparation['output_sha256'][name], name + ': review unexpected upstream change'
    for name in ['Celeste.Mod.mm.dll', 'MMHOOK_Celeste.dll']:
        shutil.copy2(GAME / 'prepared' / name, STAGE / name)
    for name in ['fna-compatibility.json', 'monomod-literal-fields.json', 'fna-graphics-compatibility.json', 'fna-backbuffer-compatibility.json']:
        shutil.copy2(ACCEPTED / name, STAGE / name)
    shutil.copytree(ACCEPTED / 'orig', STAGE / 'orig', dirs_exist_ok=True)
    assert sha(STAGE / 'orig/Celeste.exe') == preparation['original_celeste_sha256']
    env = dict(os.environ, DOTNET_ROOT=str(SDK), DOTNET_CLI_HOME=str(STAGE / 'cli-home'),
               NUGET_PACKAGES=str(B / 'launcher-runtime-everest-dependencies/nuget'),
               DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_MULTILEVEL_LOOKUP='0')
    commands = []
    def run(args, name):
        cmd = list(map(str, args)); commands.append(cmd)
        result = subprocess.run(cmd, env=env, cwd=GAME, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (STAGE / (name + '.log')).write_text(result.stdout)
        if result.returncode: raise RuntimeError(result.stdout[-9000:])
    tool = GAME / 'tools-artifacts/bin/EverestPrepare/release/EverestPrepare.dll'
    for label, path in [('old', B / 'everest-game/prepared/FNA.dll'), ('new', GAME / 'prepared/FNA.dll')]:
        run([SDK / 'dotnet', tool, 'audit', path, STAGE / ('fna-' + label + '.json')], 'audit-fna-' + label)
    before, after = read(STAGE / 'fna-old.json'), read(STAGE / 'fna-new.json')
    added_type = 'MonoMod.PatchDustBurstAttribute'
    added_method = 'System.Void MonoMod.PatchDustBurstAttribute::.ctor()'
    assert set(after['types']) - set(before['types']) == {added_type}
    assert set(after['methods']) - set(before['methods']) == {added_method}
    assert after['types'].pop(added_type) == 'BeforeFieldInit|System.Attribute'
    assert after['methods'].pop(added_method) == added_method + '|Public, HideBySig, SpecialName, RTSpecialName|IL|False||Ldarg_0:;Call:System.Void System.Attribute::.ctor();Ret:|'
    assert before == after, 'Unexpected FNA implementation change; preserve accepted renderer.'
    run([SDK / 'dotnet', tool, 'platform', GAME / 'prepared/Celeste.dll', STAGE / 'Celeste.dll', STAGE / 'platform-patch.json'], 'platform')
    run([SDK / 'dotnet', tool, 'check-fna', STAGE, STAGE / 'Celeste.dll', STAGE / 'MMHOOK_Celeste.dll'], 'check-fna')
    refs = sorted((SDK / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    names = ['Celeste.dll', 'FNA.dll', 'MMHOOK_Celeste.dll', 'MonoMod.Core.dll', 'MonoMod.RuntimeDetour.dll',
             'MonoMod.Utils.dll', 'Mono.Cecil.dll', 'NLua.dll', 'KeraLua.dll', 'Newtonsoft.Json.dll', 'CelesteIOS.dll']
    sources = sorted((SOURCE / 'managed').glob('*.cs')) + [ROOT / 'modern-ios/CelesteIOSFoundation' / n for n in ['PlatformPolicies.cs', 'TouchControlsPolicy.cs']]
    args = ['-nologo', '-nostdlib+', '-unsafe+', '-nullable:annotations', '-optimize+', '-deterministic+', '-target:library', '-out:"' + str(STAGE / 'CelesteJITEverest.dll') + '"']
    args += ['-r:"' + str(p) + '"' for p in refs + [STAGE / name for name in names]]
    args += ['"' + str(p) + '"' for p in sources]
    args += ['-resource:"' + str(p) + '",Celeste.IOSTouchControls.' + p.name for p in sorted((B / 'celeste-game/touch-assets').glob('*.a8'))]
    rsp = STAGE / 'adapter.rsp'; rsp.write_text('\n'.join(args) + '\n')
    run([SDK / 'dotnet', 'exec', SDK / 'sdk/8.0.422/Roslyn/bincore/csc.dll', '@' + str(rsp)], 'compile-adapter')
    changed = ['Celeste.Mod.mm.dll', 'Celeste.dll', 'MMHOOK_Celeste.dll', 'CelesteJITEverest.dll']
    for name, expected in prior['managed_sha256'].items():
        if name not in changed: assert sha(STAGE / name) == expected, name
    runtime_identity = read(SOURCE / 'RuntimeIdentity.json')
    source_receipt = read(B / 'launcher-runtime-everest-source/source-receipt.json')
    assert source_receipt['pins']['Everest'][1] == runtime_identity['everestSourceCommit']
    receipt = dict(schema=1, status='PASS_EVEREST_6531_PREPARED_GAME_AND_RUNTIME_ADAPTER',
        runtime_identity=runtime_identity, runtime_identity_sha256=sha(SOURCE / 'RuntimeIdentity.json'),
        accepted_everest_receipt_sha256=sha(ACCEPTED / 'receipt.json'),
        preparation_receipt_sha256=sha(GAME / 'preparation-receipt.json'),
        platform_patch_sha256=sha(STAGE / 'platform-patch.json'),
        generated_fna_audit=dict(unchanged_methods=len(before['methods']), unchanged_fields=len(before['fields']),
            unchanged_resources=len(before['resources']), added_patch_marker=added_type,
            before_sha256=sha(STAGE / 'fna-old.json'), after_sha256=sha(STAGE / 'fna-new.json'), shipped_accepted_fna=True),
        fna_compatibility_sha256=sha(STAGE / 'fna-compatibility.json'),
        fna_graphics_compatibility=prior['fna_graphics_compatibility'],
        fna_backbuffer_compatibility=prior['fna_backbuffer_compatibility'],
        mono8_utils_compatibility=prior['mono8_utils_compatibility'],
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [*sources, Path(__file__), SOURCE / 'generate_runtime_identity.py', SOURCE / 'RuntimeIdentity.json', *sorted((SOURCE / 'tools').glob('*.cs'))]},
        managed_sha256={p.name:sha(p) for p in sorted(STAGE.glob('*.dll'))},
        replaced_assemblies=changed, unchanged_accepted_assemblies=len(prior['managed_sha256'])-len(changed),
        commands=commands, host_tested=False, device_tested=False)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'])

if __name__ == '__main__': main()
