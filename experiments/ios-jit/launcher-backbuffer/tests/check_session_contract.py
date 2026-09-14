#!/usr/bin/env python3
"""Exercise the compiled process-lifetime ABI, concurrent Quit and stage ordering."""
import hashlib,json,os,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-backbuffer-validation';O.mkdir(parents=True,exist_ok=True)
sources=[S/'src/CJSession.c',S/'src/CJSession.h',S/'tests/session_contract.c',Path(__file__)]
command=['xcrun','clang','-std=c11','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(S/'src'),str(sources[0]),str(sources[2]),'-o',str(O/'session-contract')]
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
subprocess.run(command,env=env,check=True)
result=subprocess.run([str(O/'session-contract')],text=True,capture_output=True,check=True)
assert result.stdout.strip()=='PASS_SESSION_ABI_ORDER_CONCURRENT_QUIT_AND_CLOSED_LIFETIME' and not result.stderr
(O/'session-contract.log').write_text(result.stdout)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'session-contract.json').write_text(json.dumps(dict(status=result.stdout.strip(),source_sha256={str(p.relative_to(R)):sha(p) for p in sources},executable_sha256=sha(O/'session-contract'),log_sha256=sha(O/'session-contract.log'),concurrent_requests=32,sanitizers=['address','undefined'],command=command),indent=2)+'\n')
print(result.stdout.strip())
