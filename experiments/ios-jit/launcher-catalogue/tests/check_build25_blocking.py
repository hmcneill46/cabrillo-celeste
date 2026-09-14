#!/usr/bin/env python3
"""Run direct blocked-update/apply controls against immutable build25 source."""
import hashlib,json,os,subprocess,shutil
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];B=R/'.build/ios-jit'
old=R/'experiments/ios-jit/launcher-dependencies';N=B/'launcher-dependencies-native/host';D=B/'launcher-dependencies-native-dependencies'
O=B/'launcher-catalogue-build25-control';O.mkdir(parents=True,exist_ok=True)
shutil.copytree(B/'launcher-runtime-install-tests/fixtures',O/'fixtures',dirs_exist_ok=True)
test=(S/'tests/InstallTests.swift').read_text()
helpers=test[:test.index('func plannerTests()')]
definitions=test[test.index('    static var base:'):test.index('    static func main()')]
waiter=test[test.index('    static func awaitState('):test.index('    static func engine()')]
blocked=test[test.index('    static func blockedUpdates()'):test.index('    static func automatic()')]
source=O/'Build25BlockedControl.swift'
source.write_text(helpers+'\n@main struct Build25BlockedControl {\n'+definitions+waiter+blocked+'\nstatic func main() throws { try blockedUpdates() }\n}\n')
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
inputs=sorted((old/'native').glob('*.swift'))
cmd=['xcrun','swiftc','-swift-version','5','-O','-g','-I',str(N),'-I',str(D/'Yams/Sources/CYaml/include'),*map(str,inputs),str(source),str(N/'libZIPFoundation.a'),str(N/'libCYaml.a'),'-o',str(O/'control')]
p=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/'compile.log').write_text(p.stdout)
assert p.returncode==0,p.stdout[-8000:]
p=subprocess.run([str(O/'control'),'blocked',str(O)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(O/'run.log').write_text(p.stdout);assert p.returncode==0,p.stdout[-8000:]
result=O/'blocked.json';(O/'result.json').write_bytes(result.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(status='PASS_ORIGINAL_BUILD25_REJECTS_BLOCKED_UPDATES_AND_APPLY',source_sha256={str(p.relative_to(R)):sha(p) for p in inputs+[source,Path(__file__),S/'tests/InstallTests.swift']},result_sha256=sha(O/'result.json'),physical_execution=False)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
