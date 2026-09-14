#!/usr/bin/env python3
"""Build our small independent Everest ZIP for import/enable/disable testing."""
import hashlib,json,os,subprocess,zipfile
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-reflection-example';O.mkdir(parents=True,exist_ok=True)
SDK=R/'.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422';refs=sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
rsp=O/'compile.rsp';rsp.write_text('\n'.join(['-nologo','-nostdlib+','-optimize+','-deterministic+','-target:library','-out:"'+str(O/'LauncherExample.dll')+'"']+['-r:"'+str(p)+'"' for p in refs+[R/'.build/ios-jit/launcher-reflection-managed/Celeste.dll']]+['"'+str(S/'example-mod/LauncherExample.cs')+'"'])+'\n')
env=dict(os.environ,DOTNET_ROOT=str(SDK),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
subprocess.run([str(SDK/'dotnet'),'exec',str(SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)],env=env,check=True)
zip=O/'CJITLauncherExample-v1.0.0.zip'
with zipfile.ZipFile(zip,'w',zipfile.ZIP_DEFLATED) as z:
 for n,data in [('everest.yaml',(S/'example-mod/everest.yaml').read_bytes()),('LauncherExample.dll',(O/'LauncherExample.dll').read_bytes())]:
  item=zipfile.ZipInfo(n,(2026,9,12,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;z.writestr(item,data)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'receipt.json').write_text(json.dumps(dict(status='PASS_EXAMPLE_MOD_BUILD',zip_sha256=sha(zip),zip_bytes=zip.stat().st_size,source_sha256={str(p.relative_to(R)):sha(p) for p in (S/'example-mod').iterdir()},build_script_sha256=sha(Path(__file__))),indent=2)+'\n');print('PASS_EXAMPLE_MOD_BUILD',zip.stat().st_size)
