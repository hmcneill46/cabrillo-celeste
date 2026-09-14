#!/usr/bin/env python3
"""Build isolated net8.0 FNA IL and the external graphics fixture; no Apple bindings."""
import argparse, datetime, hashlib, json, os, shutil, subprocess
from pathlib import Path

SOURCE=Path(__file__).resolve().parent
ROOT=SOURCE.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-id',default='graphics-canary-20260911-11')
    parser.add_argument('--fixture-only',action='store_true')
    a=parser.parse_args()
    stage=ROOT/'.build/ios-jit/graphics-managed';stage.mkdir(parents=True,exist_ok=True)
    foundation=ROOT/'.build/ios-jit/game-foundation'
    sdk=ROOT/'.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'
    refs=sorted((sdk/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    assert len(refs)>100
    env=dict(os.environ,DOTNET_ROOT=str(sdk),DOTNET_CLI_HOME=str(stage/'cli-home'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
    commands=[]
    def compile(name,out,files,libraries=(),resources=()):
        args=['-nologo','-noconfig','-nostdlib+','-unsafe+','-nullable:disable','-optimize+','-deterministic+','-target:library','-define:NETSTANDARD2_0','-out:"'+str(out)+'"']
        args += ['-r:"'+str(f)+'"' for f in [*refs,*libraries]]
        args += ['-resource:"'+str(p)+'",'+n for p,n in resources]
        args += ['"'+str(f)+'"' for f in files]
        rsp=stage/(name+'.rsp');rsp.write_text('\n'.join(args)+'\n')
        command=[str(sdk/'dotnet'),'exec',str(sdk/'sdk/8.0.422/Roslyn/bincore/csc.dll'),'@'+str(rsp)]
        r=subprocess.run(command,cwd=stage,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (stage/(name+'.log')).write_text(r.stdout);commands.append(command)
        if r.returncode: raise RuntimeError(r.stdout)
    if not a.fixture_only:
        work=stage/'fna-source'
        if work.exists():shutil.rmtree(work)
        shutil.copytree(foundation/'fna/src',work)
        p=work/'Game.cs';s=p.read_text();needle='public class Game : IDisposable';assert s.count(needle)==1
        p.write_text(s.replace(needle,'public partial class Game : IDisposable'))
        files=sorted(p for p in work.rglob('*.cs') if p.relative_to(work).as_posix() not in ('Graphics/FNA3D.cs','FrameworkDispatcher.cs'))
        files += [foundation/'managed'/n for n in ('SDL2.cs','FNA3D.cs','FAudio.cs','Theorafile.cs','FrameworkDispatcher.cs')]
        files += [ROOT/'modern-ios/FNA.iOS/StableTouchSlotPolicy.cs',SOURCE/'managed/ExternalGameLoop.cs']
        resources=[(p,'Microsoft.Xna.Framework.Graphics.Effect.Resources.'+p.name) for p in sorted((work/'Graphics/Effect').rglob('*.fxb'))]
        assert len(resources)>3
        compile('fna',stage/'FNA.dll',files,resources=resources)
        receipt=dict(schema=1,target='net8.0 untrimmed IL',fna_revision='d52b4ce61e4086b785c51a96d331dbf106975a58',
            native_manifest_sha256=sha(foundation/'native-manifest.json'),fna_sha256=sha(stage/'FNA.dll'),
            source_sha256={str(f.relative_to(ROOT)):sha(f) for f in files},resources_sha256={n:sha(p) for p,n in resources},
            apple_bindings=False,interpreter=False,source_patch='Game partial modifier plus explicit external-loop lifecycle',commands=commands)
        (stage/'fna-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    out=ROOT/'artifacts/ios-jit'/a.build_id;out.mkdir(parents=True,exist_ok=True)
    if (out/'delivery-receipt.json').exists():raise RuntimeError('Delivered fixture is immutable; choose a new version.')
    deps=ROOT/'.build/ios-jit/hook-runtime'
    dependency=json.loads((deps/'dependencies-receipt.json').read_text())
    libraries=[deps/'managed-libraries'/n for n in dependency['assemblies_sha256']]
    assert all(sha(p)==dependency['assemblies_sha256'][p.name] for p in libraries)
    fixture=out/'GraphicsCanary-v0.4.1.dll'
    compile('graphics',fixture,[SOURCE/'managed/GraphicsCanary.cs'],[stage/'FNA.dll',*libraries])
    ipa=out/'CelesteJITGraphics-unsigned.ipa'
    receipt=dict(schema=1,fixture_sha256=sha(fixture),fixture_bytes=fixture.stat().st_size,
        source_sha256=sha(SOURCE/'managed/GraphicsCanary.cs'),fna_sha256=sha(stage/'FNA.dll'),
        dependencies_sha256=dependency['assemblies_sha256'],target='net8.0 untrimmed IL',
        compiled_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        compiled_after_ipa=ipa.exists() and fixture.stat().st_mtime_ns>ipa.stat().st_mtime_ns,
        ipa_sha256=sha(ipa) if ipa.exists() else None,device_tested=False)
    (out/'fixture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(fna_sha256=sha(stage/'FNA.dll'),fixture=fixture.name,bytes=fixture.stat().st_size)))

if __name__=='__main__': main()
