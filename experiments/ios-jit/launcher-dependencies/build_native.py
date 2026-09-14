#!/usr/bin/env python3
"""Compile pinned native ZIP/YAML dependencies and the Swift launcher module."""
import argparse,hashlib,json,os,platform,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2];D=R/'.build/ios-jit/launcher-dependencies-native-dependencies';O=R/'.build/ios-jit/launcher-dependencies-native'
p=argparse.ArgumentParser();p.add_argument('--target',choices=['host','ios','simulator'],default='host');a=p.parse_args();stage=O/a.target;stage.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer');sdkname={'host':'macosx','ios':'iphoneos','simulator':'iphonesimulator'}[a.target]
sdk=subprocess.check_output(['xcrun','--sdk',sdkname,'--show-sdk-path'],env=env,text=True).strip();target={'host':platform.machine()+'-apple-macos14.0','ios':'arm64-apple-ios26.0','simulator':platform.machine()+'-apple-ios26.0-simulator'}[a.target]
commands=[]
def run(cmd):
 commands.append(list(map(str,cmd)));x=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 with (stage/'build.log').open('a') as f:f.write(repr(cmd)+'\n'+x.stdout)
 if x.returncode:raise RuntimeError(x.stdout[-10000:])
(stage/'build.log').write_text('')
pins=json.loads((S/'native-dependencies.json').read_text())
D.mkdir(parents=True,exist_ok=True)
for name,pin in pins.items():
 checkout=D/name
 if not checkout.exists():
  run(['git','clone','--no-checkout',pin['url'],str(checkout)])
  run(['git','-C',str(checkout),'checkout','--detach',pin['commit']])
 assert subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==pin['commit'],name
 assert not subprocess.check_output(['git','-C',str(checkout),'diff','HEAD','--','Sources'],text=True).strip(),name+' tracked dependency sources changed'
ziproot=D/'ZIPFoundation';yaml=D/'Yams/Sources/CYaml';zipsources=sorted((ziproot/'Sources/ZIPFoundation').glob('*.swift'))
zipinputs={str(f.relative_to(R)):sha(f) for f in zipsources}
zipkey=hashlib.sha256((json.dumps(zipinputs,sort_keys=True)+target+sdk).encode()).hexdigest()
if not (stage/'zip-build-key.txt').exists() or (stage/'zip-build-key.txt').read_text()!=zipkey:
 run(['xcrun','swiftc','-swift-version','5','-O','-target',target,'-sdk',sdk,'-module-name','ZIPFoundation','-emit-library','-static','-emit-module','-emit-module-path',str(stage/'ZIPFoundation.swiftmodule'),'-o',str(stage/'libZIPFoundation.a'),*map(str,zipsources)])
 (stage/'zip-build-key.txt').write_text(zipkey)
objects=[]
for f in sorted((yaml/'src').glob('*.c')):
 obj=stage/(f.stem+'.o');objects.append(obj)
 run(['xcrun','clang','-target',target,'-isysroot',sdk,'-DYAML_DECLARE_STATIC','-O2','-g','-I'+str(yaml/'include'),'-c',str(f),'-o',str(obj)])
run(['xcrun','libtool','-static','-o',str(stage/'libCYaml.a'),*map(str,objects)])
sources=sorted((S/'native').glob('*.swift'));swift=stage/'libCJLauncher.a'
run(['xcrun','swiftc','-swift-version','5','-O','-g','-target',target,'-sdk',sdk,'-module-name','CJLauncher','-I',str(stage),'-I',str(yaml/'include'),'-emit-library','-static','-emit-module','-emit-module-path',str(stage/'CJLauncher.swiftmodule'),'-emit-objc-header-path',str(stage/'CJLauncher-Swift.h'),'-o',str(swift),*map(str,sources)])
inputs=sources+zipsources+sorted((yaml/'src').glob('*'))+sorted((yaml/'include').glob('*'))+[Path(__file__),S/"native-dependencies.json"]
receipt=dict(status='PASS_NATIVE_LAUNCHER_MODULE_BUILD',target=target,sdk=sdk,source_sha256={str(f.relative_to(R)):sha(f) for f in inputs if f.is_file()},libraries={str(f.relative_to(R)):sha(f) for f in [swift,stage/'libZIPFoundation.a',stage/'libCYaml.a']},dependency_commits={n:subprocess.check_output(['git','-C',str(D/n),'rev-parse','HEAD'],text=True).strip() for n in ['Yams','ZIPFoundation']},commands=commands)
(stage/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],a.target)
