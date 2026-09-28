#!/usr/bin/env python3
"""Compile/run the native launch reducer and exercise generated shortcut branches.

These are host controls, not a claim that iOS Shortcuts/VPN/JIT has passed on-device.
"""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
from check_shortcut_files46 import shortcut_checks, url_connection_controls

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-shortcut-completion'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
    work=a.work.absolute();work.mkdir(parents=True,exist_ok=False)
    files=[SOURCE/'tests/ShortcutSessionTests.m',*[SOURCE/'src'/n for n in ['CJShortcutSession.m','CJShortcutPlatform.m','CJPlatformOptions.m']]]
    env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
    command=['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-I'+str(SOURCE/'src'),*[str(f) for f in files],'-framework','Foundation','-o',str(work/'test')]
    subprocess.run(command,env=env,check=True)
    native=subprocess.check_output([work/'test',work/'journals'],text=True)
    original=ROOT/'experiments/ios-jit/launcher-shortcut-guests/src/CJShortcutSession.m'
    original_command=[str(original) if value==str(SOURCE/'src/CJShortcutSession.m') else
                      str(work/'original-test') if value==str(work/'test') else value for value in command]
    subprocess.run(original_command,env=env,check=True)
    failure=subprocess.run([work/'original-test',work/'original-journals'],capture_output=True,text=True)
    (work/'original-result.txt').write_text(failure.stdout+failure.stderr)
    assert failure.returncode==1 and 'FAIL native success completes without shortcut receipt' in failure.stderr
    branches=shortcut_checks();connection_controls=url_connection_controls()
    receipt=dict(status='PASS_HOST_SHORTCUT_CONTROLS',native=native.strip(),shortcut_branches=len(branches),checks=branches,
                 rejected_broken_url_connections=connection_controls,original43_missing_callback_failure_reproduced=True,
                 physical_device_tested=False,source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files+[original,Path(__file__),ROOT/'tools/build_shortcut_files46.py',ROOT/'tools/check_shortcut_files46.py']})
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(native.strip());print('PASS',len(branches),'generated shortcut branches')

if __name__=='__main__':main()
