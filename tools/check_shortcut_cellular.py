#!/usr/bin/env python3
"""Compile/run the native launch reducer and exercise generated shortcut branches.

These are host controls, not a claim that iOS Shortcuts/VPN/JIT has passed on-device.
"""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
import check_shortcut_files49 as workflow_controls
import build_shortcut_files49 as generator
workflow_controls.generator=generator
workflow_controls.generate=generator.generate
workflow_controls.launch_url=generator.launch_url
shortcut_checks=workflow_controls.shortcut_checks
url_connection_controls=workflow_controls.url_connection_controls

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'experiments/ios-jit/launcher-shortcut-cellular'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);a=p.parse_args()
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
    install_files=[SOURCE/'tests/ShortcutInstallTests.m',SOURCE/'src/CJShortcutInstall.m',SOURCE/'src/CJShortcutPlatform.m']
    install_command=['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-I'+str(SOURCE/'src'),*[str(f) for f in install_files],'-framework','Foundation','-o',str(work/'install-test')]
    subprocess.run(install_command,env=env,check=True)
    installation=subprocess.check_output([work/'install-test',a.assets.absolute(),work/'tampered-assets'],text=True)
    cellular_files=[SOURCE/'tests/ShortcutCellularTests.m',SOURCE/'src/CJShortcutSession.m',SOURCE/'src/CJShortcutRouteProbe.m']
    cellular_command=['xcrun','clang','-fobjc-arc','-Wall','-Wextra','-Werror','-I'+str(SOURCE/'src'),*[str(f) for f in cellular_files],'-framework','Foundation','-o',str(work/'cellular-test')]
    subprocess.run(cellular_command,env=env,check=True)
    cellular=subprocess.check_output([work/'cellular-test',work/'cellular-journals'],text=True)
    original49=ROOT/'experiments/ios-jit/launcher-shortcut-import/src/CJShortcutSession.m'
    cellular_original_command=[str(original49) if value==str(SOURCE/'src/CJShortcutSession.m') else
        str(work/'original49-test') if value==str(work/'cellular-test') else value for value in cellular_command]
    subprocess.run(cellular_original_command,env=env,check=True)
    cellular_failure=subprocess.run([work/'original49-test',work/'original49-journals'],capture_output=True,text=True)
    (work/'original49-result.txt').write_text(cellular_failure.stdout+cellular_failure.stderr)
    assert cellular_failure.returncode==1 and 'FAIL cellular route reaches isolation without developer service' in cellular_failure.stderr
    branches=shortcut_checks();connection_controls=url_connection_controls()
    for host in ['livecontainer','']:
        workflow=generator.generate(host)
        questions=workflow['WFWorkflowImportQuestions']
        assert len(questions)==bool(host)
        if host:
            q=questions[0]; row=workflow['WFWorkflowActions'][q['ActionIndex']]
            assert q['Category']=='Parameter' and q['ParameterKey']=='WFTextActionText'
            assert row['WFWorkflowActionIdentifier']=='is.workflow.actions.gettext'
            # Customize the import question only. Keep both explicit typed URL connections.
            route='livecontainer2://livecontainer-launch?bundle-name=Custom.app&container-folder-name=example&open-url=Y2FicmlsbG86Ly9sYXVuY2g%3D'
            row['WFWorkflowActionParameters'][q['ParameterKey']]=route
            assert workflow_controls.execute(workflow)[0]==[('open',route)]
    files += install_files+cellular_files+[SOURCE/'src/CJShortcutInstall.h',SOURCE/'src/CJShortcutSession.h',SOURCE/'src/CJShortcutRouteProbe.h',original49,original49.with_suffix('.h')]
    receipt=dict(status='PASS_HOST_SHORTCUT_CONTROLS',native=native.strip(),installation=installation.strip(),shortcut_branches=len(branches),checks=branches,
                 cellular=cellular.strip(),original49_cellular_order_failure_reproduced=True,
                 rejected_broken_url_connections=connection_controls,original43_missing_callback_failure_reproduced=True,
                 physical_device_tested=False,source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files+[original,Path(__file__),ROOT/'tools/build_shortcut_files49.py',ROOT/'tools/check_shortcut_files49.py']})
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(native.strip());print(installation.strip());print(cellular.strip());print('PASS',len(branches),'generated shortcut branches')

if __name__=='__main__':main()
