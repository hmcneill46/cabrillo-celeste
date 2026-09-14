#!/usr/bin/env python3
"""Build real pinned Everest tools/loader and the iOS-capable MonoMod backend."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
REPO = ROOT / '.build/ios-jit/everest-source/Everest'
STAGE = ROOT / '.build/ios-jit/everest-dependencies'
SDK = ROOT / '.build/ios-jit/hook-runtime/dotnet-sdk-9.0.300'


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    subprocess.run(['python3', str(SOURCE / 'patch_everest_source.py')], check=True)
    assert subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip() == '4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00'
    env = dict(os.environ, DOTNET_ROOT=str(SDK), DOTNET_CLI_HOME=str(STAGE / 'cli-home'),
               NUGET_PACKAGES=str(STAGE / 'nuget'), NUGET_HTTP_CACHE_PATH=str(STAGE / 'http-cache'),
               DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_MULTILEVEL_LOOKUP='0', DOTNET_GENERATE_ASPNET_CERTIFICATE='false',
               DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    command = [str(SDK / 'dotnet'), 'build', 'Celeste.Mod.mm/Celeste.Mod.mm.csproj', '-c', 'Release',
               '-p:CJAppleJitCanary=true', '-p:DoNotAddSuffix=true', '-p:CecilVersion=0.11.6',
               '-p:RestoreLockedMode=false', '-p:NuGetAudit=false', '-p:BuildInParallel=false',
               '-p:CopyLocalLockFileAssemblies=true', '-p:ShouldIncludeNativeLua=false', '--nologo']
    with (STAGE / 'build.log').open('w') as stream:
        result = subprocess.run(command, cwd=REPO, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        print((STAGE / 'build.log').read_text()[-12000:])
        raise SystemExit(result.returncode)
    output = REPO / 'Celeste.Mod.mm/bin/Release/net8.0'
    managed = STAGE / 'managed'
    managed.mkdir(exist_ok=True)
    for path in [*output.glob('*.dll'), *output.glob('*.xml')]:
        shutil.copy2(path, managed / path.name)
    required = ['Celeste.Mod.mm.dll', 'NETCoreifier.dll', 'MonoMod.Patcher.dll',
                'MonoMod.RuntimeDetour.HookGen.dll', 'MonoMod.RuntimeDetour.dll', 'NLua.dll', 'KeraLua.dll']
    assert all((managed / name).exists() for name in required)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    packages = {}
    for assets in REPO.rglob('project.assets.json'):
        for key, value in json.loads(assets.read_text()).get('libraries', {}).items():
            if value.get('type') == 'package':
                packages[key] = value.get('sha512')
    receipt = dict(schema=1, status='PASS_PINNED_EVEREST_MANAGED_BUILD', command=command,
                   source_receipt_sha256=sha(REPO.parent / 'source-receipt.json'),
                   embedded_source_patch_sha256=sha(REPO.parent / 'embedded-source-patch.json'),
                   managed_sha256={p.name: sha(p) for p in sorted(managed.glob('*.dll'))},
                   packages_sha512=packages, log_sha256=sha(STAGE / 'build.log'),
                   game_prepared=False, host_runtime_tested=False, device_tested=False)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], len(receipt['managed_sha256']), 'assemblies', flush=True)


if __name__ == '__main__':
    main()
