#!/usr/bin/env python3
"""Restore the accepted assembly-scoped Mono visibility rule in a new archive."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

from platform_inputs import ROOT, owned, sha, validate_native

ORIGINAL = 'd9fcfdb3420cfba298bbe954cc69199da0f270fd9890f3ae1210d8ae7aec4bfd'
PATCHED = 'c7630e2d48e3b2b3231b53777ff8667a52a798cec72f6f9e7d9e978a1e1841b0'
DEVELOPER = '/Applications/Xcode-26.6.app/Contents/Developer'


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
            length = int(name[3:]); name = payload[:length].rstrip(b'\0').decode()
            payload = payload[length:]
        else:
            name = name.rstrip('/')
        if not name.startswith('__.SYMDEF'):
            result.append((name, hashlib.sha256(payload).hexdigest()))
        pos += 60 + size + size % 2
    assert pos == len(data)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', required=True)
    a = p.parse_args(); work = owned(a.work)
    assert ROOT / '.build' in work.parents and not work.exists()
    base, selected = validate_native()
    pin = json.loads((ROOT / 'experiments/ios-jit/launcher-platforms/NativePayload.json').read_text())
    base_path = owned(pin['receipt']); base_work = base_path.parent
    original = base_work / 'runtime/src/mono/mono/metadata/class.c'
    assert sha(original) == ORIGINAL
    before = original.read_text()
    old = 'MonoImage *member_klass_image = m_class_get_image (member_klass);\n\t/* Partition I 8.5.3.2 */'
    new = old.replace('\n\t/* Partition', '\n\t/* CJIT: protected members also belong to the explicitly granted assembly. */\n\tif (ignores_access_checks_to (access_klass_assembly, member_klass_image->assembly))\n\t\treturn TRUE;\n\t/* Partition')
    assert before.count(old) == 1
    after = before.replace(old, new)
    assert hashlib.sha256(after.encode()).hexdigest() == PATCHED
    work.mkdir(parents=True)
    source = work / 'class.c'; source.write_text(after)
    patch = work / 'mono8-visibility.patch'
    patch.write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/src/mono/mono/metadata/class.c', tofile='b/src/mono/mono/metadata/class.c')))
    env = dict(os.environ, DEVELOPER_DIR=DEVELOPER, CLANG_MODULE_CACHE_PATH=str(work / 'module-cache'))
    commands = []
    def run(cmd, label, cwd=work):
        cmd = list(map(str, cmd)); commands.append(cmd)
        with (work / (label + '.log')).open('w') as log:
            r = subprocess.run(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        if r.returncode: raise RuntimeError(label + ' failed; inspect ' + str(work / (label + '.log')))
        print('PASS ' + label, flush=True)

    def replace(target, db, baseline, source_file):
        dest = work / target; dest.mkdir()
        row = next(r for r in json.loads(db.read_text()) if r['file'].endswith('/metadata/class.c'))
        argv = shlex.split(row['command']); obj = dest / 'class.c.o'
        argv[argv.index('-o') + 1] = str(obj)
        argv[argv.index(row['file'])] = str(source_file)
        argv += ['-iquote', str(Path(row['file']).parent), '-MMD', '-MF', str(dest / 'class.d')]
        run(argv, target + '-compile', Path(row['directory']))
        output = dest / 'libmonosgen-2.0.a'; shutil.copyfile(baseline, output)
        run(['xcrun', 'ar', '-r', output, obj], target + '-archive')
        before_members, after_members = members(baseline), members(output)
        assert sum(n == 'class.c.o' for n, _ in before_members) == 1
        assert sum(n == 'class.c.o' for n, _ in after_members) == 1
        assert Counter((n, h) for n, h in before_members if n != 'class.c.o') == Counter((n, h) for n, h in after_members if n != 'class.c.o')
        deps = shlex.split((dest / 'class.d').read_text().replace('\\\n', ' ').split(':', 1)[1])
        deps = [Path(n) if Path(n).is_absolute() else Path(row['directory']) / n for n in deps]
        assert all(ROOT in n.resolve().parents for n in deps)
        return dict(path=str(output.relative_to(ROOT)), sha256=sha(output), baseline_sha256=sha(baseline),
                    unchanged_members=len(before_members)-1, replaced_member='class.c.o', object_sha256=sha(obj),
                    class_sha256=sha(source_file), compile_database=str(db.relative_to(ROOT)), compile_database_sha256=sha(db),
                    dependencies={str(n.resolve().relative_to(ROOT)):sha(n) for n in deps})

    ios_base = owned(base['libraries']['libmonosgen-2.0.a']['path'])
    ios = replace('ios', base_work / 'mono/compile_commands.json', ios_base, source)
    # Configure the same imported source for macOS, then replace just class.c in
    # the accepted host archive. This creates both the broken-source control and
    # the corrected runtime without substituting a different metadata source.
    runtime = work / 'host-runtime'
    inputs = owned(base['input_manifest']).parent
    run(['cp', '-cR', inputs / 'runtime', runtime], 'host-source')
    build = work / 'host-config'; build.mkdir()
    generated = runtime / 'artifacts/obj'; generated.mkdir(parents=True, exist_ok=True)
    for name, dest in [('version.h', '_version.h'), ('version.c', '_version.c'), ('runtime_version.h', 'runtime_version.h')]:
        shutil.copyfile(base_work / 'mono' / name, build / name)
        shutil.copyfile(build / name, generated / dest)
    sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=env, text=True).strip()
    compiler = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--find', 'clang'], env=env, text=True).strip()
    flags = '-I' + str(ROOT / 'experiments/ios-jit/managed-canary/src') + ' -I' + str(ROOT / 'experiments/ios-jit/launcher-platforms/src')
    run(['cmake', '-S', runtime / 'src/mono', '-B', build, '-G', 'Unix Makefiles',
         '-DCMAKE_SYSTEM_NAME=Darwin', '-DCMAKE_SYSTEM_PROCESSOR=x86_64', '-DCMAKE_OSX_ARCHITECTURES=x86_64',
         '-DCMAKE_OSX_SYSROOT=' + sdk, '-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0',
         '-DCMAKE_C_COMPILER=' + compiler, '-DCMAKE_CXX_COMPILER=' + compiler + '++',
         '-DCMAKE_BUILD_TYPE=Release', '-DCLR_CMAKE_HOST_ARCH=x64', '-DCLR_CMAKE_TARGET_ARCH=x64', '-DCLR_CMAKE_TARGET_OS=darwin',
         '-DDISABLE_JIT=OFF', '-DDISABLE_INTERPRETER=ON', '-DDISABLE_AOT=ON', '-DDISABLE_EXECUTABLES=ON',
         '-DDISABLE_SHARED_LIBS=ON', '-DDISABLE_EVENTPIPE=ON', '-DENABLE_PERFTRACING=OFF',
         '-DDISABLE_DEBUGGER_AGENT=ON', '-DSTATIC_COMPONENTS=ON', '-DDISABLE_LLDB=ON', '-DGC_SUSPEND=coop',
         '-DENABLE_WERROR=OFF', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON', '-DCLR_CMAKE_KEEP_NATIVE_SYMBOLS=ON',
         '-DVERSION_HEADER_PATH=' + str(build / 'version.h'), '-DVERSION_FILE_PATH=' + str(build / 'version.c'),
         '-DRUNTIME_VERSION_HEADER_PATH=' + str(build / 'runtime_version.h'),
         '-DCMAKE_C_FLAGS=' + flags, '-DCMAKE_CXX_FLAGS=' + flags], 'host-configure')
    host_base = ROOT / '.private/loading-inputs/host/native/libmonosgen-2.0.a'
    manifest = json.loads((ROOT / '.private/loading-inputs/manifest.json').read_text())
    assert sha(host_base) == manifest['files'][str(host_base.relative_to(ROOT))]['sha256']
    host_control = replace('host-control', build / 'compile_commands.json', host_base, original)
    host_fixed = replace('host-fixed', build / 'compile_commands.json', host_base, source)
    libraries = dict(base['libraries']); libraries['libmonosgen-2.0.a'] = {k:ios[k] for k in ['path', 'sha256']}
    public = {str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))}
    public.update(base['source_sha256'])
    public['tools/platform_inputs.py'] = sha(ROOT / 'tools/platform_inputs.py')
    receipt = dict(schema=1, status='PASS_SCOPED_VISIBILITY_RUNTIME_RESTORE', deployment_target='15.0',
                   base_receipt=str(base_path.relative_to(ROOT)), base_receipt_sha256=sha(base_path),
                   input_manifest=base['input_manifest'], input_manifest_sha256=base['input_manifest_sha256'],
                   source_sha256=public, libraries=libraries, ios=ios, host_control=host_control, host_fixed=host_fixed,
                   original_class_sha256=ORIGINAL, patched_class_sha256=PATCHED, patch_sha256=sha(patch), commands=commands,
                   physical_device_tested=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__': main()
