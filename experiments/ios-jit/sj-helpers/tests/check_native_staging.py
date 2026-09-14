#!/usr/bin/env python3
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
OUT=ROOT/'.build/ios-jit/sj-helpers-native-tests';OUT.mkdir(exist_ok=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
files=[SOURCE/'tests/content_staging.m',SOURCE/'src/CJContentImport.m',SOURCE/'src/CJContentImport.h']
cmd=['xcrun','clang','-fobjc-arc','-O2','-g','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-I'+str(SOURCE/'src'),*map(str,files[:2]),'-framework','Foundation','-o',str(OUT/'staging-test')]
subprocess.run(cmd,env=env,check=True)
with tempfile.TemporaryDirectory(prefix='native-',dir=OUT) as work:
    r=subprocess.run([str(OUT/'staging-test'),work],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=100)
(OUT/'run.log').write_text(r.stdout);print(r.stdout)
assert r.returncode==0 and 'PASS_NATIVE_CONTENT_STAGING' in r.stdout
(OUT/'receipt.json').write_text(json.dumps(dict(status='PASS_NATIVE_CONTENT_STAGING',source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},command=cmd,log_sha256=hashlib.sha256(r.stdout.encode()).hexdigest(),scope='Actual Foundation/NSFileCoordinator native staging on macOS; iCloud document provider selection is a phone gate'),indent=2)+'\n')
