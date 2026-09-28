#!/usr/bin/env python3
"""Fetch hash-pinned public dependencies. No game ZIP, FMOD or private capsule."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from compile_owned_game import ROOT, SOURCE

PUBLIC = SOURCE / 'public-build'


def digest(path, algorithm='sha256'):
    with path.open('rb') as stream: return hashlib.file_digest(stream, algorithm).hexdigest()


def prepare(work, cache):
    if ROOT / '.build' not in work.parents or work.resolve() != work.absolute() or work.exists(): raise ValueError('Choose a fresh unaliased .build input directory')
    work.mkdir(parents=True); cache.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'release/owned-game-dependencies.json').read_text())['dependencies']
    arch = 'arm64' if platform.machine() == 'arm64' else 'x64'
    names = [n for n in lock if not n.startswith('sdk') or n.endswith('osx-' + arch)]
    def fetch(name):
        row = lock[name]; algorithm = 'sha512' if 'sha512' in row else 'sha256'
        target = cache / (name + '.archive')
        prior = cache / (name + '.tgz')
        if not target.exists() and prior.exists() and digest(prior, algorithm) == row[algorithm]: target = prior
        if not target.exists():
            temporary = target.with_suffix('.download')
            request = urllib.request.Request(row['url'], headers={'User-Agent': 'Cabrillo public dependency builder'})
            with urllib.request.urlopen(request, timeout=120) as response, temporary.open('xb') as output:
                shutil.copyfileobj(response, output)
            if digest(temporary, algorithm) != row[algorithm]: raise ValueError('Download checksum differs: ' + name)
            temporary.replace(target)
        if digest(target, algorithm) != row[algorithm]: raise ValueError('Cached dependency differs: ' + name)
        destination = work / name; destination.mkdir()
        if row.get('kind') == 'zip':
            with zipfile.ZipFile(target) as archive:
                for item in archive.infolist():
                    parts = Path(item.filename).parts
                    if Path(item.filename).is_absolute() or '..' in parts or '\\' in item.filename:
                        raise ValueError('Unsafe dependency ZIP path')
                archive.extractall(destination)
        else:
            with tarfile.open(target) as archive:
                for item in archive.getmembers():
                    # GitHub and Lua archives have one enclosing source directory;
                    # SDKs put dotnet at the archive root.
                    if not name.startswith('sdk'):
                        parts = item.name.split('/', 1)
                        if len(parts) != 2 or not parts[1]: continue
                        item.name = parts[1]
                    archive.extract(item, destination, filter='data')
        print('Verified public input ' + name, flush=True)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch, name) for name in names]
        for result in as_completed(futures): result.result()
    def patch(folder, file):
        # Check first; git apply is used only as a local patch tool.
        flags = ['--unidiff-zero'] if file.name in {'fna-imports.patch', 'fna-dispatcher.patch'} else []
        # Use the repository root plus an explicit destination: git-format patches
        # run from an ignored subdirectory can otherwise report success while skipping files.
        affected = [line[6:] for line in file.read_text().splitlines() if line.startswith('+++ b/')]
        if not affected: raise ValueError('Patch has no destination files: ' + str(file))
        before = {name: digest(folder / name) if (folder / name).exists() else None for name in affected}
        command = ['git', 'apply', *flags, '--directory=' + str(folder.relative_to(ROOT))]
        subprocess.run([*command, '--check', str(file)], cwd=ROOT, check=True)
        subprocess.run([*command, str(file)], cwd=ROOT, check=True)
        for name in affected:
            if not (folder / name).is_file() or digest(folder / name) == before[name]:
                raise ValueError('Patch did not change its intended file: ' + name)
    for name in ['Everest', 'MonoMod', 'runtime']: patch(work / name, PUBLIC / (name + '.patch'))
    provenance = json.loads((PUBLIC / 'patch-provenance.json').read_text())
    for name, rows in provenance['source_patches'].items():
        for path, row in rows.items():
            if digest(work / name / path) != row['patched_sha256']: raise ValueError('Patched public source differs: ' + path)
    for source, dest in [('MonoMod', 'Everest/external/MonoMod'), ('iced', 'Everest/external/MonoMod/external/iced'),
                         ('NLua', 'Everest/external/NLua'), ('Everest-libs', 'Everest/lib-ext'),
                         ('MojoShader', 'FNA3D/MojoShader'), ('Vulkan-Headers', 'FNA3D/Vulkan-Headers')]:
        target = work / dest
        if target.exists(): target.rmdir()  # Public archives omit submodule contents.
        shutil.move(work / source, target)
    for name, patches in {
        'SDL2': ['0001-tvos-use-pregenerated-metal-shaders.patch', '0003-ios-use-pregenerated-metal-shaders.patch', '0002-ios-modern-scene-host.patch'],
        'FNA3D': ['0001-add-sysrenderer-header-to-xcode-project.patch'],
        'FAudio': ['0001-align-static-distance-curves-for-ld64.patch']}.items():
        for file in patches: patch(work / name, PUBLIC / 'native' / name / file)
    for name in ['fna3d-callback.patch', 'fna3d-backbuffer.patch']: patch(work / 'FNA3D', SOURCE / 'native' / name)
    patch(work / 'lua', PUBLIC / 'lua.patch')
    patch(work / 'FNA', PUBLIC / 'fna-touch.patch')
    bindings = work / 'bindings'; bindings.mkdir()
    for path, name in [('SDL2-CS/src/SDL2.cs', 'SDL2.cs'), ('FAudio/csharp/FAudio.cs', 'FAudio.cs'),
                       ('Theorafile/csharp/Theorafile.cs', 'Theorafile.cs'), ('FNA/src/Graphics/FNA3D.cs', 'FNA3D.cs'),
                       ('FNA/src/FrameworkDispatcher.cs', 'FrameworkDispatcher.cs')]:
        shutil.copyfile(work / path, bindings / name)
    for name in ['fna-imports.patch', 'fna-dispatcher.patch']: patch(bindings, PUBLIC / name)
    game = work / 'FNA/src/Game.cs'; text = game.read_text()
    assert text.count('public class Game : IDisposable') == 1
    game.write_text(text.replace('public class Game : IDisposable', 'public partial class Game : IDisposable'))
    spec = importlib.util.spec_from_file_location('owned_loading', SOURCE / 'patch_loading.py')
    loading = importlib.util.module_from_spec(spec); spec.loader.exec_module(loading)
    loading.apply(work / 'Everest')
    receipt = dict(schema=1, status='PASS_PUBLIC_SOURCE_INPUTS', dependencies={n: lock[n] for n in names},
                   game_files_used=False, private_capsule_used=False, sdk_arch=arch,
                   files={str(f.relative_to(work)): digest(f) for f in sorted(work.rglob('*')) if f.is_file()})
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True); parser.add_argument('--cache', required=True)
    args = parser.parse_args()
    prepare(Path(args.work).resolve(), Path(args.cache).resolve())
