#!/usr/bin/env python3
"""Build game-free managed payload from public inputs, without Celeste files."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
from compile_owned_game import ROOT, SOURCE, compile_bootstrap, write_recipe, sha


def build(inputs, work):
    if work.exists(): raise ValueError('Choose a fresh managed build directory')
    receipt = json.loads((inputs / 'receipt.json').read_text())
    assert receipt['status'] == 'PASS_PUBLIC_SOURCE_INPUTS'
    input_hash = sha(inputs / 'receipt.json')
    for name, expected in receipt['files'].items():
        if sha(inputs / name) != expected: raise ValueError('Public input changed: ' + name)
    checked_sources = [Path(__file__), ROOT / 'tools/compile_owned_game.py',
        ROOT / 'experiments/ios-jit/hook-canary/monomod/AppleJitSystem.cs',
        ROOT / 'experiments/ios-jit/graphics-canary/managed/ExternalGameLoop.cs',
        ROOT / 'scripts/generate-ios-touch-assets.py', SOURCE / 'OriginalGameIdentity.json',
        SOURCE / 'GameContentManifest.json', SOURCE / 'public-build/StableTouchSlotPolicy.cs']
    for folder in [SOURCE / 'managed', SOURCE / 'preparation', SOURCE / 'tools',
                   ROOT / 'experiments/ios-jit/launcher-session/support-module',
                   ROOT / 'experiments/ios-jit/everest-canary/mods', ROOT / 'modern-ios/Assets/TouchControls/Source',
                   ROOT / 'modern-ios/CelesteIOSFoundation']:
        checked_sources += sorted(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in checked_sources}
    work.mkdir(parents=True)
    arch = receipt['sdk_arch']
    sdk8, sdk9 = [inputs / ('sdk' + version + '-osx-' + arch) for version in ['8.0', '9.0']]
    env = dict(os.environ, DOTNET_CLI_HOME=str(work / 'cli-home'), NUGET_PACKAGES=str(work / 'nuget'),
               NUGET_HTTP_CACHE_PATH=str(work / 'http-cache'), DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_MULTILEVEL_LOOKUP='0',
               DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', DOTNET_GENERATE_ASPNET_CERTIFICATE='false')
    commands = []
    def run(command, label, cwd=None):
        command = list(map(str, command)); commands.append(command)
        with (work / (label + '.log')).open('w') as stream:
            result = subprocess.run(command, cwd=cwd or work, env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode: raise RuntimeError(label + ' failed: ' + str(work / (label + '.log')))
        print('PASS ' + label, flush=True)
    repo = work / 'Everest'
    run(['cp', '-cR', inputs / 'Everest', repo], 'copy-everest')
    shutil.copyfile(ROOT / 'experiments/ios-jit/hook-canary/monomod/AppleJitSystem.cs',
                    repo / 'external/MonoMod/src/MonoMod.Core/Platforms/Systems/AppleJitSystem.cs')
    run([sdk9 / 'dotnet', 'build', 'Celeste.Mod.mm/Celeste.Mod.mm.csproj', '-c', 'Release',
         '-p:CJAppleJitCanary=true', '-p:DoNotAddSuffix=true', '-p:CecilVersion=0.11.6',
         '-p:RestoreLockedMode=false', '-p:NuGetAudit=false', '-p:BuildInParallel=false',
         '-p:CopyLocalLockFileAssemblies=true', '-p:ShouldIncludeNativeLua=false', '--nologo'], 'everest', repo)
    deps = repo / 'Celeste.Mod.mm/bin/Release/net8.0'
    resources = work / 'resources'; managed = resources / 'Managed'; managed.mkdir(parents=True)
    pack = inputs / 'mono-ios-arm64/runtimes/ios-arm64'
    for path in [*sorted((pack / 'lib/net8.0').glob('*.dll')), pack / 'native/System.Private.CoreLib.dll']:
        shutil.copyfile(path, managed / path.name)
    excluded = {'Celeste.dll', 'Celeste.exe', 'Celeste.Content.dll', 'MMHOOK_Celeste.dll', 'FNA.dll', 'EverestSplash.dll'}
    for path in deps.glob('*.dll'):
        if path.name not in excluded: shutil.copyfile(path, managed / path.name)
    shutil.copyfile(repo / 'lib-ext/lib64-osx/Steamworks.NET.dll', managed / 'Steamworks.NET.dll')
    refs = sorted((sdk8 / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    compiler = [sdk8 / 'dotnet', 'exec', sdk8 / 'sdk/8.0.422/Roslyn/bincore/csc.dll']
    tools = work / 'tools'; tools.mkdir()
    for f in deps.glob('*.dll'): shutil.copyfile(f, tools / f.name)
    usings = tools / 'GlobalUsings.cs'
    usings.write_text('global using System;\nglobal using System.IO;\nglobal using System.Linq;\nglobal using System.Collections.Generic;\n')
    def compile(name, sources, extra=(), exe=True, destination=None, resources=(), defines=()):
        output = (destination or tools) / (name + '.dll')
        rsp = tools / (name + '.rsp')
        arguments = ['-nologo', '-noconfig', '-nostdlib+', '-unsafe+', '-nullable:annotations', '-optimize+', '-deterministic+',
                     '-target:' + ('exe' if exe else 'library'), '-out:"' + str(output) + '"']
        arguments += ['-define:' + define for define in defines]
        arguments += ['-r:"' + str(f) + '"' for f in refs + list(extra)]
        arguments += ['-resource:"' + str(f) + '",' + logical for f, logical in resources]
        arguments += ['"' + str(f) + '"' for f in sources]
        rsp.write_text('\n'.join(arguments) + '\n')
        run([*compiler, '@' + str(rsp)], 'compile-' + name)
        if exe:
            output.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': {'tfm': 'net8.0', 'framework': {'name': 'Microsoft.NETCore.App', 'version': '8.0.28'}}}))
        return output
    libs = lambda names: [managed / n for n in names]
    cecil = libs(['Mono.Cecil.dll', 'Mono.Cecil.Rocks.dll'])
    tool = compile('EverestPrepare', [SOURCE / 'tools' / n for n in ['Program.cs', 'AssemblyAudit.cs', 'PlatformPatch.cs', 'FnaCompatibility.cs']] +
                   [SOURCE / 'preparation/BootstrapPaths.cs', usings], cecil + libs(['MonoMod.Patcher.dll', 'NETCoreifier.dll']))
    runner = [sdk8 / 'dotnet', tool]
    env.update(MONOMOD_DEPDIRS=os.pathsep.join(map(str, [managed, deps, repo / 'lib-stripped'])), MONOMOD_DEPENDENCY_MISSING_THROW='0')
    fna_sources = sorted(f for f in (inputs / 'FNA/src').rglob('*.cs') if f.relative_to(inputs / 'FNA/src').as_posix() not in {'Graphics/FNA3D.cs', 'FrameworkDispatcher.cs'})
    fna_sources += sorted((inputs / 'bindings').glob('*.cs')) + [SOURCE / 'public-build/StableTouchSlotPolicy.cs', ROOT / 'experiments/ios-jit/graphics-canary/managed/ExternalGameLoop.cs']
    fna_effects = [(f, 'Microsoft.Xna.Framework.Graphics.Effect.Resources.' + f.name) for f in sorted((inputs / 'FNA/src/Graphics/Effect').rglob('*.fxb'))]
    compile('FNA', fna_sources, exe=False, destination=managed, resources=fna_effects, defines=['NETSTANDARD2_0'])
    run([*runner, 'patch', managed / 'FNA.dll', managed / 'Celeste.Mod.mm.dll', managed / 'FNA.patched.dll'], 'patch-fna')
    (managed / 'FNA.patched.dll').replace(managed / 'FNA.dll')
    run([*runner, 'fna-compat', managed / 'FNA.dll', managed / 'FNA.patched.dll', work / 'fna-query.json'], 'fna-query')
    (managed / 'FNA.patched.dll').replace(managed / 'FNA.dll')
    for name in ['FnaGraphicsCompatibility', 'PatchFnaBackbuffer', 'PatchMonoMod', 'PatchReflectionFlags']:
        compile(name, [SOURCE / 'tools' / (name + '.cs')], cecil)
    run([sdk8 / 'dotnet', tools / 'FnaGraphicsCompatibility.dll', 'patch', managed / 'FNA.dll', managed / 'FNA.patched.dll', work / 'fna-targets.json', sha(managed / 'FNA.dll')], 'fna-targets')
    (managed / 'FNA.patched.dll').replace(managed / 'FNA.dll')
    guard = compile('BackbufferReadGuard', [SOURCE / 'tools/BackbufferReadGuard.cs'], exe=False)
    run([sdk8 / 'dotnet', tools / 'PatchFnaBackbuffer.dll', managed / 'FNA.dll', guard, managed / 'FNA.patched.dll', work / 'fna-backbuffer.json', sha(managed / 'FNA.dll')], 'fna-backbuffer')
    (managed / 'FNA.patched.dll').replace(managed / 'FNA.dll')
    literal = compile('LiteralFieldEmitter', [SOURCE / 'tools/LiteralFieldEmitter.cs'], cecil + libs(['MonoMod.Utils.dll']), exe=False)
    run([sdk8 / 'dotnet', tools / 'PatchMonoMod.dll', managed / 'MonoMod.Utils.dll', literal, managed / 'MonoMod.Utils.patched.dll', work / 'monomod-literal.json', sha(managed / 'MonoMod.Utils.dll')], 'monomod-literal')
    (managed / 'MonoMod.Utils.patched.dll').replace(managed / 'MonoMod.Utils.dll')
    corelib = managed / 'System.Private.CoreLib.dll'
    run([sdk8 / 'dotnet', tools / 'PatchReflectionFlags.dll', corelib, sha(corelib), managed / 'CoreLib.patched.dll', work / 'reflection.json'], 'reflection')
    (managed / 'CoreLib.patched.dll').replace(corelib)
    reference = work / 'reference'; reference.mkdir()
    reference_tool = compile('BuildReference', [SOURCE / 'tools/BuildReference.cs'], cecil + libs(['MonoMod.Patcher.dll', 'NETCoreifier.dll']))
    run([sdk8 / 'dotnet', reference_tool, repo / 'lib-stripped/Celeste.exe', managed / 'Celeste.Mod.mm.dll', reference / 'Celeste.dll'], 'public-reference')
    run([*runner, 'hookgen', '--private', reference / 'Celeste.dll', reference / 'MMHOOK_Celeste.dll'], 'reference-hooks')
    # References are build-only stripped metadata, never payload files.
    game_refs = [reference / 'Celeste.dll', reference / 'MMHOOK_Celeste.dll'] + libs(['FNA.dll', 'MonoMod.Core.dll', 'MonoMod.RuntimeDetour.dll', 'MonoMod.Utils.dll', 'Mono.Cecil.dll', 'NLua.dll', 'KeraLua.dll', 'Newtonsoft.Json.dll'])
    support = ROOT / 'experiments/ios-jit/launcher-session/support-module'
    compile('CelesteIOS', sorted(support.glob('*.cs')), game_refs, exe=False, destination=managed)
    touch = work / 'touch'
    run(['python3', ROOT / 'scripts/generate-ios-touch-assets.py', '--source-dir', ROOT / 'modern-ios/Assets/TouchControls/Source', '--output-dir', touch], 'touch-assets')
    adapter = sorted(f for f in (SOURCE / 'managed').glob('*.cs') if f.name not in {'ContentStore.cs', 'ContentLibrary.cs'})
    adapter += [ROOT / 'modern-ios/CelesteIOSFoundation' / n for n in ['PlatformPolicies.cs', 'TouchControlsPolicy.cs']]
    compile('CelesteJITEverest', adapter, game_refs + libs(['CelesteIOS.dll']), exe=False, destination=managed,
            resources=[(f, 'Celeste.IOSTouchControls.' + f.name) for f in sorted(touch.glob('*.a8'))])
    canary = compile('CJITCodeCanary', sorted((ROOT / 'experiments/ios-jit/everest-canary/mods').glob('*.cs')), game_refs, exe=False)
    with zipfile.ZipFile(resources / 'CJITCodeCanary-v1.0.0.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        files = {'CJITCodeCanary.dll': canary.read_bytes(),
                 'everest.yaml': b'- Name: CJITCodeCanary\n  Version: 1.0.0\n  DLL: CJITCodeCanary.dll\n  Dependencies:\n    - Name: Everest\n      Version: 1.6458.0\n'}
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 25, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    resolver_patch = compile('PatchCecilOwnedGame', [SOURCE / 'tools/PatchCecilOwnedGame.cs'], cecil)
    run([sdk8 / 'dotnet', resolver_patch, managed / 'Mono.Cecil.dll', managed / 'Mono.Cecil.patched.dll', work / 'cecil-owned-game.json'], 'cecil-owned-game')
    (managed / 'Mono.Cecil.patched.dll').replace(managed / 'Mono.Cecil.dll')
    compile_bootstrap(sdk8, managed, work, run)
    for pdb in managed.glob('*.pdb'): pdb.unlink()
    original = json.loads((SOURCE / 'OriginalGameIdentity.json').read_text())
    write_recipe(original['inputs'], managed, resources / 'OwnedGameRecipe.json')
    shutil.copyfile(SOURCE / 'GameContentManifest.json', resources / 'GameContentManifest.json')
    assert not any((managed / name).exists() for name in excluded if name != 'FNA.dll')
    assert sha(inputs / 'receipt.json') == input_hash
    assert source_hashes == {str(p.relative_to(ROOT)): sha(p) for p in checked_sources}, 'Source changed during compilation'
    result = dict(schema=1, status='PASS_PUBLIC_GAME_FREE_MANAGED_BUILD', input_receipt_sha256=input_hash,
                  input_receipt=str(inputs / 'receipt.json'), game_files_used=False, private_capsule_used=False,
                  resources={str(f.relative_to(resources)): sha(f) for f in sorted(resources.rglob('*')) if f.is_file()}, commands=commands,
                  source_sha256=source_hashes,
                  nuget_packages={str(p.relative_to(work / 'nuget')): sha(p) for p in sorted((work / 'nuget').rglob('*.nupkg'))},
                  physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'], flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--inputs', required=True); p.add_argument('--work', required=True)
    args = p.parse_args(); build(Path(args.inputs).resolve(), Path(args.work).resolve())
