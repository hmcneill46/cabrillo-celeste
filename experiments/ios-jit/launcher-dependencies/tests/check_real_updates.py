#!/usr/bin/env python3
import hashlib,json,os,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit';O=B/'launcher-dependencies-real-updates';N=B/'launcher-dependencies-native/host';D=B/'launcher-dependencies-native-dependencies'
O.mkdir(exist_ok=True);mods=O/'Profile/Mods';mods.mkdir(parents=True,exist_ok=True)
for p in (B/'sj-lobby-mods').glob('*.zip'):
 if not (mods/p.name).exists():os.link(p,mods/p.name)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
cmd=['xcrun','swiftc','-swift-version','5','-O','-g','-I',str(N),'-I',str(D/'Yams/Sources/CYaml/include'),*map(str,sorted((S/'native').glob('*.swift'))),str(S/'tests/RealUpdateTests.swift'),str(N/'libZIPFoundation.a'),str(N/'libCYaml.a'),'-o',str(O/'tests')]
p=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/'compile.log').write_text(p.stdout)
assert not p.returncode,p.stdout
p=subprocess.run([str(O/'tests'),str(O),str(B/'launcher-dependencies-service/references'),str(S/'CompatibilityDownloads.json')],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900);(O/'run.log').write_text(p.stdout)
assert not p.returncode,p.stdout
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'receipt.json').write_text(json.dumps(dict(status='PASS_REAL_TWO_MOD_UPDATE_TRANSACTION',result_sha256=sha(O/'result.json'),source_sha256={str(p.relative_to(R)):sha(p) for p in sorted((S/'native').glob('*.swift'))+[Path(__file__),S/'tests/RealUpdateTests.swift']},command=cmd),indent=2)+'\n');print('PASS_REAL_TWO_MOD_UPDATE_TRANSACTION')
