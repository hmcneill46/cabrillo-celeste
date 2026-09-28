#!/usr/bin/env python3
"""Build Cabrillo from public dependency receipts and an explicit private FMOD SDK receipt."""
import argparse, datetime, json, os, plistlib, re, shutil, subprocess, zipfile
from pathlib import Path
from compile_owned_game import ROOT, sha
SOURCE = ROOT / 'experiments/ios-jit/launcher-shortcut-tunnel'

DEVELOPER=os.environ.get('DEVELOPER_DIR','/Applications/Xcode-26.6.app/Contents/Developer')
XCODE='Xcode 26.6\nBuild version 17F113'
TARGET='arm64-apple-ios15.0'
APP_NAME='CelesteJITEverest'

def read_json(path): return json.loads(path.read_text())
def write_json(path,value): path.write_text(json.dumps(value,indent=2)+'\n')
def local_path(name):
    path=(ROOT/name).absolute()
    if path.resolve()!=path or ROOT not in path.parents: raise ValueError('Expected an unaliased repository path: '+str(name))
    return path

def validate(args):
    paths=[local_path(n) for n in [args.managed,args.native,args.fmod]]
    managed,native,fmod=map(read_json,paths)
    assert managed['status']=='PASS_PUBLIC_GAME_FREE_MANAGED_BUILD' and not managed['game_files_used'] and not managed['private_capsule_used']
    assert native['status']=='PASS_PUBLIC_NATIVE_DEPENDENCIES' and not native['legacy_read_during_build']
    assert fmod['status']=='PASS_EXPLICIT_FMOD_SDK' and not fmod['redistribution_permission_granted']
    assert fmod['native_receipt_sha256']==sha(paths[1])
    assert managed['nuget_packages']==read_json(ROOT/'release/owned-game-nuget.json')['packages']
    manifest=Path(managed['input_receipt']); inputs=manifest.parent
    assert native['input_manifest_sha256']==managed['input_receipt_sha256']==sha(manifest)
    resources=paths[0].parent/'resources'
    assert managed['resources']=={str(p.relative_to(resources)):sha(p) for p in resources.rglob('*') if p.is_file()}
    selected=list(native['libraries'].values())+list(fmod['libraries'].values())
    assert len(selected)==16
    for row in selected: assert sha(local_path(row['path']))==row['sha256']
    for receipt in [managed,native,fmod]:
        for name,h in receipt['source_sha256'].items(): assert sha(local_path(name))==h,name
    return paths,managed,native,fmod,inputs,resources,selected

