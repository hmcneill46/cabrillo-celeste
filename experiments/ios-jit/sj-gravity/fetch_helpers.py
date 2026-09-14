#!/usr/bin/env python3
"""Fetch the original locked SJ helper ZIPs without changing their contents."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/sj-gravity-inputs'
sha = lambda data: hashlib.sha256(data).hexdigest()

def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    pins = json.loads((SOURCE / 'helper-pins.json').read_text())
    receipt = {'schema': 1, 'pins_sha256': sha((SOURCE / 'helper-pins.json').read_bytes()), 'files': {}}
    for row in pins['helpers']:
        name = row['name'] + '-v' + row['resolvedVersion'] + '.zip'
        path = STAGE / name
        if not path.exists():
            temp = path.with_suffix('.download')
            subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error', '--max-time', '90',
                            row['publicUrl'], '--output', str(temp)], check=True)
            assert temp.stat().st_size == row['zipBytes'] and sha(temp.read_bytes()) == row['zipSha256'], name
            temp.replace(path)
        assert path.stat().st_size == row['zipBytes'] and sha(path.read_bytes()) == row['zipSha256'], name
        with zipfile.ZipFile(path) as archive:
            actual_dll_paths = {}
            for dll in row['distributedDlls']:
                matches = [n for n in archive.namelist() if Path(n).name == dll['path']]
                assert len(matches) == 1, (name, dll['path'], matches)
                data = archive.read(matches[0])
                assert len(data) == dll['bytes'] and sha(data) == dll['sha256'], dll['path']
                (STAGE / dll['path']).write_bytes(data)
                actual_dll_paths[dll['path']] = matches[0]
        receipt['files'][name] = dict(row, actual_dll_paths=actual_dll_paths)
        print('VERIFIED', name, row['zipBytes'], flush=True)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

if __name__ == '__main__':
    main()
