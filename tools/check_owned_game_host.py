#!/usr/bin/env python3
"""Private integration check of game-free bootstrap, owned import and real gameplay.

Uses explicit pinned historical test fixtures; this is not the public builder.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from compile_owned_game import SOURCE, ROOT, compile_bootstrap, write_recipe, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', required=True)
    p.add_argument('--game-zip', required=True)
    p.add_argument('--managed', help='Fresh public managed receipt')
    a = p.parse_args()
    work = ROOT / a.work
    assert work.resolve() == work.absolute() and ROOT / '.build' in work.parents and not work.exists()
    work.mkdir(parents=True)
    baseline = ROOT / '.build/everest-game37-c'
    prior = json.loads((baseline / 'receipt.json').read_text())
    assert prior['status'] == 'PASS_BACKUP_RESTORED_REAL_GAME_SAVE_QUIT'
    for name, digest in prior['host_managed_sha256'].items():
        assert sha(baseline / 'Managed' / name) == digest, name
    native_runtime = json.loads((ROOT / '.build/visibility-runtime36-a/receipt.json').read_text())
    archive = ROOT / native_runtime['host_fixed']['path']
    assert sha(archive) == native_runtime['host_fixed']['sha256']
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    commands = []
    def run(command, label, timeout=600):
        command = list(map(str, command)); commands.append(command)
        with (work / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode: raise RuntimeError(label + ' failed: ' + str(work / (label + '.log')))
        print(label + ' PASS', flush=True)
    managed = work / 'Managed'
    run(['cp', '-cR', baseline / 'Managed', managed], 'copy-runtime')
    for name in ['Celeste.dll', 'Celeste.Content.dll', 'MMHOOK_Celeste.dll']:
        (managed / name).unlink()
    shutil.rmtree(managed / 'orig')
    public = None
    if a.managed:
        public_path = (ROOT / a.managed).resolve()
        public = json.loads(public_path.read_text())
        assert public['status'] == 'PASS_PUBLIC_GAME_FREE_MANAGED_BUILD'
        resources = public_path.parent / 'resources'
        for name, digest in public['resources'].items(): assert sha(resources / name) == digest, name
        for path in (resources / 'Managed').glob('*.dll'): shutil.copyfile(path, managed / path.name)
        inputs = Path(public['input_receipt']).parent
        pack = inputs / 'mono-osx-x64/runtimes/osx-x64'
        for path in (pack / 'lib/net8.0').glob('*.dll'): shutil.copyfile(path, managed / path.name)
        sdk = inputs / 'sdk8.0-osx-x64'
        corelib = pack / 'native/System.Private.CoreLib.dll'
        run([sdk / 'dotnet', public_path.parent / 'tools/PatchReflectionFlags.dll', corelib, sha(corelib),
             managed / 'System.Private.CoreLib.dll', work / 'host-reflection.json'], 'host-reflection')
        shutil.copyfile(resources / 'OwnedGameRecipe.json', work / 'OwnedGameRecipe.json')
    else:
        dependencies = ROOT / '.build/everest-managed37-b/tool-artifacts/bin/EverestPrepare/release'
        for path in dependencies.glob('*.dll'):
            if path.name not in {'EverestPrepare.dll'}:
                if not (managed / path.name).exists(): shutil.copyfile(path, managed / path.name)
        sdk = ROOT / '.private/loading-inputs/sdk8'
        compile_bootstrap(sdk, managed, work, run)
        original_pins = {}
        with zipfile.ZipFile(a.game_zip) as z:
            for name in ['Celeste.exe', 'Celeste.Content.dll', 'FNA.dll']:
                data = z.read(name)
                original_pins[name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        write_recipe(original_pins, managed, work / 'OwnedGameRecipe.json')
    assert not any((managed / name).exists() for name in ['Celeste.dll', 'Celeste.exe', 'Celeste.Content.dll', 'MMHOOK_Celeste.dll', 'orig'])
    run(['cp', '-cR', baseline / 'GameLibrary', work / 'GameLibrary'], 'copy-content')
    shutil.copyfile(baseline / 'GameContentManifest.json', work / 'GameContentManifest.json')
    shutil.copyfile(baseline / 'SessionIntegrationTests.dll', work / 'SessionIntegrationTests.dll')
    original = ROOT / '.build/loading-host30-c'
    lock = json.loads((ROOT / 'experiments/ios-jit/launcher-everest6580/Dependencies.json').read_text())
    includes = [SOURCE / 'src', ROOT / 'experiments/ios-jit/managed-canary/src'] + [ROOT / n for n in lock['include_directories']]
    objects = []
    for source in [SOURCE / 'tests/host_motion.m', SOURCE / 'src/CJGraphicsManaged.m', SOURCE / 'src/CJContentImport.m']:
        obj = work / (source.stem + '.o'); objects.append(obj)
        run(['xcrun', 'clang', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-DCJ_HOOK_HOST_TEST=1', '-DCJ_GRAPHICS_HOST_TEST=1',
             '-fobjc-arc', '-Wno-deprecated-declarations', *['-I' + str(x) for x in includes], '-c', source, '-o', obj], 'compile-' + source.stem)
    replaced = {'host_graphics.o', 'CJGraphicsManaged.o', 'CJContentImport.o'}
    objects += [x for x in sorted(original.glob('*.o')) if x.name not in replaced]
    native = ROOT / '.private/loading-inputs/host/native'
    run(['xcrun', 'clang', *objects, archive, *sorted(native.glob('libmono-component-*.a')), '-lc++', '-liconv', '-lz',
         '-framework', 'CoreFoundation', '-framework', 'Foundation', '-framework', 'Security', '-framework', 'AppKit',
         '-Wl,-rpath,' + str(original), '-o', work / 'game-test'], 'link-host')
    env.update(CJIT_GAME_CONTENT_ROOT=str(work / 'pending/Content'), CJIT_CONTENT_LIBRARY_ROOT=str(work / 'GameLibrary/v1'),
        CJIT_CONTENT_MANIFEST=str(work / 'GameContentManifest.json'), CJIT_GAME_CODE_ROOT=str(work / 'GameCode/v1'),
        CJIT_GAME_CODE_RECIPE=str(work / 'OwnedGameRecipe.json'), CJIT_TEST_TOUCH='1', CJIT_VERIFY_SJ='0', CJIT_HOST_NORMAL='1',
        CJIT_SESSION_TEST=str(work / 'SessionIntegrationTests.dll'), CJIT_EXPECT_HAIR_FIXED='1',
        CJIT_REFLECTION_SIGNATURES=str(ROOT / '.private/loading-host-inputs/ReflectionSignatures.dll'))
    for stage in ['cold', 'warm']:
        scenario = work / stage; scenario.mkdir()
        profile = scenario / 'Profile'
        run(['cp', '-cR', baseline / 'Profile', profile], 'copy-profile-' + stage)
        run([baseline / 'roundtrip', scenario], 'backup-transfer-' + stage)
        if public:
            shutil.copyfile(resources / 'CJITCodeCanary-v1.0.0.zip', profile / 'Mods/CJITCodeCanary-v1.0.0.zip')
        env.update(CJIT_CONTENT_ARCHIVE=a.game_zip if stage == 'cold' else '', CJIT_GAME_SAVE_ROOT=str(profile))
        command = [str(x).replace(str(baseline / 'Managed'), str(managed)) for x in prior['commands'][-1]]
        command[0] = str(work / 'game-test'); command[3] = str(managed / 'Cabrillo.Bootstrap.dll')
        run(command, stage)
        output = (work / (stage + '.log')).read_text()
        for marker in ['owned_game_adapter_bound', 'PASS_HOST_COOPERATIVE_BOOT', 'PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME',
                       'PASS_REAL_GAME_HAIR_MOTION_RESTORED', 'PASS_DESKTOP_SAVE_TRANSFER_REAL_EVEREST',
                       'game_code_ready reused=' + ('False' if stage == 'cold' else 'True')]:
            assert marker in output, marker
    (work / 'receipt.json').write_text(json.dumps(dict(status='PASS_OWNED_GAME_COLD_WARM_GAMEPLAY',
        public_managed_receipt_sha256=sha(public_path) if public else None,
        commands=commands, native_runtime_sha256=sha(archive), game_free_bundle={x.name: sha(x) for x in managed.glob('*.dll')},
        logs={n: sha(work / (n + '.log')) for n in ['cold', 'warm']}, physical_device_tested=False), indent=2) + '\n')


if __name__ == '__main__': main()
