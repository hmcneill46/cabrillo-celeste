#!/usr/bin/env python3
"""Materialize pinned Everest sources without writing to accepted canaries."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/everest-source'
PINS = {
    'Everest': ('https://github.com/EverestAPI/Everest.git', '4bbde91b8dbaaddef2ceec75ca0cd6d59b3b8d00'),
    'MonoMod': ('https://github.com/MonoMod/MonoMod.git', 'dfc30a1506d37fb88a2c2be004f525205f46a24c'),
    'iced': ('https://github.com/icedland/iced.git', 'c50f29b7bc305696895c075f3fc7719751426b12'),
    'NLua': ('https://github.com/EverestAPI/NLua.git', 'b3524288712743fb2394dcf615d14d0dac3276e2'),
    'Everest-libs': ('https://github.com/EverestAPI/Everest-libs.git', '591f7c12fcb4e8fda9ef5ef1b331b5ed40d3fb1f'),
}


def run(args, cwd=None):
    result = subprocess.run(list(map(str, args)), cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with (STAGE / 'source-prepare.log').open('a') as stream:
        stream.write(repr(list(map(str, args))) + '\n' + result.stdout)
    if result.returncode:
        raise RuntimeError(result.stdout[-6000:])
    return result.stdout.strip()


def checkout(name, destination, local=None):
    url, commit = PINS[name]
    if not (destination / '.git').exists():
        if local:
            run(['git', 'clone', '--no-hardlinks', '--no-checkout', local, destination])
        else:
            destination.mkdir(parents=True, exist_ok=True)
            run(['git', 'init', destination])
            run(['git', 'remote', 'add', 'origin', url], destination)
            run(['git', 'fetch', '--depth=1', 'origin', commit], destination)
        run(['git', 'checkout', '--detach', commit], destination)
    assert run(['git', 'rev-parse', 'HEAD'], destination) == commit, destination
    print(name + ' source ready: ' + commit, flush=True)


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    everest = STAGE / 'Everest'
    checkout('Everest', everest, ROOT / '.build/ios-jit/audit/references/Everest')
    mono = everest / 'external/MonoMod'
    checkout('MonoMod', mono, ROOT / '.build/ios-jit/hook-runtime/MonoMod')
    checkout('iced', mono / 'external/iced', ROOT / '.build/ios-jit/hook-runtime/MonoMod/external/iced')
    checkout('NLua', everest / 'external/NLua')
    checkout('Everest-libs', everest / 'lib-ext')

    # Copy only hash-verified hosting corrections, never accepted build outputs.
    accepted = ROOT / '.build/ios-jit/hook-runtime'
    receipt = json.loads((accepted / 'monomod-patch-receipt.json').read_text())
    for name, item in receipt['files'].items():
        original = accepted / 'MonoMod' / name
        assert hashlib.sha256(original.read_bytes()).hexdigest() == item['patched_sha256'], name
        target = mono / name
        if target.exists():
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            assert digest in {item.get('original_sha256'), item['patched_sha256']}, ('Unrecognized staging edit', name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
    (STAGE / 'source-receipt.json').write_text(json.dumps(dict(schema=1, pins=PINS, accepted_monomod_hosting_files=receipt['files'], source_only=True), indent=2) + '\n')
    print('PINNED_EVEREST_SOURCES_AND_ACCEPTED_HOOK_BACKEND_READY', flush=True)


if __name__ == '__main__':
    main()
