#!/usr/bin/env python3
"""Production catalogue parsing/cache/cancellation and selected-root transactions."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-catalogue-tests';N=R/'.build/ios-jit/launcher-catalogue-native/host';D=R/'.build/ios-jit/launcher-catalogue-native-dependencies'
O.mkdir(parents=True,exist_ok=True)
for name in ['cache','cancel-cache','invalid-cache','profile','live-profile']:
 p=O/name
 if p.exists():shutil.rmtree(p)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
sources=sorted((S/'native').glob('*.swift'))+[S/'tests/CatalogueTests.swift']
cmd=['xcrun','swiftc','-swift-version','5','-O','-g','-I',str(N),'-I',str(D/'Yams/Sources/CYaml/include'),*map(str,sources),str(N/'libZIPFoundation.a'),str(N/'libCYaml.a'),'-o',str(O/'tests')]
p=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/'compile.log').write_text(p.stdout)
if p.returncode:print(p.stdout[-10000:]);sys.exit(p.returncode)
args=[str(O/'tests'),str(O),str(R/'.build/ios-jit/launcher-catalogue-service'),str(R/'.build/ios-jit/launcher-catalogue-install-tests/fixtures'),'--live']
p=subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=480);(O/'run.log').write_text(p.stdout)
if p.returncode:print(p.stdout[-10000:]);sys.exit(p.returncode)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((O/'results.json').read_text());assert result['status']=='PASS_NATIVE_CATALOGUE_CONTRACT_CACHE_INSTALLS'
(O/'receipt.json').write_text(json.dumps(dict(status=result['status'],source_sha256={str(p.relative_to(R)):sha(p) for p in sources+[Path(__file__)]},results={n:sha(O/n) for n in ['results.json','run.log','live-results.json']},commands=[cmd,args]),indent=2)+'\n');print(p.stdout)
