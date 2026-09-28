#!/usr/bin/env python3
"""Independently verify the owned-game IPA, recorded payload audit and fresh symbols."""
import argparse, json, plistlib, zipfile
from pathlib import Path
from compile_owned_game import ROOT,SOURCE,sha
from verify_everest6580 import macho,compiled_protocol,digest,require

def verify(directory):
    r=json.loads((directory/'build-receipt.json').read_text()); ipa=directory/r['ipa']
    require(sha(ipa)==r['ipa_sha256'] and ipa.stat().st_size==r['bytes'],'IPA hash or size changed')
    for n,h in r['source_sha256'].items(): require(sha(ROOT/n)==h,'Changed source: '+n)
    require(r['historical_uuid_restoration'] is False and r['original_executable_copied'] is False and r['game_files_used'] is False,'Invalid build provenance')
    audit=json.loads((directory/'payload-audit.json').read_text())
    require(audit['status']=='PASS_NO_BUNDLED_GAME_ASSEMBLIES' and sha(directory/'payload-audit.json')==r['payload_audit_sha256'],'Missing payload identity audit')
    prefix='Payload/CelesteJITEverest.app/'
    with zipfile.ZipFile(ipa) as z:
        require(len(z.namelist())==len(set(z.namelist())) and z.testzip() is None,'ZIP CRC or duplicate error')
        require(set(z.namelist())=={prefix+n for n in r['app_files']},'Package file set differs')
        forbidden={'celeste.dll','celeste.exe','celeste.content.dll','mmhook_celeste.dll'}
        for n,h in r['app_files'].items():
            path=Path(n)
            require(path.name.lower() not in forbidden and not {'orig','Content','reference','_CodeSignature','..'}.intersection(path.parts),'Forbidden game/reference content: '+n)
            require(path.name!='embedded.mobileprovision' and path.suffix.lower() not in {'.bank','.xnb','.pdb'},'Unexpected private content: '+n)
            require(digest(z.read(prefix+n))==h,'Payload changed: '+n)
        info=json.loads(z.read(prefix+'BuildInfo.json')); settings=plistlib.loads(z.read(prefix+'Info.plist'))
        require(info['game_code_recipe_sha256']==digest(z.read(prefix+'OwnedGameRecipe.json')),'Stale preparation recipe')
        recipe=json.loads(z.read(prefix+'OwnedGameRecipe.json'))
        for n,h in recipe['tools'].items(): require(digest(z.read(prefix+'Managed/'+n))==h,'Changed preparation component: '+n)
        require(info['owned_game_preparation']['bundled_game'] is False and info['private_prepared_game_il'] is False,'Bundled game claim differs')
        require(info['source_sha256']==r['source_sha256'],'Source metadata differs')
        require(settings['CFBundleVersion']==r['build']['build_number'] and settings['CFBundleShortVersionString']==r['build']['version'],'Stale package identity')
        require(settings['CFBundleIdentifier']=='io.github.hmcneill46.celeste.everest.jit.everest','Guest data identity changed')
        exe=z.read(prefix+'CelesteJITEverest'); uuid=macho(exe,True)
        require(compiled_protocol(exe)==info['compiled_protocol'],'JIT protocol differs')
        require(macho((directory/'CelesteJITEverest.app.dSYM/Contents/Resources/DWARF/CelesteJITEverest').read_bytes())==uuid,'dSYM UUID differs')
        require({n for n in audit['assemblies'] if n!='CJITCodeCanary.dll'}=={Path(n).name for n in r['app_files'] if n.startswith('Managed/')},'Assembly audit set differs')
    return dict(status='PASS_OWNED_GAME_PACKAGE',version=r['build']['version'],build_number=r['build']['build_number'],ipa_sha256=sha(ipa),bytes=ipa.stat().st_size,uuid=uuid,
                managed_assemblies=len(audit['assemblies'])-1,bundled_game_assemblies=0,game_assets_bundled=False,physical_device_tested=False,
                public_ipa_ready=r['public_ipa_ready'],distribution_blockers=r['distribution_blockers'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args();print(json.dumps(verify(Path(a.directory)),indent=2))
