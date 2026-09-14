#!/usr/bin/env python3
"""Build the isolated custom Mono runtime with Xcode 26.6; no Apple workload/AOT checkout writes."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
source=Path(__file__).resolve().parent
root=source.parents[2]
base=root/'.build/ios-jit/managed-runtime'
runtime=base/'runtime-v8.0.28'
build=base/'mono-build-ios'
pin=json.loads((source/'runtime-pin.json').read_text())
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--configure-only',action='store_true');a=p.parse_args()
build.mkdir(parents=True,exist_ok=True)
actual=subprocess.check_output(['git','-C',str(runtime),'rev-parse','HEAD'],text=True).strip()
assert actual==pin['runtime_commit']
patch=json.loads((base/'runtime-patch-receipt.json').read_text())
assert patch['runtime_commit']==actual
for name,hashes in patch['files'].items():
 assert hashlib.sha256((runtime/name).read_bytes()).hexdigest()==hashes['patched_sha256'],name
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
sdk=subprocess.check_output(['xcrun','--sdk','iphoneos','--show-sdk-path'],env=env,text=True).strip()
compiler=subprocess.check_output(['xcrun','--sdk','iphoneos','--find','clang'],env=env,text=True).strip()
(build/'version.h').write_text('#define VER_PRODUCTVERSION_STR "8.0.28.0"\n')
(build/'version.c').write_text('static char sccsid[] __attribute__((used)) = "@(#)Version 8.0.28.0 @Commit: '+actual+'";\n')
(build/'runtime_version.h').write_text('#define RuntimeProductMajorVersion 8\n#define RuntimeProductMinorVersion 0\n#define RuntimeProductPatchVersion 28\n')
version_dir=runtime/'artifacts/obj';version_dir.mkdir(parents=True,exist_ok=True)
for local,name in [('version.h','_version.h'),('version.c','_version.c'),('runtime_version.h','runtime_version.h')]:
 (version_dir/name).write_bytes((build/local).read_bytes())
flags='-DCJ_MONO_IOS_JIT=1 -I'+str(source/'src')
args=['cmake','-S',str(runtime/'src/mono'),'-B',str(build),'-G','Unix Makefiles',
 '-DCMAKE_SYSTEM_NAME=iOS','-DCMAKE_SYSTEM_PROCESSOR=arm64','-DCMAKE_OSX_ARCHITECTURES=arm64',
 '-DCMAKE_OSX_SYSROOT='+sdk,'-DCMAKE_OSX_DEPLOYMENT_TARGET=26.0','-DCMAKE_C_COMPILER='+compiler,'-DCMAKE_CXX_COMPILER='+compiler+'++',
 '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INSTALL_PREFIX='+str(build/'out'),'-DCMAKE_INSTALL_LIBDIR=lib',
 '-DCLR_CMAKE_HOST_ARCH=arm64','-DCLR_CMAKE_TARGET_ARCH=arm64','-DCLR_CMAKE_TARGET_OS=ios',
 '-DDISABLE_JIT=OFF','-DDISABLE_INTERPRETER=ON','-DDISABLE_AOT=ON','-DDISABLE_EXECUTABLES=ON','-DDISABLE_SHARED_LIBS=ON',
 '-DDISABLE_EVENTPIPE=ON','-DENABLE_PERFTRACING=OFF','-DDISABLE_DEBUGGER_AGENT=ON','-DSTATIC_COMPONENTS=ON',
 '-DDISABLE_LLDB=ON','-DGC_SUSPEND=coop','-DENABLE_WERROR=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
 '-DVERSION_HEADER_PATH='+str(build/'version.h'),'-DVERSION_FILE_PATH='+str(build/'version.c'),'-DRUNTIME_VERSION_HEADER_PATH='+str(build/'runtime_version.h'),
 '-DCMAKE_C_FLAGS='+flags,'-DCMAKE_CXX_FLAGS='+flags,'-DCLR_CMAKE_KEEP_NATIVE_SYMBOLS=ON']
(base/'runtime-build-commands.json').write_text(json.dumps({'configure':args,'env':{'DEVELOPER_DIR':env['DEVELOPER_DIR']}},indent=2)+'\n')
with (base/'runtime-configure.log').open('w') as log:
 result=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:
 print((base/'runtime-configure.log').read_text()[-9000:]);raise SystemExit(result.returncode)
print('CONFIGURED',flush=True)
if not a.configure_only:
 with (base/'runtime-build.log').open('w') as log:
  result=subprocess.run(['cmake','--build',str(build),'--target','monosgen-static','mono-component-marshal-ilgen-static','mono-component-debugger-stub-static','mono-component-hot_reload-stub-static','mono-component-diagnostics_tracing-stub-static','--parallel','4'],env=env,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:print((base/'runtime-build.log').read_text()[-12000:]);raise SystemExit(result.returncode)
 print('BUILT_MONO_IOS_STATIC_RUNTIME',flush=True)
