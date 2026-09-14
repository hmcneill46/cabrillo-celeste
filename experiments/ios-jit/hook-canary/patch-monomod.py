#!/usr/bin/env python3
"""Apply the narrow, pinned MonoMod hosting corrections to the isolated clone."""
from pathlib import Path
import hashlib,json,subprocess

source=Path(__file__).resolve().parent;root=source.parents[2]
base=root/'.build/ios-jit/hook-runtime';repo=base/'MonoMod'
pin=json.loads((source/'dependencies-pin.json').read_text())
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==pin['commit']
changes={}
def change(name, transform):
    pristine=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+name])
    patched=transform(pristine.decode('utf-8-sig')).encode()
    path=repo/name
    assert path.read_bytes() in (pristine,patched), 'Unrecognized edits: '+name
    path.write_bytes(patched)
    changes[name]={'original_sha256':hashlib.sha256(pristine).hexdigest(),'patched_sha256':hashlib.sha256(patched).hexdigest()}
def replace(text, before, after, count=1):
    assert text.count(before)==count,(before,text.count(before))
    return text.replace(before,after)

change('src/MonoMod.Core/Platforms/PlatformTriple.cs',lambda t:replace(t,'if (lazyCurrent is null)\n                    ThrowTripleAlreadyExists();','if (lazyCurrent is not null)\n                    ThrowTripleAlreadyExists();') .replace('if (lazyCurrent is null)\n                ThrowTripleAlreadyExists();','if (lazyCurrent is not null)\n                ThrowTripleAlreadyExists();'))
change('src/MonoMod.Core/Platforms/Runtimes/MonoRuntime.cs',lambda t:replace(t,'typeof(DynamicMethod).GetField("mhandle", BindingFlags.NonPublic | BindingFlags.Instance)!;',
    'typeof(DynamicMethod).GetField("_mhandle", BindingFlags.NonPublic | BindingFlags.Instance) ??\n            typeof(DynamicMethod).GetField("mhandle", BindingFlags.NonPublic | BindingFlags.Instance)!;'))
change('src/MonoMod.Utils/PlatformDetection.cs',lambda t:replace(t,'            var os = OSKind.Unknown;\n            var arch = ArchitectureKind.Unknown;',
    '''#if NET5_0_OR_GREATER
            // Modern Apple runtime packs expose the actual process OS/arch.
            // uname reports Darwin for both products and an iPhone model as
            // its machine name; neither identifies an ARM64 iOS process.
            if (OperatingSystem.IsIOS())
                return (OSKind.IOS, RuntimeInformation.ProcessArchitecture == System.Runtime.InteropServices.Architecture.Arm64 ? ArchitectureKind.Arm64 : ArchitectureKind.Unknown);
            if (OperatingSystem.IsMacOS())
                return (OSKind.OSX, RuntimeInformation.ProcessArchitecture == System.Runtime.InteropServices.Architecture.X64 ? ArchitectureKind.x86_64 : ArchitectureKind.Arm64);
#endif
            var os = OSKind.Unknown;
            var arch = ArchitectureKind.Unknown;'''))
for suffix in ('props','targets'):
    change('src/MonoMod.Core/Directory.Build.'+suffix,lambda t:replace(t,'/Platforms/Architectures/NativeHelpers.'+suffix+'" />',
        '/Platforms/Architectures/NativeHelpers.'+suffix+'" Condition="\'$(CJAppleJitCanary)\' != \'true\'" />'))
change('tools/Common.props',lambda t:replace(t,'    <BackportsTargetFrameworks>',
    '    <TargetFrameworks Condition="\'$(CJAppleJitCanary)\' == \'true\'">net8.0</TargetFrameworks>\n    <BackportsTargetFrameworks>'))
new='src/MonoMod.Core/Platforms/Systems/AppleJitSystem.cs'
data=(source/'monomod/AppleJitSystem.cs').read_bytes();(repo/new).write_bytes(data)
changes[new]={'added':True,'patched_sha256':hashlib.sha256(data).hexdigest()}
patch=subprocess.check_output(['git','-C',str(repo),'diff','--no-ext-diff','--binary','--',*changes])
(source/'monomod-hosting.patch').write_bytes(patch)
receipt={'repository':pin['repository'],'commit':pin['commit'],'iced_commit':pin['iced_commit'],'files':changes,'new_source':str((source/'monomod/AppleJitSystem.cs').relative_to(root)),'patch_sha256':hashlib.sha256(patch).hexdigest()}
(base/'monomod-patch-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('PINNED_MONOMOD_HOSTING_PATCH_READY',len(changes))
