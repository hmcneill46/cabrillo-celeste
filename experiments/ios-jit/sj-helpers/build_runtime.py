#!/usr/bin/env python3
"""Recompile one Mono metadata object into separate host/iOS archive copies."""
import collections
import difflib
import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
RUNTIME = ROOT / '.build/ios-jit/managed-runtime'
STAGE = ROOT / '.build/ios-jit/sj-helper-runtime'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def members(path):
    data = path.read_bytes()
    assert data.startswith(b'!<arch>\n')
    pos, result = 8, []
    while pos < len(data):
        header = data[pos:pos + 60]
        assert header[58:60] == b'`\n'
        size = int(header[48:58]); name = header[:16].decode().strip()
        payload = data[pos + 60:pos + 60 + size]
        if name.startswith('#1/'):
            length = int(name[3:]); name = payload[:length].rstrip(b'\0').decode(); payload = payload[length:]
        else:
            name = name.rstrip('/')
        if not name.startswith('__.SYMDEF'):
            result.append((name, hashlib.sha256(payload).hexdigest()))
        pos += 60 + size + size % 2
    assert pos == len(data)
    return result

def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    original = RUNTIME / 'runtime-v8.0.28/src/mono/mono/metadata/class.c'
    assert sha(original) == 'd9fcfdb3420cfba298bbe954cc69199da0f270fd9890f3ae1210d8ae7aec4bfd'
    before = original.read_text()
    replacements = [
        ('MonoImage *member_klass_image = m_class_get_image (member_klass);\n\t/* Partition I 8.5.3.2 */',
         'MonoImage *member_klass_image = m_class_get_image (member_klass);\n\t/* CJIT: protected members also belong to the explicitly granted assembly. */\n\tif (ignores_access_checks_to (access_klass_assembly, member_klass_image->assembly))\n\t\treturn TRUE;\n\t/* Partition I 8.5.3.2 */'),
    ]
    after = before
    for old, new in replacements:
        assert after.count(old) == 1
        after = after.replace(old, new)
    source = STAGE / 'class.c'; source.write_text(after)
    patch = STAGE / 'mono8-visibility.patch'
    patch.write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/src/mono/mono/metadata/class.c', tofile='b/src/mono/mono/metadata/class.c')))
    receipt = dict(schema=1, runtime='Mono 8.0.28', original_class_sha256=sha(original), patched_class_sha256=sha(source), patch_sha256=sha(patch), builder_sha256=sha(Path(__file__)), targets={})
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    for name, build in [('host', 'mono-build-host-coop'), ('ios', 'mono-build-ios')]:
        target = STAGE / name; target.mkdir(exist_ok=True)
        db = RUNTIME / build / 'compile_commands.json'
        command = next(row['command'] for row in json.loads(db.read_text()) if row['file'] == str(original))
        args = shlex.split(command)
        args[args.index('-o') + 1] = str(target / 'class.c.o')
        args[args.index(str(original))] = str(source)
        args += ['-iquote', str(original.parent), '-MMD', '-MF', str(target / 'class.d')]
        result = subprocess.run(args, cwd=target, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (target / 'compile.log').write_text(result.stdout)
        if result.returncode: raise RuntimeError(result.stdout)
        original_archive = RUNTIME / build / 'mono/mini/libmonosgen-2.0.a'
        output = target / 'libmonosgen-2.0.a'
        old_members = members(original_archive)
        assert sum(n == 'class.c.o' for n, _ in old_members) == 1
        shutil.copy2(original_archive, output)
        subprocess.run(['xcrun', 'ar', '-r', str(output), str(target / 'class.c.o')], env=env, check=True)
        new_members = members(output)
        assert collections.Counter((n,h) for n,h in old_members if n != 'class.c.o') == collections.Counter((n,h) for n,h in new_members if n != 'class.c.o')
        assert sum(n == 'class.c.o' for n, _ in new_members) == 1
        deps = shlex.split((target / 'class.d').read_text().replace('\\\n', ' ').split(':', 1)[1])
        receipt['targets'][name] = dict(original_archive=str(original_archive.relative_to(ROOT)), original_sha256=sha(original_archive), archive=str(output.relative_to(ROOT)), sha256=sha(output), replaced_member='class.c.o', unchanged_members=len(old_members)-1, object_sha256=sha(target/'class.c.o'), compile_database_sha256=sha(db), command=args, source_sha256={str(Path(p)):sha(Path(p)) for p in deps})
        print('PASS_ISOLATED_MONO_VISIBILITY', name, 'unchanged members', len(old_members)-1, flush=True)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

if __name__ == '__main__':
    main()
