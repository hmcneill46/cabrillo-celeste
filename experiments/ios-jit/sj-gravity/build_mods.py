#!/usr/bin/env python3
"""Author a small original room and ordinary Everest code/map ZIPs."""
import hashlib
import io
import json
import os
import struct
import subprocess
import shutil
import zipfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/sj-gravity-mods'
MANAGED = ROOT / '.build/ios-jit/sj-gravity-managed'
SDK = ROOT / '.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'


def map_bytes():
    # The documented Celeste binary-map tree format; all room geometry is
    # authored here. Tile style and audio refer to the owner's installed assets.
    def element(name, attrs=None, children=None):
        return name, attrs or {}, children or []
    width, height = 80, 23
    tiles = '\n'.join('1' * width if y >= 20 or y < 2 else '11' + '0' * (width - 4) + '11' for y in range(height))
    room = element('level', dict(name='lvl_test', x=0, y=0, width=640, height=184,
                               music='event:/music/lvl1/main', windPattern='None', c=1), [
        element('solids', {'innerText': tiles}), element('bg', {'innerText': ''}),
        element('fgtiles', {'innerText': ''}), element('bgtiles', {'innerText': ''}),
        element('objtiles', {'innerText': ''}), element('bgdecals'), element('fgdecals'),
        element('triggers', children=[
            element('luaCutscenes/luaCutsceneTrigger', dict(id=10, x=24, y=112, width=80, height=48, filename='CJITGravityProbe:/Assets/CJITGravityProbe/retained_cutscene', onlyOnce=True, oncePerSession=False, unskippable=False, arguments='')),
            element('GravityHelper/GravityTrigger', dict(id=11, x=144, y=16, width=336, height=144, gravityType=1, exitGravityType=0, momentumMultiplier=1.0, defaultToController=False, affectsPlayer=True, affectsHoldableActors=False, affectsOtherActors=False, pluginVersion='1', modVersion='1.2.28'))]),
        element('entities', children=[element('player', dict(id=1, x=40, y=160)),
                                      element('CJITCanary/status', dict(id=2, x=16, y=16)),
                                      element('CJITGravityProbe/status', dict(id=3, x=16, y=16)),
                                      element('MaxHelpingHand/UpsideDownJumpThru', dict(id=4, x=192, y=48, width=240, texture='wood', animationDelay=0.0, pushPlayer=False, squishPlayer=False, attached=False))])])
    tree = element('Map', children=[element('levels', children=[room]), element('Filler'),
                    element('Style', {'color': '162c48'}, [element('Backgrounds'), element('Foregrounds')])])
    names = []
    def collect(node):
        name, attrs, children = node
        for name in [name, *attrs]:
            if name not in names: names.append(name)
        for child in children: collect(child)
    collect(tree)
    output = io.BytesIO()
    def string(value):
        data = value.encode('utf-8'); length = len(data)
        while length >= 128:
            output.write(bytes([(length & 127) | 128])); length >>= 7
        output.write(bytes([length])); output.write(data)
    def pack(fmt, *values): output.write(struct.pack('<' + fmt, *values))
    string('CELESTE MAP'); string('CJITGravityProbe/RuntimeRoom'); pack('h', len(names))
    for name in names: string(name)
    def write(node):
        name, attrs, children = node
        pack('hB', names.index(name), len(attrs))
        for key, value in attrs.items():
            pack('h', names.index(key))
            if isinstance(value, bool): pack('B?', 0, value)
            elif isinstance(value, int): pack('Bi', 3, value)
            elif isinstance(value, float): pack('Bf', 4, value)
            else: pack('B', 6); string(value)
        pack('h', len(children))
        for child in children: write(child)
    write(tree)
    return output.getvalue()


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    refs = sorted((SDK / 'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    libs = ['Celeste.dll', 'FNA.dll', 'MMHOOK_Celeste.dll', 'MonoMod.Utils.dll', 'MonoMod.RuntimeDetour.dll', 'Mono.Cecil.dll']
    output = STAGE / 'CJITGravityProbe.dll'
    sources = sorted((SOURCE / 'mods').glob('*.cs'))
    rsp = STAGE / 'mod.rsp'
    args = ['-nologo', '-nostdlib+', '-optimize+', '-deterministic+', '-target:library', '-out:"' + str(output) + '"']
    args += ['-r:"' + str(p) + '"' for p in refs + [MANAGED / n for n in libs]]
    args += ['-r:"' + str(ROOT / '.build/ios-jit/sj-gravity-inputs' / n) + '"' for n in ['GravityHelper.dll', 'MaxHelpingHand.dll']]
    args += ['"' + str(p) + '"' for p in sources]
    rsp.write_text('\n'.join(args) + '\n')
    env = dict(os.environ, DOTNET_ROOT=str(SDK), DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_MULTILEVEL_LOOKUP='0')
    command = [str(SDK / 'dotnet'), 'exec', str(SDK / 'sdk/8.0.422/Roslyn/bincore/csc.dll'), '@' + str(rsp)]
    result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (STAGE / 'build.log').write_text(result.stdout)
    if result.returncode: raise RuntimeError(result.stdout)
    def zip_mod(name, files):
        with zipfile.ZipFile(STAGE / (name + '-v1.0.0.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, data in sorted(files.items()):
                info = zipfile.ZipInfo(path, (2026, 9, 11, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data.encode() if isinstance(data, str) else data)
    manifest = "- Name: CJITGravityProbe\n  Version: 1.0.0\n  DLL: CJITGravityProbe.dll\n  Dependencies:\n    - Name: Everest\n      Version: 1.6458.0\n    - Name: CJITCodeCanary\n      Version: 1.0.0\n    - Name: LuaCutscenes\n      Version: 0.2.13\n    - Name: GravityHelper\n      Version: 1.2.28\n    - Name: MaxHelpingHand\n      Version: 1.40.9\n"
    zip_mod('CJITGravityProbe', {'everest.yaml': manifest, 'CJITGravityProbe.dll': output.read_bytes(),
        'Maps/CJITGravityProbe/RuntimeRoom.bin': map_bytes(),
        'Maps/CJITGravityProbe/RuntimeRoom.meta.yaml': 'IntroType: Respawn\nDreaming: false\nColorGrade: none\nDarknessAlpha: 0\nBloomBase: 0\nModes:\n  - Inventory: Default\n    StartLevel: test\n',
        'Dialog/English.txt': 'CJITSJHELPERS= Celeste JIT Helper Tests\nCJITSJHELPERS_RUNTIMEROOM= Lua and Gravity\n',
        'Assets/CJITGravityProbe/retained_cutscene.lua': (SOURCE/'mods/retained_cutscene.lua').read_bytes()})
    for name in ['CJITCodeCanary-v1.0.0.zip', 'CJITTestMap-v1.0.0.zip']:
        shutil.copy2(ROOT/'artifacts/ios-jit/everest-canary-20260911-13'/name, STAGE/name)
    shutil.copy2(ROOT/'artifacts/ios-jit/sj-code-budget-20260912-16/CJITSJHelpers-v1.0.0.zip', STAGE/'CJITSJHelpers-v1.0.0.zip')
    helpers = json.loads((ROOT/'.build/ios-jit/sj-gravity-inputs/receipt.json').read_text())
    for name in helpers['files']:
        shutil.copy2(ROOT/'.build/ios-jit/sj-gravity-inputs'/name, STAGE/name)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    receipt = dict(schema=1, status='PASS_SMALL_EVEREST_MOD_ZIPS_BUILT',
                   files={p.name: dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(STAGE.glob('*.zip'))},
                   code_dll_sha256=sha(output), source_sha256={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), SOURCE/'mods/retained_cutscene.lua', SOURCE/'helper-pins.json', SOURCE/'fetch_helpers.py', *sources]},
                   reference_sha256={n: sha(MANAGED / n) for n in libs}, command=command,
                   proprietary_content_included=False, original_helpers=helpers, device_tested=False)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'])


if __name__ == '__main__': main()
