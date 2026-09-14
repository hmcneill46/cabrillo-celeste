#!/usr/bin/env python3
"""Derive private, untrimmed net8 Celeste IL from the owner's locked input."""
import argparse, datetime, importlib.util, hashlib, json, os, re, shutil, subprocess, urllib.request, zipfile, tarfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
ROOT=SOURCE.parents[2]
STAGE=ROOT/'.build/ios-jit/celeste-game'
MANAGED=ROOT/'.build/ios-jit/celeste-managed'
SDK=ROOT/'.build/ios-jit/managed-runtime/dotnet-sdk-8.0.422'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(p,old,new,count=1):
    s=p.read_text(); assert s.count(old)==count,(p,old,s.count(old));p.write_text(s.replace(old,new))
def body(p,signature,new):
    s=p.read_text(); assert s.count(signature)==1,(p,signature)
    start=s.index('{',s.index(signature));depth=1;end=start+1
    while depth:
        if s[end]=='{':depth+=1
        elif s[end]=='}':depth-=1
        end+=1
    p.write_text(s[:start]+'{\n'+new+'\n\t}'+s[end:])
def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--build-id',default='celeste-canary-20260911-12')
    a.add_argument('--game-root',type=Path,default=Path('/Users/harrymcneill/Projects/Celeste Required Files/Celeste Untouched.app'))
    a=a.parse_args();STAGE.mkdir(parents=True,exist_ok=True);MANAGED.mkdir(parents=True,exist_ok=True)
    output=ROOT/'artifacts/ios-jit'/a.build_id;output.mkdir(parents=True,exist_ok=True)
    assert not (output/'delivery-receipt.json').exists(),'Delivered kit is immutable'
    env=dict(os.environ,DOTNET_ROOT=str(SDK),DOTNET_ROLL_FORWARD='Major',DOTNET_CLI_HOME=str(STAGE/'cli-home'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_MULTILEVEL_LOOKUP='0')
    commands=[]
    def run(cmd,name,cwd=STAGE):
        commands.append(list(map(str,cmd)))
        r=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (STAGE/(name+'.log')).write_text(r.stdout)
        if r.returncode:raise RuntimeError(r.stdout[-12000:])
    run([ROOT/'scripts/validate-celeste-input.sh','--game-root',a.game_root,'--output',STAGE/'input-manifest.json'],'input-validation',ROOT)
    inputs=json.loads((STAGE/'input-manifest.json').read_text());assert inputs['normalizationAdapter']=='none'
    resources=a.game_root/'Contents/Resources'
    lock=json.loads((ROOT/'managed/celeste-generation.lock.json').read_text());tool=lock['generationTool']
    gamepin=json.loads((SOURCE/'game-generation-pin.json').read_text())
    rt=gamepin['decompilerRuntime'];archive=STAGE/'dotnet-runtime-6.0.36-osx-x64.tar.gz'
    if not archive.exists():urllib.request.urlretrieve(rt['url'],archive)
    assert hashlib.sha512(archive.read_bytes()).hexdigest()==rt['hash']
    rtroot=STAGE/'runtime6';rtroot.mkdir(exist_ok=True)
    if not (rtroot/'dotnet').exists():
        with tarfile.open(archive) as t:t.extractall(rtroot,filter='data')
    package=STAGE/'ilspycmd.nupkg'
    if not package.exists():urllib.request.urlretrieve('https://api.nuget.org/v3-flatcontainer/ilspycmd/'+tool['version']+'/ilspycmd.'+tool['version']+'.nupkg',package)
    assert sha(package)==tool['packageSha256']
    decompiler=STAGE/'decompiler';decompiler.mkdir(exist_ok=True)
    with zipfile.ZipFile(package) as z:
        for n in z.namelist():
            if n.startswith('tools/net6.0/any/') and not n.endswith('/'):
                target=decompiler/n.removeprefix('tools/net6.0/any/');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
    reference=STAGE/'input';reference.mkdir(exist_ok=True)
    for name in ['Celeste.exe','FNA.dll','Celeste.Content.dll']:shutil.copy2(resources/name,reference/name)
    original=STAGE/'decompiled-net6'
    if not original.exists():run([rtroot/'dotnet','exec',decompiler/'ilspycmd.dll','-p','--nested-directories','-lv','CSharp10_0','-o',original,'-r',reference,reference/'Celeste.exe'],'decompile')
    run(['python3',ROOT/'scripts/celeste-managed.py','tree-manifest','--root',original,'--kind','decompiled-source','--placeholder','DECOMPILED_ROOT','--output',STAGE/'decompiled-manifest.json'],'source-validate')
    manifest=json.loads((STAGE/'decompiled-manifest.json').read_text());expected=gamepin['decompiledSource']
    assert all(manifest[k]==v for k,v in expected.items()),{k:manifest[k] for k in expected}
    work=STAGE/'generated'
    if work.exists():shutil.rmtree(work)
    shutil.copytree(original,work)
    patches=['patches/crash-fixes.patch','managed/patches/game/0001-modern-library-boundary-and-bcl.patch']
    for i,p in enumerate(patches):run(['patch','--batch','--fuzz=0','-p1','-i',ROOT/p],'patch-'+str(i),work)
    replace(work/'Monocle/SaveLoad.cs','modern tvOS target','modern JIT target',2)
    replace(work/'Celeste/Celeste.cs','public class Celeste : Engine','public partial class Celeste : Engine')
    replace(work/'Celeste/Audio.cs','public static class Audio','public static partial class Audio')
    replace(work/'Monocle/Engine.cs','public static string ContentDirectory => Path.Combine(AssemblyDirectory, Instance.Content.RootDirectory);','public static string ContentDirectory => CelesteJIT.Game.Entry.ContentRoot;')
    replace(work/'Monocle/Engine.cs','GCSettings.LatencyMode = GCLatencyMode.SustainedLowLatency;', 'try { GCSettings.LatencyMode = GCLatencyMode.SustainedLowLatency; } catch (PlatformNotSupportedException) { CelesteJIT.Game.Entry.Mark("game_gc_policy", "Mono default collector policy; latency override unavailable"); }')
    body(work/'Celeste/UserIO.cs','private static string GetSavePath(string dir)','\t\treturn Path.Combine(CelesteJIT.Game.Entry.SaveRoot, dir);')
    body(work/'Monocle/ErrorLog.cs','private static string GetLogPath()','\t\treturn Path.Combine(CelesteJIT.Game.Entry.SaveRoot, "errorLog.txt");')
    body(work/'Monocle/ErrorLog.cs','public static void Open()','\t\tCelesteJIT.Game.Entry.Mark("game_error_log", File.Exists(Filename) ? File.ReadAllText(Filename) : "No error log");')
    # The launcher, not desktop Process.Start, owns application lifetime.
    p=work/'Celeste/Celeste.cs'
    if 'private static void CallProcess(' in p.read_text():
        sig=re.search(r'private static void CallProcess\([^\n]+',p.read_text()).group()
        body(p,sig,'\t\tthrow new PlatformNotSupportedException("Desktop subprocesses are unavailable in the JIT game canary.");')
    body(work/'Celeste/Settings.cs','public void ApplyScreen()', '\t\tEngine.ViewPadding = 0;\n\t\tif (CelesteJIT.Game.Entry.IsPhone) Engine.SetFullscreen();\n\t\telse Engine.SetWindowed(960, 540);')
    for name in ['GameLoader.cs','OverworldLoader.cs']:
        p=work/'Celeste'/name;s=p.read_text();s=re.sub(r'^\s*activeThread.Priority = ThreadPriority.\w+;','',s,flags=re.M);p.write_text(s)
    shutil.copy2(SOURCE/'managed/RunThread.cs',work/'Celeste/RunThread.cs')
    audio=work/'Celeste/Audio.cs'
    replace(audio,'\t[DllImport("fmod_SDL", CallingConvention = CallingConvention.Cdecl)]\n\tprivate static extern void FMOD_SDL_Register(IntPtr system);\n','')
    replace(audio,'\t\tif (SDL.SDL_GetPlatform().Equals("Linux"))\n\t\t{\n\t\t\tFMOD_SDL_Register(system.getRaw());\n\t\t}\n','')
    replace(audio,'\t\tready = true;','\t\tready = true;\n\t\tsystem.getVersion(out uint runtimeVersion);\n\t\tCelesteJIT.Game.Entry.Mark("game_audio_ready", "FMOD version=" + runtimeVersion.ToString("x") + "; ready=true");\n\t\tCJITApplySuspended();')
    replace(audio,'\t\t\tbank.loadSampleData();','\t\t\tCheckFmod(bank.loadSampleData());\n\t\t\tCelesteJIT.Game.Entry.Mark("game_audio_bank", name);')
    replace(audio,'\t\t\tsystem = null;','\t\t\tsystem = null;\n\t\t\tready = false;')
    dsp=work/'FMOD/DSP.cs'
    body(dsp,'public RESULT getCPUUsage(out uint exclusive, out uint inclusive)','\t\texclusive = inclusive = 0;\n\t\treturn RESULT.ERR_UNSUPPORTED;')
    s=dsp.read_text();s,n=re.subn(r'\n\t\[DllImport\("fmod"[^\n]*\)\]\n\tpublic static extern RESULT FMOD_DSP_GetCPUUsage\([^;]+;\n','\n',s);assert n==1;dsp.write_text(s)
    imports=0
    for p in work.rglob('*.cs'):
        s=p.read_text();s,n=re.subn(r'\[DllImport\("(?:fmod|fmodstudio)"(?:, CallingConvention = CallingConvention.Cdecl)?\)\]', '[DllImport("__Internal", CallingConvention = CallingConvention.Cdecl, ExactSpelling = true)]',s)
        if n:p.write_text(s);imports+=n
    assert imports==488,imports
    spec=importlib.util.spec_from_file_location('touch',SOURCE/'touch-derive.py');touch=importlib.util.module_from_spec(spec);spec.loader.exec_module(touch);touch.apply(work,replace)
    run(['python3',ROOT/'scripts/generate-ios-touch-assets.py','--source-dir',ROOT/'modern-ios/Assets/TouchControls/Source','--output-dir',STAGE/'touch-assets'],'touch-assets')
    # Reuse the exact physically accepted FNA IL and callback contract.
    accepted=ROOT/'.build/ios-jit/graphics-managed'
    fna=json.loads((accepted/'fna-receipt.json').read_text());assert sha(accepted/'FNA.dll')==fna['fna_sha256']
    for n in ['FNA.dll','fna-receipt.json']:shutil.copy2(accepted/n,MANAGED/n)
    refs=sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    deps=ROOT/'.build/ios-jit/hook-runtime';dependency=json.loads((deps/'dependencies-receipt.json').read_text())
    libraries=[MANAGED/'FNA.dll']+[deps/'managed-libraries'/n for n in dependency['assemblies_sha256']]
    assert all(sha(deps/'managed-libraries'/n)==v for n,v in dependency['assemblies_sha256'].items())
    sources=sorted(work.rglob('*.cs'))+[SOURCE/'managed'/n for n in ['GameEntry.cs','GamePlatform.cs','TouchPort.cs','GlobalUsings.cs']]+[ROOT/'modern-ios/CelesteIOSFoundation'/n for n in ['PlatformPolicies.cs','TouchControlsPolicy.cs']]
    dll=MANAGED/'Celeste.dll'
    args=['-nologo','-noconfig','-nostdlib+','-unsafe+','-nullable:disable','-optimize+','-deterministic+','-target:library','-out:"'+str(dll)+'"']
    args+=['-r:"'+str(p)+'"' for p in refs+libraries]+['"'+str(p)+'"' for p in sources]
    args += ['-resource:"'+str(p)+'",Celeste.IOSTouchControls.'+p.name for p in sorted((STAGE/'touch-assets').glob('*.a8'))]
    rsp=STAGE/'celeste.rsp';rsp.write_text('\n'.join(args)+'\n')
    run([SDK/'dotnet','exec',SDK/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(rsp)],'compile')
    fixture=output/'CelesteJITGame-v0.5.0.dll';shutil.copy2(dll,fixture)
    receipt=dict(schema=1,target='net8.0 untrimmed IL; Celeste 1.4.0.0',fixture_sha256=sha(fixture),fixture_bytes=fixture.stat().st_size,
        original_input=inputs,decompiler_package_sha256=sha(package),decompiled_logical_sha256=manifest['logicalSha256'],
        fna_sha256=fna['fna_sha256'],patch_sha256={p:sha(ROOT/p) for p in patches},fmod_static_imports=imports,
        build_source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),*sources]},
        compiled_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),commands=commands,device_tested=False)
    (output/'fixture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');shutil.copy2(output/'fixture-receipt.json',MANAGED/'game-receipt.json')
    print(json.dumps(dict(fixture=str(fixture),bytes=fixture.stat().st_size,sha256=sha(fixture))))
if __name__=='__main__':main()
