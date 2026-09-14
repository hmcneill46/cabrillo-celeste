#!/usr/bin/env python3
import hashlib,json,os,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
SDK=ROOT/'.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422';OUT=ROOT/'.build/ios-jit/sj-budget-content-tests';OUT.mkdir(parents=True,exist_ok=True)
refs=sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
files=[SOURCE/'managed/ContentStore.cs',SOURCE/'tests/ContentStoreTests.cs']
rsp=OUT/'tests.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-target:exe','-out:"'+str(OUT/'ContentStoreTests.dll')+'"']+['-r:"'+str(p)+'"' for p in refs]+['"'+str(p)+'"' for p in files]))
env=dict(os.environ,DOTNET_ROOT=str(SDK),DOTNET_MULTILEVEL_LOOKUP='0')
subprocess.run([str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)],env=env,check=True)
(OUT/'ContentStoreTests.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.28'}}}))
import tempfile
with tempfile.TemporaryDirectory(prefix='case-',dir=OUT) as work:
 r=subprocess.run([str(SDK/'dotnet'),str(OUT/'ContentStoreTests.dll'),work],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(OUT/'run.log').write_text(r.stdout);print(r.stdout[-2500:]);assert r.returncode==0
(OUT/'receipt.json').write_text(json.dumps({'status':'PASS_CONTENT_STORE_TESTS','runtime':'CoreCLR 8.0.28; logic tests only, separate embedded-Mono integration required','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'log_sha256':hashlib.sha256(r.stdout.encode()).hexdigest()},indent=2)+'\n')
