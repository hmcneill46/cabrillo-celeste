#!/usr/bin/env python3
"""Compile the production parser and run import/selection failures plus the real SJ ZIP corpus."""
import json,os,shutil,stat,struct,subprocess,zipfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-dependencies-mod-library-tests';N=R/'.build/ios-jit/launcher-dependencies-native/host';D=R/'.build/ios-jit/launcher-dependencies-native-dependencies'
if O.exists():shutil.rmtree(O)
F=O/'fixtures';F.mkdir(parents=True)
def write(name,meta=None,extra=None):
 with zipfile.ZipFile(F/(name+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  if meta is not None:z.writestr('everest.yaml',meta)
  for n,b in (extra or {}).items():z.writestr(n,b)
write('reserved-support','- Name: CelesteIOS\n  Version: 99.0.0\n')
write('support-consumer','- Name: UsesIOS\n  Version: 1.0.0\n  Dependencies: [{Name: CelesteIOS, Version: 1.0.0}]\n')
write('consumer','- Name: Consumer\n  Version: 1.0\n  Dependencies:\n    - Name: Helper\n      Version: 1.9\n')
write('dependency','- Name: Helper\n  Version: 1.10\n');write('duplicate','- Name: Helper\n  Version: 1.11\n')
write('optional','- Name: Optional\n  Version: 1.0\n  OptionalDependencies:\n    - Name: Helper\n      Version: 2.0\n')
write('traversal',extra={'../escape':'bad'});write('missing-dll','- Name: Missing\n  Version: 1.0\n  DLL: No.dll\n')
write('bad-yaml','[[[broken');write('oversize-yaml',' '*1048577)
write('recursive-alias','- &self {Name: Loop, Version: 1.0, Dependencies: [*self]}')
write('multi-document','---\n- Name: First\n---\n- Name: Second\n');write('duplicate-key','- Name: First\n  Name: Second\n')
write('multi','- Name: A\n  Version: 1.0\n  Dependencies: &deps [{Name: API, Version: 1.0}]\n- Name: B\n  Version: 1.0\n  Dependencies: *deps\n')
write('asset',extra={'Graphics/hello.txt':'asset test'})
write('cycle','- Name: A\n  Dependencies: [{Name: B, Version: 1.0}]\n- Name: B\n  Dependencies: [{Name: A, Version: 1.0}]\n')
with zipfile.ZipFile(F/'symlink.zip','w') as z:
 e=zipfile.ZipInfo('link');e.create_system=3;e.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(e,'../../outside')
with zipfile.ZipFile(F/'duplicate-entry.zip','w') as z:z.writestr('x','one');z.writestr('x','two')
write('bad-crc','- Name: CRC\n  Version: 1.0\n');p=F/'bad-crc.zip';d=bytearray(p.read_bytes());i=d.index(b'PK\x01\x02');struct.pack_into('<I',d,i+16,123);p.write_bytes(d)
mods=O/'full/Mods';mods.mkdir(parents=True)
for p in (R/'.build/ios-jit/sj-lobby-mods').glob('*.zip'):os.link(p,mods/p.name)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
subprocess.run(['xcrun','swiftc','-swift-version','5','-O','-I',str(N),'-I',str(D/'Yams/Sources/CYaml/include'),*map(str, sorted((S/'native').glob('*.swift'))),str(S/'tests/ModLibraryTests.swift'),str(N/'libZIPFoundation.a'),str(N/'libCYaml.a'),'-o',str(O/'tests')],env=env,check=True)
subprocess.run([str(O/'tests'),str(O)],check=True)

subprocess.run(['xcrun','swiftc','-swift-version','5','-O','-I',str(N),'-I',str(D/'Yams/Sources/CYaml/include'),*map(str, sorted((S/'native').glob('*.swift'))),str(S/'tests/CatalogueTool.swift'),str(N/'libZIPFoundation.a'),str(N/'libCYaml.a'),'-o',str(O/'catalogue')],env=env,check=True)
