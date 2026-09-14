#!/usr/bin/env python3
"""Recompile Mono code allocation into copies of build 15 compatibility archives."""
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
STAGE = ROOT / '.build/ios-jit/sj-budget-runtime'
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
    original = RUNTIME / 'runtime-v8.0.28/src/mono/mono/utils/mono-codeman.c'
    assert sha(original) == 'f572009ff0384dc2d980bfe2aa1559e40719f9a4e453e1f4ae165edef967c155'
    before = original.read_text()
    replacements = [
        ('#define MIN_PAGES 16', '/* CJIT: keep the usual 64 KiB floor independent of OS page size.\n * Each generated assembly owns a code manager; 16 x 16 KiB wastes the\n * fixed iOS code arena. Page/granule alignment and ARM64 thunk room remain. */\n#define MIN_CHUNK_BYTES (64 * 1024)'),
        ('MAX (pagesize * MIN_PAGES, valloc_granule)',
         'MAX (MAX (MIN_CHUNK_BYTES, pagesize), valloc_granule)'),
    ]
    after = before
    for old, new in replacements:
        assert after.count(old) == 1
        after = after.replace(old, new)
    source = STAGE / 'mono-codeman.c'; source.write_text(after)
    patch = STAGE / 'mono8-code-chunks.patch'
    patch.write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/src/mono/mono/utils/mono-codeman.c', tofile='b/src/mono/mono/utils/mono-codeman.c')))
    receipt = dict(schema=1, runtime='Mono 8.0.28', original_codeman_sha256=sha(original), patched_codeman_sha256=sha(source), patch_sha256=sha(patch), builder_sha256=sha(Path(__file__)), targets={})
    inherited = ROOT / '.build/ios-jit/sj-helper-runtime'
    inherited_receipt = json.loads((inherited / 'receipt.json').read_text())
    receipt['inherited_visibility_receipt_sha256'] = sha(inherited / 'receipt.json')
    receipt['ordinary_chunk_minimum_bytes'] = 65536
    receipt['host_model'] = dict(page_bytes=16384, valloc_granule_bytes=16384, bind_room_divisor=4, arm64_execution=False)
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    for name, build in [('host', 'mono-build-host-coop'), ('ios', 'mono-build-ios')]:
        target = STAGE / name; target.mkdir(exist_ok=True)
        db = RUNTIME / build / 'compile_commands.json'
        command = next(row['command'] for row in json.loads(db.read_text()) if row['file'] == str(original))
        args = shlex.split(command)
        args[args.index('-o') + 1] = str(target / 'mono-codeman.c.o')
        args[args.index(str(original))] = str(source)
        args += ['-iquote', str(original.parent), '-MMD', '-MF', str(target / 'mono-codeman.d')]
        # Host-only code sizing models iOS pages and ARM64 thunk reservation.
        # These flags are never used for the shipped iOS object.
        if name == 'host':
            args += ['-Dmono_pagesize=cjit_test_pagesize', '-Dmono_valloc_granule=cjit_test_valloc_granule', '-DBIND_ROOM=4']
        result = subprocess.run(args, cwd=target, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (target / 'compile.log').write_text(result.stdout)
        if result.returncode: raise RuntimeError(result.stdout)
        original_archive = inherited / name / 'libmonosgen-2.0.a'
        assert sha(original_archive) == inherited_receipt['targets'][name]['sha256']
        output = target / 'libmonosgen-2.0.a'
        old_members = members(original_archive)
        assert sum(n == 'mono-codeman.c.o' for n, _ in old_members) == 1
        shutil.copy2(original_archive, output)
        subprocess.run(['xcrun', 'ar', '-r', str(output), str(target / 'mono-codeman.c.o')], env=env, check=True)
        new_members = members(output)
        assert collections.Counter((n,h) for n,h in old_members if n != 'mono-codeman.c.o') == collections.Counter((n,h) for n,h in new_members if n != 'mono-codeman.c.o')
        assert sum(n == 'mono-codeman.c.o' for n, _ in new_members) == 1
        deps = shlex.split((target / 'mono-codeman.d').read_text().replace('\\\n', ' ').split(':', 1)[1])
        receipt['targets'][name] = dict(original_archive=str(original_archive.relative_to(ROOT)), original_sha256=sha(original_archive), archive=str(output.relative_to(ROOT)), sha256=sha(output), replaced_member='mono-codeman.c.o', unchanged_members=len(old_members)-1, object_sha256=sha(target/'mono-codeman.c.o'), compile_database_sha256=sha(db), command=args, source_sha256={str(Path(p)):sha(Path(p)) for p in deps})
        print('PASS_ISOLATED_MONO_CODE_CHUNKS', name, 'unchanged members', len(old_members)-1, flush=True)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

if __name__ == '__main__':
    main()
