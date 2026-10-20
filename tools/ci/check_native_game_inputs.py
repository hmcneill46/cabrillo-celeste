#!/usr/bin/env python3
"""Exercise the launcher availability hint with legacy and selected game inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', default='.build/ci/native-game-inputs')
    args = parser.parse_args()
    work = (ROOT / args.work).absolute()
    if work.resolve() != work or ROOT / '.build' not in work.parents or work.exists():
        raise ValueError('Use a fresh directory under .build')
    work.mkdir(parents=True)
    lane = ROOT / 'experiments/ios-jit/launcher-game-inputs'
    sources = [lane / 'src/CJGameInputState.m', lane / 'tests/GameInputStateTests.m']
    env = dict(os.environ)
    env.setdefault('DEVELOPER_DIR', '/Applications/Xcode-26.6.app/Contents/Developer')
    subprocess.run(['xcrun', 'clang', '-fobjc-arc', '-Wall', '-Wextra', '-Werror',
                    '-I' + str(lane / 'src'), *map(str, sources), '-framework', 'Foundation',
                    '-o', str(work / 'check')], env=env, check=True)
    result = subprocess.check_output([str(work / 'check'), str(work / 'Documents')], text=True)
    assert 'PASS_NATIVE_GAME_INPUT_STATE checks=14' in result
    (work / 'receipt.json').write_text(json.dumps(dict(status='PASS_NATIVE_GAME_INPUT_STATE', checks=14,
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sources + [lane / 'src/CJGameInputState.h', Path(__file__)]},
        physical_device_tested=False), indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
