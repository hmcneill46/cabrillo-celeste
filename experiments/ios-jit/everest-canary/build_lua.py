#!/usr/bin/env python3
"""Build pinned Lua 5.4.8 for the native iOS host and matching Mac tests."""
import hashlib
import json
import os
import subprocess
import tarfile
import urllib.request
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/everest-lua'
URL = 'https://www.lua.org/ftp/lua-5.4.8.tar.gz'
DIGEST = '4f18ddae154e793e46eeab727c59ef1c0c0c2b744e7b94219710d76f530629ae'


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    archive = STAGE / 'lua-5.4.8.tar.gz'
    if not archive.exists(): urllib.request.urlretrieve(URL, archive)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(archive) == DIGEST
    source = STAGE / 'lua-5.4.8/src'
    if not source.exists():
        with tarfile.open(archive) as stream: stream.extractall(STAGE, filter='data')
    oslib = source / 'loslib.c'
    original = oslib.read_text()
    marker = 'static int os_execute (lua_State *L) {\n'
    replacement = marker + '#if defined(CJIT_IOS)\n  return luaL_error(L, "External processes are unavailable in the iOS host");\n#else\n'
    if marker in original and replacement not in original:
        start = original.index(marker)
        end = original.index('\n}', start)
        text = original[:end] + '\n#endif' + original[end:]
        oslib.write_text(text.replace(marker, replacement, 1))
    assert replacement in oslib.read_text()
    commands = []
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')

    def run(args):
        commands.append(list(map(str, args)))
        result = subprocess.run(list(map(str, args)), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with (STAGE / 'build.log').open('a') as stream: stream.write(repr(commands[-1]) + '\n' + result.stdout)
        if result.returncode: raise RuntimeError(result.stdout)
        return result.stdout.strip()

    libraries = {}
    for name, sdk, target in [('ios', 'iphoneos', 'arm64-apple-ios26.0'), ('simulator', 'iphonesimulator', 'x86_64-apple-ios26.0-simulator'), ('host', 'macosx', 'x86_64-apple-macos12.0')]:
        output = STAGE / name
        output.mkdir(exist_ok=True)
        sdkpath = run(['xcrun', '--sdk', sdk, '--show-sdk-path'])
        objects = []
        for path in sorted(source.glob('*.c')):
            if path.name in ['lua.c', 'luac.c']: continue
            obj = output / (path.stem + '.o')
            flags = ['-DCJIT_IOS=1'] if name != 'host' else ['-DLUA_USE_MACOSX=1']
            run(['xcrun', '--sdk', sdk, 'clang', '-target', target, '-isysroot', sdkpath, '-O2', '-g', '-fPIC', *flags, '-c', path, '-o', obj])
            objects.append(obj)
        library = output / 'liblua54.a'
        run(['xcrun', 'libtool', '-static', '-o', library, *objects])
        libraries[name] = dict(target=target, path=str(library.relative_to(ROOT)), sha256=sha(library))
        if name == 'host':
            dylib = output / 'liblua54.dylib'
            run(['xcrun', 'clang', '-target', target, '-dynamiclib', *objects, '-install_name', '@rpath/liblua54.dylib', '-o', dylib])
            libraries[name]['dylib_sha256'] = sha(dylib)
        print('LUA_BUILT', name, flush=True)
    receipt = dict(schema=1, status='PASS_LUA_5_4_8_NATIVE_BUILD', source_url=URL, archive_sha256=DIGEST,
                   checksum_source='https://www.lua.org/ftp/', kerlua_package='1.4.7',
                   kerlua_repository_commit='20113b5267f18fdf9f153ba4acaed2c6c8d1d3e1',
                   source_sha256={p.name: sha(p) for p in sorted(source.iterdir()) if p.suffix in ['.c', '.h']},
                   libraries=libraries, commands=commands, ios_external_processes=False,
                   lua_jit_enabled=False, managed_interpreter_enabled=False, runtime_tested=False)
    (STAGE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