def collect_notices(inputs,managed_work,app):
    destination=app/'licenses'; destination.mkdir()
    roots=[(name,inputs/name) for name in ['Everest','runtime','FNA','SDL2','FNA3D','FAudio','Theorafile','lua','SDL2-CS']]
    roots += [('nuget',managed_work/'nuget')]
    records={}
    for label,root in roots:
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.is_symlink() or path.stat().st_size>2*1024*1024: continue
            if not path.name.lower().startswith(('license','licence','copying','copyright','notice','third-party-notice','thirdpartynotice')): continue
            relative=Path(label)/path.relative_to(root); target=destination/relative
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target); records[str(relative)]=sha(target)
    for name,path in [('CABRILLO-LICENSE',ROOT/'LICENSE'),('ZIPFoundation-LICENSE',ROOT/'vendor/ZIPFoundation/LICENSE'),
                      ('Yams-LICENSE',ROOT/'vendor/Yams/LICENSE')]:
        shutil.copyfile(path,destination/name); records[name]=sha(path)
    # Lua's license is in its public header; retain the full upstream text.
    for label,path in [('Lua-lua.h',inputs/'lua/src/lua.h'),('DOTNET-LICENSE.TXT',inputs/'mono-ios-arm64/LICENSE.TXT'),
                       ('DOTNET-THIRD-PARTY-NOTICES.TXT',inputs/'mono-ios-arm64/THIRD-PARTY-NOTICES.TXT')]:
        if path.is_file(): shutil.copyfile(path,destination/label); records[label]=sha(path)
    import xml.etree.ElementTree as ET
    packages=[]
    for spec in sorted((managed_work/'nuget').rglob('*.nuspec')):
        root=ET.parse(spec).getroot(); ns={'n':root.tag.split('}')[0][1:]} if root.tag.startswith('{') else {}
        metadata=root.find('n:metadata',ns) if ns else root.find('metadata')
        if metadata is None: continue
        values={child.tag.rsplit('}',1)[-1]:child.text for child in metadata if child.text and child.tag.rsplit('}',1)[-1] in {'id','version','authors','license','licenseUrl','projectUrl','copyright'}}
        packages.append(values)
    write_json(destination/'nuget-packages.json',packages)
    write_json(destination/'index.json',records)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['managed','native','fmod','work','output']: p.add_argument('--'+name,required=True)
    p.add_argument('--compile-only',action='store_true',help='Compile native code without making an IPA or freezing the lane')
    args=p.parse_args(); paths,managed,native_overlay,fmod,inputs,overlay,selected_libraries=validate(args)
    work=local_path(args.work); output=local_path(args.output)
    assert ROOT/'.build' in work.parents and ROOT/'artifacts' in output.parents and not work.exists() and not output.exists()
    identity=read_json(SOURCE/'BuildIdentity.json'); settings=plistlib.loads((SOURCE/'Info.plist').read_bytes())
    assert settings['CFBundleVersion']==identity['build_number'] and settings['CFBundleShortVersionString']==identity['version']
    assert identity['build_number']=='41' and settings['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.everest'
    lock=read_json(SOURCE/'Dependencies.json')
    for key,path in zip(['managed','native','fmod'],paths):
        assert sha(path)==lock['base_receipts'][key]['sha256'], 'Build 41 must retain the exact build 38 runtime dependencies'
    sources=[Path(__file__),ROOT/'tools/build_shortcut_files.py',ROOT/'tools/check_shortcut_tunnel.py',ROOT/'tools/check_shortcut_ui.py',ROOT/'tools/compile_owned_game.py',ROOT/'tools/verify_owned_game.py',ROOT/'tools/prepare_owned_public.py',SOURCE/'tools/AuditPayload.cs',
             ROOT/'release/current.json',ROOT/'release/owned-game-dependencies.json',ROOT/'release/owned-game-nuget.json',ROOT/'LICENSE',ROOT/'vendor/ZIPFoundation/LICENSE',ROOT/'vendor/Yams/LICENSE',ROOT/'modern-ios/Assets/TouchControls/NOTICE.md']
    sources += [p for folder in [SOURCE/'src',SOURCE/'native',SOURCE/'public-build'] for p in folder.rglob('*') if p.is_file()]
    sources += [SOURCE/'tests'/name for name in ['ShortcutSessionTests.m','ShortcutPreview.swift','ShortcutUITests.swift','LoadingUITests.pbxproj.template','LoadingUITests.xcscheme']]
    sources += [SOURCE/n for n in ['BuildIdentity.json','BuildContract.json','Dependencies.json','Info.plist','RuntimeIdentity.json',
                                 'CompatibilityDownloads.json','RuntimeCompatibleReleases.json','THIRD_PARTY_NOTICES.md']]
    sources += [ROOT/n for n in lock['shared_source_sha256']]
    script=ROOT/'experiments/ios-jit/launcher-catalogue/scripts/celeste-jit-probe.js'; sources.append(script)
    for r in [managed,native_overlay,fmod]: sources += [ROOT/n for n in r['source_sha256']]
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(sources))}
    work.mkdir(parents=True); output.mkdir(parents=True)
    env=dict(os.environ,DEVELOPER_DIR=DEVELOPER,CLANG_MODULE_CACHE_PATH=str(work/'module-cache'),SWIFT_MODULECACHE_PATH=str(work/'module-cache'))
    assert subprocess.check_output(['xcodebuild','-version'],env=env,text=True).strip()==XCODE
    sdk=subprocess.check_output(['xcrun','--sdk','iphoneos','--show-sdk-path'],env=env,text=True).strip()
    sdk_version=subprocess.check_output(['xcrun','--sdk','iphoneos','--show-sdk-version'],env=env,text=True).strip(); assert sdk_version=='26.5'
    release_config=read_json(ROOT/'release/current.json')
    approved=release_config.get('public_ipa_ready') is True and release_config.get('fmod_distribution',{}).get('approved') is True
    if approved and not release_config['fmod_distribution'].get('permission_reference'): raise ValueError('Missing FMOD permission record')
    created=datetime.datetime.now(datetime.timezone.utc).isoformat()
    native=work/'native'; stage=work/'stage'; native.mkdir(); stage.mkdir(); commands=[]; compiled=[]
    def run(command):
        command=list(map(str,command)); commands.append(command)
        with (output/'build.log').open('a') as log:
            log.write(repr(command)+'\n'); log.flush()
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode: raise RuntimeError('Command failed; see '+str(output/'build.log'))
    swift_flags = ["-swift-version", "5", "-O", "-g", "-target", TARGET, "-sdk", sdk,
                   "-module-cache-path", work / "module-cache"]
    zip_sources = sorted((ROOT / "vendor/ZIPFoundation/Sources/ZIPFoundation").glob("*.swift"))
    run(["xcrun", "swiftc", *swift_flags, "-module-name", "ZIPFoundation", "-emit-library", "-static",
         "-emit-module", "-emit-module-path", native / "ZIPFoundation.swiftmodule", "-o", native / "libZIPFoundation.a", *zip_sources])
    compiled.extend(zip_sources)
    yaml = ROOT / "vendor/Yams/Sources/CYaml"
    yaml_objects = []
    for source in sorted((yaml / "src").glob("*.c")):
        obj = native / (source.stem + ".o")
        run(["xcrun", "clang", "-target", TARGET, "-isysroot", sdk, "-DYAML_DECLARE_STATIC", "-O2", "-g",
             "-I" + str(yaml / "include"), "-c", source, "-o", obj])
        yaml_objects.append(obj)
        compiled.append(source)
    run(["xcrun", "libtool", "-static", "-o", native / "libCYaml.a", *yaml_objects])
    swift_sources = sorted((SOURCE / "native").glob("*.swift"))
    run(["xcrun", "swiftc", *swift_flags, "-module-name", "CJLauncher", "-I", native, "-I", yaml / "include",
         "-emit-library", "-static", "-emit-module", "-emit-module-path", native / "CJLauncher.swiftmodule",
         "-emit-objc-header-path", native / "CJLauncher-Swift.h", "-o", native / "libCJLauncher.a", *swift_sources])
    compiled.extend(swift_sources)
    libraries = [ROOT / r["path"] for r in selected_libraries]

    def make_table(name, resolver, paths, pattern, minimum):
        names = set()
        for path in paths:
            symbols = subprocess.check_output(["xcrun", "nm", "-g", "-U", "-j", str(path)], env=env, text=True)
            names.update(line[1:] for line in symbols.splitlines() if re.fullmatch(pattern, line))
        if len(names) < minimum:
            raise RuntimeError("Incomplete symbol table: " + name)
        names = sorted(names)
        source = stage / name
        source.write_text('#include <string.h>\n' + ''.join('extern void ' + n + '(void);\n' for n in names)
            + 'void *' + resolver + '(const char *name) {\n'
            + ''.join('if (!strcmp(name,"' + n + '")) return (void *)&' + n + ';\n' for n in names) + 'return 0;\n}\n')
        return source

    tables = [make_table("SystemNativeTable.c", "CJResolveSystemNative", [p for p in libraries if p.name.startswith("libSystem.")],
                        r"_(SystemNative_|CompressionNative_|AppleCryptoNative_)[A-Za-z0-9_]+", 100),
              make_table("FNAStaticTable.c", "CJResolveFNAStatic", libraries,
                        r"_(FMOD_[A-Za-z0-9_]+|SDL_[A-Za-z0-9_]+|FNA3D_[A-Za-z0-9_]+|FAudio[A-Za-z0-9_]*|F3DAudio[A-Za-z0-9_]*|FACT[A-Za-z0-9_]*|FAPO[A-Za-z0-9_]*|XNA_[A-Za-z0-9_]+|stb_vorbis_[A-Za-z0-9_]+|tf_[A-Za-z0-9_]+|luaL?_[A-Za-z0-9_]+|luaopen_[A-Za-z0-9_]+)", 500)]
    includes = [SOURCE / "src", native, ROOT / "experiments/ios-jit/managed-canary/src"]
    includes += [inputs / "SDL2/include", inputs / "mono-ios-arm64/runtimes/ios-arm64/native/include/mono-2.0"]
    native_sources = sorted(p for p in (SOURCE / "src").iterdir() if p.suffix in {".c", ".m"})
    native_sources += [ROOT / "experiments/ios-jit/managed-canary/src" / n for n in ["CanaryNative.c", "CJNativeResolver.c", "CJMonoThread.c"]]
    native_sources += tables
    objects = []
    for source in native_sources:
        obj = stage / (source.stem + ".o")
        run(["xcrun", "clang", "-target", TARGET, "-isysroot", sdk, "-O2", "-g", "-Wall", "-Wextra", "-Werror",
             "-Wno-deprecated-declarations", *(["-fobjc-arc"] if source.suffix == ".m" else []),
             *(["-std=c11"] if source.suffix == ".c" else []),
             *(["-fno-omit-frame-pointer"] if source.name == "main.m" else []),
             *("-I" + str(p) for p in includes), "-c", source, "-o", obj])
        objects.append(obj)
        compiled.append(source)
    if any(str(p.relative_to(ROOT)) not in source_hashes for p in compiled if p not in tables):
        raise RuntimeError("Compilation consumed an unrecorded source")
    native_receipt=dict(status="PASS_FRESH_NATIVE_COMPILATION",source_sha256=source_hashes,commands=list(commands),
        native_libraries=selected_libraries,compiled_source_count=len(compiled),created_utc=created,
        generated_sources={p.name:sha(p) for p in tables})
    write_json(output/'native-receipt.json',native_receipt)
    if args.compile_only:
        print('PASS_OWNED_GAME_NATIVE_COMPILATION'); return
    for path,name in zip(paths,['managed-receipt.json','native-dependencies.json','fmod-receipt.json']): shutil.copyfile(path,output/name)
    app=stage/'Payload'/(APP_NAME+'.app'); shutil.copytree(overlay,app)
    for name in ['RuntimeIdentity.json','CompatibilityDownloads.json','RuntimeCompatibleReleases.json','THIRD_PARTY_NOTICES.md']:
        shutil.copyfile(SOURCE/name,app/name)
    shutil.copyfile(script,app/'celeste-jit-probe.js')
    shutil.copyfile(ROOT/'modern-ios/Assets/TouchControls/NOTICE.md',app/'TOUCH_ARTWORK_NOTICE.md')
    collect_notices(inputs,paths[0].parent,app)
    shutil.copyfile(paths[2].parent/'FMOD-LICENSE.TXT',app/'licenses/FMOD-LICENSE.TXT')
    assets = stage / "Assets.xcassets"
    icon = assets / "AppIcon.appiconset"
    icon.mkdir(parents=True)
    write_json(assets / "Contents.json", {"info": {"author": "xcode", "version": 1}})
    write_json(icon / "Contents.json", {"images": [{"filename": "AppIcon.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}], "info": {"author": "xcode", "version": 1}})
    run(["xcrun", "swift", ROOT / "experiments/ios-jit/native-probe/scripts/make_icon.swift", icon / "AppIcon.png"])
    run(["xcrun", "actool", assets, "--compile", app, "--platform", "iphoneos", "--minimum-deployment-target", "15.0",
         "--target-device", "iphone", "--target-device", "ipad", "--app-icon", "AppIcon", "--output-partial-info-plist", stage / "asset-info.plist"])
    settings.update(plistlib.loads((stage / "asset-info.plist").read_bytes()))
    (app / "Info.plist").write_bytes(plistlib.dumps(settings, fmt=plistlib.FMT_BINARY))
    info=read_json(SOURCE/'BuildContract.json'); info.pop('provenance')
    canary=app/'CJITCodeCanary-v1.0.0.zip'
    info['mod_download_manifest'][canary.name]=dict(bytes=canary.stat().st_size,sha256=sha(canary),url=None)
    runtime=read_json(SOURCE/'RuntimeIdentity.json'); recipe=read_json(app/'OwnedGameRecipe.json')
    info.update(identity,shortcut_launch=dict(schema=1,network_restore="configured_preset_for_travel",vpn_gate="rppairing_v19_hello",jit_gate="native_checks_after_detach",physical_tested=False),created_utc=created,xcode=XCODE,sdk='iphoneos',sdk_version=sdk_version,target=TARGET,
        bundled_runtime_identity=runtime,bundled_runtime_identity_sha256=sha(SOURCE/'RuntimeIdentity.json'),
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        working_tree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),source_sha256=source_hashes,
        launcher_native_receipt_sha256=sha(output/'native-receipt.json'),managed_build_receipt_sha256=sha(paths[0]),
        game_code_source_id=recipe['source_id'],game_code_recipe_sha256=sha(app/'OwnedGameRecipe.json'),
        game_fixture_sha256=sha(app/'Managed/Cabrillo.Bootstrap.dll'),game_adapter_sha256=sha(app/'Managed/CelesteJITEverest.dll'),
        game_content_manifest_sha256=sha(app/'GameContentManifest.json'),script_template_sha256=sha(app/'celeste-jit-probe.js'),
        compatibility_downloads_sha256=sha(app/'CompatibilityDownloads.json'),runtime_compatible_releases_sha256=sha(app/'RuntimeCompatibleReleases.json'),
        private_prepared_game_il=False,owned_game_preparation=dict(schema=1,cached=True,bundled_game=False,one_time_jit_required=True),
        runtime_pin=dict(runtime_commit=native_overlay['runtime_commit'],version='8.0.28'),
        monomod_pin=dict(commit='dfc30a1506d37fb88a2c2be004f525205f46a24c'),reflection_flags=dict(abi=1),
        ios_support=dict(id='CelesteIOS',version='1.0.0',abi=1,required=True,sha256=sha(app/'Managed/CelesteIOS.dll')),
        platforms=dict(minimum_ios='15.0',jit_routes=['livecontainer2','stikdebug','trollstore','manual'],local_memory_below_ios26=True,default_callback_fps=60,optional_callback_fps=120),
        loading=dict(abi=1,scheduler='main CADisplayLink',ready_gate='first_draw_and_post_present_readback',passive_game_startup=True,non_preemptible_steps=True),
        precision_repair=dict(schema=1,original_float_sites=10,lava_float_setters=2,lava_double_constants=1,preserved_double_sites=10,changed_method_bodies=4),
        save_transfers=dict(schema=1,unchanged_file_contents=True,vanilla_slots=3,staged_profile_swap=True,retained_rollback=True,main_only_mod_choice=True),
        profile_backups=dict(schema=1,exact_restore=True,retained_rollback=True,fresh_process_required=True,arbitrary_save_slots=True,mod_archives_included=False),
        public_dependencies=dict(input_receipt_sha256=managed['input_receipt_sha256'],native_receipt_sha256=sha(paths[1]),managed_receipt_sha256=sha(paths[0]),private_capsule_used=False),
        fmod=dict(version=fmod['version'],sdk_receipt_sha256=sha(paths[2]),redistribution_permission_granted=approved,permission_reference=release_config.get('fmod_distribution',{}).get('permission_reference')))
    write_json(app/'BuildInfo.json',info)
    sdk_arch=read_json(inputs/'receipt.json')['sdk_arch']; dotnet=inputs/('sdk8.0-osx-'+sdk_arch)
    references=sorted((dotnet/'packs/Microsoft.NETCore.App.Ref/8.0.28/ref/net8.0').glob('*.dll'))
    audit_dir=work/'audit'; audit_dir.mkdir(); auditor=audit_dir/'AuditPayload.dll'
    response=audit_dir/'compile.rsp'
    response.write_text('\n'.join(['-nologo','-nostdlib+','-target:exe','-out:"'+str(auditor)+'"']+
        ['-r:"'+str(f)+'"' for f in references+[app/'Managed/Mono.Cecil.dll']]+['"'+str(SOURCE/'tools/AuditPayload.cs')+'"'])+'\n')
    run([dotnet/'dotnet','exec',dotnet/'sdk/8.0.422/Roslyn/bincore/csc.dll','@'+str(response)])
    shutil.copyfile(app/'Managed/Mono.Cecil.dll',audit_dir/'Mono.Cecil.dll')
    write_json(auditor.with_suffix('.runtimeconfig.json'),dict(runtimeOptions=dict(tfm='net8.0',framework=dict(name='Microsoft.NETCore.App',version='8.0.28'))))
    run([dotnet/'dotnet',auditor,app,output/'payload-audit.json'])
    executable = app / APP_NAME
    frameworks = ["UIKit", "Foundation", "UniformTypeIdentifiers", "QuartzCore", "AVFoundation", "AudioToolbox",
                  "CoreBluetooth", "CoreGraphics", "CoreHaptics", "CoreMotion", "CoreVideo", "GameController", "Metal",
                  "OpenGLES", "Security", "CoreFoundation"]
    run(["xcrun", "swiftc", "-target", TARGET, "-sdk", sdk, "-Xlinker", "-no_adhoc_codesign", *objects,
         native / "libCJLauncher.a", native / "libZIPFoundation.a", native / "libCYaml.a", *libraries,
         *(arg for framework in frameworks for arg in ["-framework", framework]), "-lc++", "-liconv", "-lz", "-o", executable])
    run(["xcrun", "dsymutil", executable, "-o", output / (APP_NAME + ".app.dSYM")])
    run(["xcrun", "strip", "-S", executable])
    for name,digest in source_hashes.items():
        if sha(ROOT/name)!=digest: raise RuntimeError('Source changed during build: '+name)
    validate(args)
    from verify_everest6580 import macho,compiled_protocol
    binary=executable.read_bytes(); uuid=macho(binary,True)
    assert compiled_protocol(binary)==info['compiled_protocol']
    assert macho((output/(APP_NAME+'.app.dSYM')/'Contents/Resources/DWARF'/APP_NAME).read_bytes())==uuid
    assert not any(p.name.lower() in {'celeste.dll','celeste.exe','celeste.content.dll','mmhook_celeste.dll'} for p in app.rglob('*'))
    ipa=output/f"Cabrillo-{identity['version']}-build-{identity['build_number']}-unsigned.ipa"
    with zipfile.ZipFile(ipa,'x',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app.rglob('*')):
            if path.is_file(): archive.write(path,str(path.relative_to(stage)))
    receipt=dict(status='BUILD_COMPLETE_AWAITING_PACKAGE_VERIFICATION',build=identity,actual_created_utc=created,
        ipa=ipa.name,ipa_sha256=sha(ipa),bytes=ipa.stat().st_size,executable_sha256=sha(executable),source_sha256=source_hashes,
        app_files={str(p.relative_to(app)):sha(p) for p in sorted(app.rglob('*')) if p.is_file()},
        native_receipt_sha256=sha(output/'native-receipt.json'),managed_receipt_sha256=sha(paths[0]),commands=commands,
        payload_audit_sha256=sha(output/'payload-audit.json'),
        historical_uuid_restoration=False,original_executable_copied=False,game_files_used=False,device_tested=False,
        public_ipa_ready=approved,distribution_blockers=[] if approved else ['fmod_redistribution'])
    write_json(output/'build-receipt.json',receipt)
    from verify_owned_game import verify
    verified=verify(output); write_json(output/'verification.json',verified); print(json.dumps(verified,indent=2))

if __name__=='__main__': main()
