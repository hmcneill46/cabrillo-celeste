#!/usr/bin/env python3
"""Convert and patch an isolated copy of original Celeste IL using real Everest."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/everest-game'
DEPS = ROOT / '.build/ios-jit/everest-dependencies'
REPO = ROOT / '.build/ios-jit/everest-source/Everest'
SDK = ROOT / '.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'
OWNED = Path('/Users/harrymcneill/Projects/Celeste Required Files/Celeste Untouched.app/Contents/Resources')


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / 'global.json').write_text(json.dumps({'sdk': {'version': '8.0.422', 'rollForward': 'disable'}}) + '\n')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    dep_receipt = json.loads((DEPS / 'receipt.json').read_text())
    for name, digest in dep_receipt['managed_sha256'].items():
        assert sha(DEPS / 'managed' / name) == digest, name
    env = dict(os.environ, DOTNET_ROOT=str(SDK), DOTNET_CLI_HOME=str(STAGE / 'cli-home'),
               NUGET_PACKAGES=str(DEPS / 'nuget'), DOTNET_CLI_TELEMETRY_OPTOUT='1',
               DOTNET_GENERATE_ASPNET_CERTIFICATE='false', DOTNET_MULTILEVEL_LOOKUP='0')
    commands = []

    def run(cmd, name, cwd=STAGE):
        commands.append(list(map(str, cmd)))
        with (STAGE / (name + '.log')).open('w') as stream:
            result = subprocess.run(list(map(str, cmd)), cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError((STAGE / (name + '.log')).read_text()[-11000:])

    run([SDK / 'dotnet', 'build', SOURCE / 'tools/EverestPrepare.csproj', '-c', 'Release',
         '--artifacts-path', STAGE / 'tools-artifacts', '-p:EverestLibraries=' + str(DEPS / 'managed'),
         '-p:NuGetAudit=false', '--nologo'], 'build-tool')
    tool = STAGE / 'tools-artifacts/bin/EverestPrepare/release/EverestPrepare.dll'
    assert tool.exists(), tool
    # Hash-validated original IL. Content stays owner-owned and is never changed.
    assert sha(OWNED / 'Celeste.exe') == 'fd73f8a2311fa5737ded550cbad4b75c85b7686b36432f59185e940fcb65fcfe'
    original = STAGE / 'orig'
    original.mkdir(exist_ok=True)
    for name in ['Celeste.exe', 'Celeste.Content.dll', 'FNA.dll']:
        shutil.copy2(OWNED / name, original / name)
    work = STAGE / 'prepared'
    work.mkdir(exist_ok=True)
    for source in (DEPS / 'managed').glob('*.dll'):
        shutil.copy2(source, work / source.name)
    shutil.copy2(REPO / 'lib-ext/lib64-osx/Steamworks.NET.dll', work / 'Steamworks.NET.dll')
    env['MONOMOD_DEPDIRS'] = os.pathsep.join(map(str, [work, DEPS / 'managed', original]))
    env['MONOMOD_DEPENDENCY_MISSING_THROW'] = '0'
    args = [SDK / 'dotnet', tool]
    run([*args, 'coreify', original / 'Celeste.exe', work / 'Celeste.dll'], 'coreify-celeste')
    run([*args, 'coreify', original / 'Celeste.Content.dll', work / 'Celeste.Content.dll'], 'coreify-content')
    fna = ROOT / '.build/ios-jit/graphics-managed/FNA.dll'
    assert sha(fna) == '802b6dd2fe0a6c386d1b29b48dfea358ce85fe4f2530332410bcfaa015bfcbf0'
    shutil.copy2(fna, work / 'FNA.dll')
    for name in ['FNA', 'Celeste']:
        temporary = work / (name + '.patched.dll')
        run([*args, 'patch', work / (name + '.dll'), work / 'Celeste.Mod.mm.dll', temporary], 'patch-' + name.lower())
        shutil.move(temporary, work / (name + '.dll'))
    run([*args, 'hookgen', '--private', work / 'Celeste.dll', work / 'MMHOOK_Celeste.dll'], 'hookgen')
    run([*args, 'patch', work / 'MMHOOK_Celeste.dll', work / 'Celeste.Mod.mm.dll', work / 'MMHOOK_Celeste.patched.dll'], 'relink-hooks')
    shutil.move(work / 'MMHOOK_Celeste.patched.dll', work / 'MMHOOK_Celeste.dll')
    run([*args, 'inspect', work / 'Celeste.dll'], 'game-surface')
    surface = json.loads((STAGE / 'game-surface.log').read_text())
    assert any(t['name'] == 'Celeste.Mod.Everest' for t in surface['types'])
    receipt = dict(schema=1, status='PASS_ORIGINAL_IL_COREIFY_EVEREST_PATCH_AND_HOOKGEN',
                   original_sha256={p.name: sha(p) for p in original.glob('*.dll')},
                   original_celeste_sha256=sha(original / 'Celeste.exe'),
                   accepted_fna_input_sha256=sha(fna), dependencies_receipt_sha256=sha(DEPS / 'receipt.json'),
                   output_sha256={p.name: sha(p) for p in sorted(work.glob('*.dll'))}, commands=commands,
                   platform_adapted=False, host_runtime_tested=False, device_tested=False)
    (STAGE / 'preparation-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__':
    main()
