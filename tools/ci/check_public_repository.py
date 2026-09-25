#!/usr/bin/env python3
"""Audit a public checkout without opening Cabrillo's private dependency capsule."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_SUFFIXES = {'.dll', '.exe', '.ipa', '.a', '.dylib', '.p12', '.p8',
                      '.mobileprovision', '.bank', '.xnb', '.zip'}


def audit(root):
    names = sorted(set(subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
        cwd=root).decode().split('\0')) - {''})
    inventory_name = 'docs/MIGRATION_FILE_INVENTORY.json'
    inventory = json.loads((root / inventory_name).read_text())['files']
    if set(names) != set(inventory):
        raise ValueError('Public file inventory differs: ' + repr(sorted(set(names) ^ set(inventory))))
    python_files = json_files = total = 0
    for name in names:
        path, row = root / name, inventory[name]
        if Path(name).parts[0] in {'.private', '.build', 'artifacts', 'dist'}:
            raise ValueError('Private/generated directory in public checkout: ' + name)
        if path.is_symlink() or path.resolve() != path.absolute() or not row.get('reason'):
            raise ValueError('Unjustified path or symlink: ' + name)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError('Binary, game or signing input in public checkout: ' + name)
        data = path.read_bytes()
        keys = [b'-----BEGIN ' + kind + b'PRIVATE KEY-----'
                for kind in [b'', b'RSA ', b'EC ', b'OPENSSH ']]
        if data.startswith((b'MZ', b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe')) or any(k in data for k in keys):
            raise ValueError('Binary or private key in public checkout: ' + name)
        if name == inventory_name:
            if not row.get('self_describing'):
                raise ValueError('Inventory must describe its own unhashed entry')
        elif hashlib.sha256(data).hexdigest() != row.get('sha256') or len(data) != row.get('bytes'):
            raise ValueError('Public inventory hash/size mismatch: ' + name)
        if path.suffix == '.py':
            ast.parse(data, filename=name)
            python_files += 1
        if path.suffix == '.json':
            json.loads(data)
            json_files += 1
        total += len(data)
    for name in ['.private/example.dll', '.build/example.o', 'artifacts/example.ipa', 'dist/example.ipa']:
        if subprocess.run(['git', 'check-ignore', '-q', '--no-index', name], cwd=root).returncode:
            raise ValueError('Private/generated path is not ignored: ' + name)
    return dict(status='PASS_PUBLIC_SOURCE_CHECKOUT', public_files=len(names), public_bytes=total,
                parsed_python_files=python_files, parsed_json_files=json_files,
                private_dependencies_used=False,
                scope='Source inventory, exclusion boundaries and syntax; not an IPA or device test.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = audit(ROOT)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
