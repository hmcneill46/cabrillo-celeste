#!/usr/bin/env python3
"""Exercise production native ZIP installation and actual HTTPS download on macOS."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/sj-lobby-store-tests';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
cmd=['xcrun','clang','-fobjc-arc','-g','-O1','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-fsanitize=address,undefined',str(S/'tests/ModStoreTests.m'),str(S/'src/CJModStore.m'),'-framework','Foundation','-o',str(O/'store-tests')]
subprocess.run(cmd,env=env,check=True)
with tempfile.TemporaryDirectory(prefix='fixture-',dir=O) as temp:
 run=subprocess.run([O/'store-tests',temp],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
(O/'run.log').write_text(run.stdout)
assert run.returncode==0 and 'PASS_CANCEL_PRESERVES_INSTALLED_MODS' in run.stdout,run.stdout
assert 'ERROR: AddressSanitizer' not in run.stdout and 'runtime error:' not in run.stdout
files=[Path(__file__),S/'src/CJModStore.m',S/'src/CJModStore.h',S/'tests/ModStoreTests.m',O/'run.log',O/'store-tests']
receipt=dict(status='PASS_ATOMIC_MOD_IMPORT_HTTPS_DOWNLOAD_REUSE_CANCEL_ASAN_UBSAN',command=cmd,files={str(p.relative_to(R)):sha(p) for p in files},phone_downloader_tested=False)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(run.stdout)
