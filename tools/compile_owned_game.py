#!/usr/bin/env python3
"""Compile the game-free bootstrap from explicit SDK and public tool inputs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/ios-jit/launcher-owned-game'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_bootstrap(sdk, managed, work, run, extra_sources=()):
    refs = sorted((sdk / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    assert len(refs) > 100
    names = ['Mono.Cecil.dll', 'Mono.Cecil.Rocks.dll', 'NETCoreifier.dll', 'MonoMod.Patcher.dll']
    usings = work / 'PreparationUsings.cs'
    usings.write_text('global using System;\nglobal using System.IO;\nglobal using System.Linq;\nglobal using System.Collections.Generic;\n')
    sources = [*sorted((SOURCE / 'preparation').glob('*.cs')), SOURCE / 'managed/ContentStore.cs',
               SOURCE / 'tools/PlatformPatch.cs', SOURCE / 'tools/RepairPlayerPrecision.cs', usings, *extra_sources]
    rsp = work / 'bootstrap.rsp'
    rsp.write_text('\n'.join(['-nologo', '-nostdlib+', '-target:library', '-optimize+', '-deterministic+',
        '-nullable:annotations', '-out:"' + str(managed / 'Cabrillo.Bootstrap.dll') + '"'] +
        ['-r:"' + str(f) + '"' for f in refs + [managed / n for n in names]] +
        ['"' + str(f) + '"' for f in sources]) + '\n')
    run([sdk / 'dotnet', 'exec', sdk / 'sdk/8.0.422/Roslyn/bincore/csc.dll', '@' + str(rsp)], 'compile-bootstrap')


def write_recipe(original_pins, managed, destination):
    canonical = ''.join(n + '\0' + str(p['bytes']) + '\0' + p['sha256'] + '\n' for n, p in sorted(original_pins.items()))
    tools = ['Cabrillo.Bootstrap.dll', 'Celeste.Mod.mm.dll', 'NETCoreifier.dll', 'FNA.dll']
    tools += [p.name for p in managed.glob('Mono*.dll')]
    recipe = dict(schema=1, source_id=hashlib.sha256(canonical.encode()).hexdigest(),
                  inputs=original_pins, tools={n: sha(managed / n) for n in sorted(tools)})
    destination.write_text(json.dumps(recipe, indent=2, sort_keys=True) + '\n')
    return recipe
