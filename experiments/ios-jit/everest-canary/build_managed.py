#!/usr/bin/env python3
"""Apply the recorded platform boundary and compile the independent entry adapter."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/everest-managed'
GAME = ROOT / '.build/ios-jit/everest-game'
SDK = ROOT / '.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DOTNET_ROOT=str(SDK), DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_MULTILEVEL_LOOKUP='0')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    receipt = json.loads((GAME / 'preparation-receipt.json').read_text())
    for name, digest in receipt['output_sha256'].items():
        assert sha(GAME / 'prepared' / name) == digest, name
        shutil.copy2(GAME / 'prepared' / name, STAGE / name)
    commands = []

    def run(args, name):
        commands.append(list(map(str, args)))
        result = subprocess.run(list(map(str, args)), cwd=GAME, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (STAGE / (name + '.log')).write_text(result.stdout)
        if result.returncode: raise RuntimeError(result.stdout[-9000:])

    tool = GAME / 'tools-artifacts/bin/EverestPrepare/release/EverestPrepare.dll'
    run([SDK / 'dotnet', 'build', SOURCE / 'tools/EverestPrepare.csproj', '-c', 'Release',
         '--artifacts-path', GAME / 'tools-artifacts',
         '-p:EverestLibraries=' + str(ROOT / '.build/ios-jit/everest-dependencies/managed'),
         '-p:NuGetAudit=false', '--nologo'], 'build-platform-tool')
    run([SDK / 'dotnet', tool, 'platform', GAME / 'prepared/Celeste.dll', STAGE / 'Celeste.dll', STAGE / 'platform-patch.json'], 'platform-patch')
    run([SDK / 'dotnet', tool, 'fna-compat', GAME / 'prepared/FNA.dll', STAGE / 'FNA.dll', STAGE / 'fna-compatibility.json'], 'fna-compatibility')
    run([SDK / 'dotnet', tool, 'check-fna', STAGE, STAGE / 'Celeste.dll', STAGE / 'MMHOOK_Celeste.dll'], 'check-fna')
    refs = sorted((SDK / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    # Reference only the runtime surface; patch assemblies contain conflicting
    # pre-merge types and belong to preparation, not adapter compilation.
    runtime_names = ['Celeste.dll', 'FNA.dll', 'MMHOOK_Celeste.dll', 'MonoMod.Core.dll', 'MonoMod.RuntimeDetour.dll', 'MonoMod.Utils.dll', 'Mono.Cecil.dll', 'NLua.dll', 'KeraLua.dll']
    sources = sorted((SOURCE / 'managed').glob('*.cs')) + [ROOT / 'modern-ios/CelesteIOSFoundation' / n for n in ['PlatformPolicies.cs', 'TouchControlsPolicy.cs']]
    output = STAGE / 'CelesteJITEverest.dll'
    args = ['-nologo', '-nostdlib+', '-unsafe+', '-nullable:annotations', '-optimize+', '-deterministic+', '-target:library', '-out:"' + str(output) + '"']
    args += ['-r:"' + str(p) + '"' for p in refs + [STAGE / name for name in runtime_names]]
    args += ['"' + str(p) + '"' for p in sources]
    assets = ROOT / '.build/ios-jit/celeste-game/touch-assets'
    args += ['-resource:"' + str(p) + '",Celeste.IOSTouchControls.' + p.name for p in sorted(assets.glob('*.a8'))]
    rsp = STAGE / 'adapter.rsp'
    rsp.write_text('\n'.join(args) + '\n')
    run([SDK / 'dotnet', 'exec', SDK / 'sdk/8.0.422/Roslyn/bincore/csc.dll', '@' + str(rsp)], 'compile-adapter')
    # The original input remains available for Everest's vanilla identity checks.
    original = STAGE / 'orig'
    original.mkdir(exist_ok=True)
    shutil.copy2(GAME / 'orig/Celeste.exe', original / 'Celeste.exe')
    result = dict(schema=1, status='PASS_EVEREST_PLATFORM_IL_AND_ENTRY_BUILD',
                  preparation_receipt_sha256=sha(GAME / 'preparation-receipt.json'),
                  platform_patch_sha256=sha(STAGE / 'platform-patch.json'),
                  fna_compatibility_sha256=sha(STAGE / 'fna-compatibility.json'),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  managed_sha256={p.name: sha(p) for p in sorted(STAGE.glob('*.dll'))},
                  commands=commands, host_tested=False, device_tested=False)
    (STAGE / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
