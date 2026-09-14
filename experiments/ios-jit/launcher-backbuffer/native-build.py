#!/usr/bin/env python3
"""Build the isolated pinned FNA3D callback adaptation for iOS and host regression."""
import hashlib, json, os, shutil, subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
STAGE = ROOT / '.build/ios-jit/launcher-backbuffer-renderer'
BASE = ROOT / '.build/ios-jit/game-native/work/sources'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    env['CLANG_MODULE_CACHE_PATH'] = str(STAGE / 'module-cache')
    commands = []
    def run(args, cwd=None):
        args = list(map(str, args)); commands.append(args)
        result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with (STAGE/'build.log').open('a') as log: log.write(repr(args)+'\n'+result.stdout+'\n')
        if result.returncode: raise RuntimeError(result.stdout[-6000:])
        return result.stdout
    original = BASE / 'FNA3D'
    pin = run(['git', '-C', original, 'rev-parse', 'HEAD']).strip()
    assert pin == 'dba98a71514cc30f3c19dc19fc0a479be7c90d52'
    (STAGE/'source-state.json').write_text(json.dumps(dict(schema=1, owner='CJIT backbuffer build 24', fna3d_revision=pin))+'\n')
    work = STAGE / 'sources/FNA3D'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(original, work, ignore=shutil.ignore_patterns('.git'))
    sdl = STAGE / 'sources/SDL2/include'
    shutil.copytree(BASE/'SDL2/include', sdl, dirs_exist_ok=True)
    patch = SOURCE/'native/fna3d-callback.patch'
    run(['git', 'apply', '--check', patch], cwd=work)
    run(['git', 'apply', patch], cwd=work)
    backbuffer_patch=SOURCE/'native/fna3d-backbuffer.patch'
    run(['git','apply','--check',backbuffer_patch],cwd=work)
    run(['git','apply',backbuffer_patch],cwd=work)
    output = STAGE/'stage/ios-arm64/libFNA3D.a'; output.parent.mkdir(parents=True, exist_ok=True)
    (STAGE/'logs').mkdir(exist_ok=True)
    run(['xcodebuild', 'build', '-project', work/'Xcode-iOS/FNA3D.xcodeproj', '-target', 'FNA3D',
         '-configuration', 'Release', '-sdk', 'iphoneos', 'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=NO',
         'IPHONEOS_DEPLOYMENT_TARGET=26.0', 'CODE_SIGNING_ALLOWED=NO', 'CODE_SIGNING_REQUIRED=NO',
         'GCC_GENERATE_DEBUGGING_SYMBOLS=YES', 'DEBUG_INFORMATION_FORMAT=dwarf',
         'OBJROOT='+str(STAGE/'derived/obj'), 'SYMROOT='+str(STAGE/'derived/sym'),
         'CONFIGURATION_BUILD_DIR='+str(STAGE/'work/ios-products')])
    run(['python3', ROOT/'scripts/finalize-apple-archive.py', '--build-root', STAGE,
         '--input', STAGE/'work/ios-products/libFNA3D.a', '--output', output,
         '--report', STAGE/'logs/archive-construction.json'])
    # The real pinned renderer is tested on macOS too. The test's SDL dylib is
    # private desktop input; it is never packaged in the phone app.
    desktop = Path('/Users/harrymcneill/Projects/Celeste Required Files/Celeste Untouched.app/Contents/MacOS/osx')
    host = STAGE/'host'; host.mkdir(exist_ok=True)
    shutil.copy2(desktop/'libSDL2-2.0.0.dylib', host/'libSDL2-2.0.0.dylib')
    run(['cmake', '-S', work, '-B', host, '-DCMAKE_BUILD_TYPE=RelWithDebInfo',
         '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', '-DSDL2_INCLUDE_DIRS='+str(sdl),
         '-DSDL2_LIBRARIES='+str(host/'libSDL2-2.0.0.dylib')])
    run(['cmake', '--build', host, '--parallel', '4'])
    exports = run(['xcrun','nm','-g','-U','-j',output])
    assert '_FNA3D_CJIT_EndCallback' in exports.splitlines()
    receipt = dict(schema=1, fna3d_revision=pin, patch_sha256=sha(patch),
        backbuffer_patch_sha256=sha(backbuffer_patch), builder_sha256=sha(Path(__file__)),
        original_metal_sha256=sha(original/'src/FNA3D_Driver_Metal.c'),
        patched_metal_sha256=sha(work/'src/FNA3D_Driver_Metal.c'),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted((STAGE/'sources').rglob('*')) if p.is_file()},
        ios_archive=str(output.relative_to(ROOT)), ios_archive_sha256=sha(output),
        host_library=str((host/'libFNA3D.0.dylib').relative_to(ROOT)),
        host_library_sha256=sha(host/'libFNA3D.0.dylib'),
        base_ios_archive_sha256=sha(ROOT/'.build/ios-jit/game-native-output/FNA3D.xcframework/ios-arm64/libFNA3D.a'),
        commands=commands, xcode=run(['xcodebuild','-version']).strip(),
        base_native_tree_unchanged=True, scope='Retained Metal backbuffer read, deferred clear and MSAA preservation; inherited callback/reset adaptation unchanged')
    (STAGE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('ios_archive_sha256','host_library_sha256','patch_sha256')}))

if __name__ == '__main__': main()
