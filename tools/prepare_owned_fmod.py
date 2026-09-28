#!/usr/bin/env python3
"""Stage explicit user-supplied FMOD 1.10.09 SDK libraries for a private iOS build."""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path
from compile_owned_game import ROOT, SOURCE, sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk',required=True); p.add_argument('--native',required=True); p.add_argument('--work',required=True)
    a=p.parse_args(); sdk=Path(a.sdk).resolve(); work=(ROOT/a.work).resolve()
    if ROOT/'.build' not in work.parents or work.exists(): raise ValueError('Choose a fresh .build directory')
    native_path=(ROOT/a.native).resolve(); native=json.loads(native_path.read_text())
    assert native['status']=='PASS_PUBLIC_NATIVE_DEPENDENCIES'
    row=native['libraries']['libtheorafile.a']; theory=ROOT/row['path']; assert sha(theory)==row['sha256']
    policy=SOURCE/'public-build/fmod-inputs.json'; lock=json.loads(policy.read_text())
    inputs={kind:sdk/row['path'] for kind,row in lock['deviceArchives'].items()}
    for kind,path in inputs.items():
        assert path.is_file() and not path.is_symlink() and sha(path)==lock['deviceArchives'][kind]['sha256'], kind
    assert '1.10.09' in (sdk/'doc/revision.txt').read_text()
    work.mkdir(parents=True); env=dict(os.environ,DEVELOPER_DIR=os.environ.get('DEVELOPER_DIR','/Applications/Xcode-26.6.app/Contents/Developer'),ZERO_AR_DATE='1')
    commands=[]
    def run(cmd,cwd=None):
        cmd=list(map(str,cmd)); commands.append(cmd)
        return subprocess.check_output(cmd,cwd=cwd or work,env=env,text=True,stderr=subprocess.STDOUT)
    low=work/'libfmod-arm64.a'; studio=work/'libfmodstudio_iphoneos-arm64.a'
    for kind,dest in [('lowLevel',low),('studio',studio)]: run(['xcrun','lipo',inputs[kind],'-thin','arm64','-output',dest])
    def symbols(path): return {line for line in run(['xcrun','nm','-gjU',path]).splitlines() if line.startswith('_') and not line.endswith(':')}
    names=SOURCE/'public-build/fmod-localized-symbols.txt'
    expected={s for s in names.read_text().splitlines() if s and not s.startswith('#')}
    assert symbols(low)&symbols(theory)==expected, 'FMOD/Theorafile duplicate symbols changed'
    (work/'symbols.txt').write_text('\n'.join(sorted(expected))+'\n')
    objects=work/'objects'; objects.mkdir(); run(['xcrun','ar','-x',low],objects)
    members=[f for f in objects.iterdir() if f.is_file() and not f.name.startswith('__.SYMDEF')]
    assert len(members)==1, 'Expected the reviewed single-object FMOD archive'
    run(['xcrun','nmedit','-R',work/'symbols.txt','-o',work/'FMOD-localized.o',members[0]])
    localized=work/'libfmod_iphoneos-localized.a'
    run(['xcrun','ar','rcs',localized,work/'FMOD-localized.o'])
    assert not symbols(localized)&symbols(theory)
    assert {'_FMOD_System_Create','_FMOD_System_GetVersion','_FMOD_System_Init','_FMOD_System_Release'}<=symbols(localized)
    shutil.copyfile(sdk/'doc/LICENSE.TXT',work/'FMOD-LICENSE.TXT')
    result=dict(schema=1,status='PASS_EXPLICIT_FMOD_SDK',version=lock['version'],build=lock['build'],
        sdk_input_sha256={k:sha(v) for k,v in inputs.items()},
        libraries={v.name:dict(path=str(v.relative_to(ROOT)),sha256=sha(v)) for v in [localized,studio]},
        source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [Path(__file__),policy,names]},
        native_receipt_sha256=sha(native_path),license_sha256=sha(work/'FMOD-LICENSE.TXT'),commands=commands,
        proprietary_dependency=True,redistribution_permission_granted=False,game_files_used=False)
    (work/'receipt.json').write_text(json.dumps(result,indent=2)+'\n'); print(result['status'])
if __name__=='__main__': main()
