#!/usr/bin/env python3
"""Compile the changed59 adapter against verified public build-only metadata.

This is a local integration audit, never a payload or IPA build. Public58
dependency DLLs are explicit compiler/tool references; the shipping59 recipe
still builds those dependencies from public source. Neither a game nor the
compiled adapter is executed. No original Celeste files or private inputs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/launcher-input-fixes59'
IPA_SHA = '1226d62149d8fa5189da6c0aa5261ace9cd89962e5b458558fe7f0d67b45efa5'
TAG_SOURCE = '3bdf1713667bacedf3cd639e3c6eba3e19ac52b5'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['ipa', 'everest-archive', 'sdk', 'work']:
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    ipa, archive, sdk, work = [v.resolve() for v in [a.ipa, a.everest_archive, a.sdk, a.work]]
    if ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Use a fresh audit directory inside .build')
    if sha(ipa) != IPA_SHA:
        raise ValueError('Expected exact public v0.29.0 IPA')
    lock = ROOT / 'release/everest55-dependencies.json'
    everest = json.loads(lock.read_text())['dependencies']['Everest']
    if sha(archive) != everest['sha256']:
        raise ValueError('Expected pinned official Everest source archive')
    refs = sorted((sdk / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    if len(refs) != 163:
        raise ValueError('Expected pinned SDK8.0.422 /8.0.28 references')
    work.mkdir()
    env = dict(os.environ, DOTNET_CLI_HOME=str(work / 'cli-home'),
               DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',
               DOTNET_MULTILEVEL_LOOKUP='0', DOTNET_GENERATE_ASPNET_CERTIFICATE='false')
    commands = []

    def run(args, label):
        args = list(map(str, args))
        commands.append(args)
        with (work / (label + '.log')).open('w') as out:
            result = subprocess.run(args, env=env, cwd=work, stdout=out, stderr=subprocess.STDOUT, timeout=180)
        if result.returncode:
            raise RuntimeError(label + ': ' + (work / (label + '.log')).read_text()[-4000:])
        print('PASS ' + label, flush=True)

    run(['gh', 'attestation', 'verify', ipa, '--repo', 'hmcneill46/cabrillo-celeste',
         '--signer-workflow', 'hmcneill46/cabrillo-celeste/.github/workflows/release.yml',
         '--source-digest', TAG_SOURCE, '--source-ref', 'refs/tags/v0.29.0',
         '--deny-self-hosted-runners', '--format', 'json'], 'verify-public-ipa-attestation')
    run([sdk / 'dotnet', '--version'], 'sdk-version')
    if (work / 'sdk-version.log').read_text().strip() != '8.0.422':
        raise ValueError('Wrong audit SDK')
    tools = work / 'tools'; tools.mkdir()
    metadata = work / 'metadata'; metadata.mkdir()
    output = work / 'compiled'; output.mkdir()
    # Copy only app dependency DLLs, never platform BCL/native/game payloads.
    names = ['FNA.dll', 'Celeste.Mod.mm.dll', 'Mono.Cecil.dll', 'Mono.Cecil.Rocks.dll',
             'MonoMod.Patcher.dll', 'NETCoreifier.dll', 'MonoMod.RuntimeDetour.HookGen.dll',
             'MonoMod.Core.dll', 'MonoMod.RuntimeDetour.dll', 'MonoMod.Utils.dll',
             'MonoMod.ILHelpers.dll', 'MonoMod.Backports.dll', 'NLua.dll', 'KeraLua.dll',
             'Newtonsoft.Json.dll', 'MonoMod.Iced.dll', 'Steamworks.NET.dll',
             'Jdenticon.dll', 'DiscordGameSDK.dll', 'DotNetZip.dll', 'MAB.DotIgnore.dll',
             'YamlDotNet.dll', 'Mono.Cecil.Mdb.dll', 'Mono.Cecil.Pdb.dll']
    public_files = {}
    with zipfile.ZipFile(ipa) as z:
        for name in names + ['CelesteJITEverest.dll']:
            member = 'Payload/CelesteJITEverest.app/Managed/' + name
            matches = [x for x in z.infolist() if x.filename == member]
            if len(matches) != 1 or matches[0].file_size > 16000000:
                raise ValueError('Missing/duplicate/oversized public metadata dependency ' + member)
            dest = (metadata if name == 'CelesteJITEverest.dll' else tools) / name
            dest.write_bytes(z.read(matches[0]))
            public_files[member] = sha(dest)
    prefix = 'Everest-' + everest['commit'] + '/lib-stripped/'
    with tarfile.open(archive) as t:
        for name in ['Celeste.exe', 'FNA.dll', 'Steamworks.NET.dll']:
            matches = [m for m in t.getmembers() if m.name == prefix + name]
            if len(matches) != 1 or not matches[0].isfile() or matches[0].size > 3000000:
                raise ValueError('Invalid public stripped metadata ' + name)
            dest = metadata / name
            dest.write_bytes(t.extractfile(matches[0]).read())
            public_files[matches[0].name] = sha(dest)
    source_paths = [SOURCE / 'tools' / n for n in ['BuildReference.cs', 'Program.cs', 'AssemblyAudit.cs', 'PlatformPatch.cs', 'FnaCompatibility.cs']]
    source_paths += [SOURCE / 'preparation/BootstrapPaths.cs']
    support = sorted((ROOT / 'experiments/ios-jit/launcher-session/support-module').glob('*.cs'))
    adapter = sorted(x for x in (SOURCE / 'managed').glob('*.cs') if x.name not in {'ContentStore.cs', 'ContentLibrary.cs'})
    adapter += [ROOT / 'modern-ios/CelesteIOSFoundation' / n for n in ['PlatformPolicies.cs', 'TouchControlsPolicy.cs']]
    source_paths += support + adapter + [Path(__file__).resolve(), lock, ROOT / 'scripts/generate-ios-touch-assets.py']
    source_paths += sorted(x for x in (ROOT / 'modern-ios/Assets/TouchControls/Source').rglob('*') if x.is_file())
    hashes = {str(x.relative_to(ROOT)): sha(x) for x in source_paths}
    usings = tools / 'Usings.cs'
    usings.write_text('global using System;\nglobal using System.IO;\nglobal using System.Linq;\nglobal using System.Collections.Generic;\n')

    def compile(name, sources, extra=(), exe=False, resources=(), destination=output):
        dest = destination / (name + '.dll')
        rsp = tools / (name + '.rsp')
        args = ['-nologo', '-noconfig', '-nostdlib+', '-unsafe+', '-nullable:annotations', '-optimize+', '-deterministic+',
                '-target:' + ('exe' if exe else 'library'), '-out:"' + str(dest) + '"']
        args += ['-r:"' + str(x) + '"' for x in refs + list(extra)]
        args += ['-resource:"' + str(x) + '",' + logical for x, logical in resources]
        args += ['"' + str(x) + '"' for x in sources]
        rsp.write_text('\n'.join(args) + '\n')
        run([sdk / 'dotnet', 'exec', sdk / 'sdk/8.0.422/Roslyn/bincore/csc.dll', '@' + str(rsp)], 'compile-' + name)
        if exe:
            dest.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': {'tfm': 'net8.0', 'framework': {'name': 'Microsoft.NETCore.App', 'version': '8.0.28'}}}))
        return dest

    cecil = [tools / x for x in ['Mono.Cecil.dll', 'Mono.Cecil.Rocks.dll']]
    reference_tool = compile('BuildReference', [SOURCE / 'tools/BuildReference.cs'],
                             cecil + [tools / x for x in ['MonoMod.Patcher.dll', 'NETCoreifier.dll']], True, destination=tools)
    hook_tool = compile('EverestPrepare', source_paths[1:6] + [usings],
                        cecil + [tools / x for x in ['MonoMod.Patcher.dll', 'NETCoreifier.dll']], True, destination=tools)
    env.update(MONOMOD_DEPDIRS=os.pathsep.join(map(str, [tools, metadata])), MONOMOD_DEPENDENCY_MISSING_THROW='0')
    sandbox = work / 'audit.sb'
    policy = '(version 1)\n(allow default)\n(deny network*)\n'
    for folder in [ROOT / '.private', ROOT.parent / 'celeste-ios', ROOT.parent / 'Celeste-Everest-JIT-Apple-Platforms', ROOT.parent / 'Celeste Required Files']:
        policy += '(deny file-read* file-write* (subpath ' + json.dumps(str(folder)) + '))\n'
    sandbox.write_text(policy)
    runner = ['sandbox-exec', '-f', sandbox, sdk / 'dotnet']
    run([*runner, reference_tool, metadata / 'Celeste.exe', tools / 'Celeste.Mod.mm.dll', metadata / 'Celeste.dll'], 'build-stripped-reference')
    run([*runner, hook_tool, 'hookgen', '--private', metadata / 'Celeste.dll', metadata / 'MMHOOK_Celeste.dll'], 'build-metadata-hooks')
    game_refs = [metadata / n for n in ['Celeste.dll', 'MMHOOK_Celeste.dll']]
    game_refs += [tools / n for n in ['FNA.dll', 'MonoMod.Core.dll', 'MonoMod.RuntimeDetour.dll', 'MonoMod.Utils.dll', 'Mono.Cecil.dll', 'NLua.dll', 'KeraLua.dll', 'Newtonsoft.Json.dll']]
    module = compile('CelesteIOS', support, game_refs)
    touch = work / 'touch'
    run(['python3', ROOT / 'scripts/generate-ios-touch-assets.py', '--source-dir', ROOT / 'modern-ios/Assets/TouchControls/Source', '--output-dir', touch], 'touch-assets')
    assembly = compile('CelesteJITEverest', adapter, game_refs + [module],
                       resources=[(f, 'Celeste.IOSTouchControls.' + f.name) for f in sorted(touch.glob('*.a8'))])
    if hashes != {str(x.relative_to(ROOT)): sha(x) for x in source_paths} or sha(ipa) != IPA_SHA or sha(archive) != everest['sha256']:
        raise ValueError('Audit inputs changed')
    receipt = dict(status='PASS_INPUT_FIXES59_ADAPTER_COMPILATION_AUDIT', build_number='59',
                   scope='Compilation only, public58 dependency references; not fresh dependency/payload/IPA build',
                   adapter=str(assembly.relative_to(ROOT)), adapter_sha256=sha(assembly), adapter_source_count=len(adapter),
                   compiled_support_sha256=sha(module), source_sha256=hashes,
                   public_inputs=dict(ipa_sha256=IPA_SHA, tag='v0.29.0', source=TAG_SOURCE,
                                      everest_archive_sha256=everest['sha256'], files=public_files),
                   sdk_version='8.0.422', metadata_tools_network_denied=True, commands=commands,
                   private_or_legacy_inputs=False, game_or_adapter_executed=False,
                   full_managed_payload_built=False, ipa_built=False, physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__':
    main()
