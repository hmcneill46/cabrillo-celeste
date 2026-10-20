#!/usr/bin/env python3
"""Audit the actual59 IPA's helper isolation, identity, unsigned code and notices."""
import argparse
import json
from pathlib import Path
import plistlib
import zipfile

from build_stikjit57 import COMMIT, ARCHIVE_SHA256, lock_value, macho_details_data
from verify_owned_game import verify as verify_owned

COMPONENT_FILES = {'Frameworks/StikJIT.framework/' + name for name in ['StikJIT', 'Info.plist', 'universal.js', 'legacy.js']}
COMPONENT_FILES |= {'PlugIns/CabrilloJITHelper.appex/' + name for name in ['CabrilloJITHelper', 'Info.plist']}


def verify_combined_notice(notice, info):
    """Reject obsolete runtime/permission text or missing merged attributions."""
    runtime = info['bundled_runtime_identity']
    required = [
        f'# Cabrillo {info["version"]} / build{info["build_number"]} notices',
        'Everest stable ' + runtime['builtins']['Everest'], runtime['everestSourceCommit'],
        'FMOD runtime distribution permission',
        'Developers must obtain their own FMOD SDK from https://www.fmod.com',
        'SDK components are not redistributed.', 'licenses/FMOD-LICENSE.TXT',
        'Morro', 'licenses/MORRO-LICENSE', 'StikJIT', 'MPL-2.0',
        info['integrated_jit']['upstream_commit'], 'licenses/StikJIT/UPSTREAM.json',
        'prebuilt idevice FFI static library',
    ]
    if any(text not in notice for text in required):
        raise ValueError('Combined app notice has stale identity or missing runtime/SDK/attribution disclosure')


def verify_game_input_contract(info, recipe):
    """The native launcher's retained-input lookup must match the bootstrap."""
    if (info.get('game_code_legacy_source_id') != recipe['legacy_source_id']
            or info.get('game_code_sources') != [
                dict(source_id=row['source_id'], kind=row['kind']) for row in recipe['sources']]):
        raise ValueError('Native retained-game source metadata differs from the preparation recipe')


def verify_component_rows(rows, package_files):
    if not isinstance(rows, dict):
        raise ValueError('Missing helper/framework file receipt')
    mapped = {('Frameworks/' if name.startswith('StikJIT.framework/') else 'PlugIns/') + name for name in rows}
    if mapped != COMPONENT_FILES or set(package_files) != COMPONENT_FILES:
        raise ValueError('Missing or unapproved helper/framework package members')


def verify_parts(settings, info, host, helper_settings, helper, framework_settings, framework, upstream):
    lock = lock_value()
    identity = info.get('integrated_jit', {})
    if (settings.get('CFBundleIdentifier') != 'io.github.hmcneill46.celeste.everest.jit.everest'
            or settings.get('CFBundleDisplayName') != 'Cabrillo' or settings.get('UIFileSharingEnabled') is not True
            or settings.get('MinimumOSVersion') != '15.0'
            or settings.get('CFBundleShortVersionString') != '0.29.1' or settings.get('CFBundleVersion') != '59'):
        raise ValueError('Host identity, file sharing or iOS15 support differs')
    if (identity.get('upstream_commit') != COMMIT or identity.get('upstream_archive_sha256') != ARCHIVE_SHA256
            or identity.get('bundled_idevice_ffi') != lock['bundled_idevice_ffi']
            or identity.get('framework_in_host') is not False or identity.get('livecontainer_supported') is not False
            or identity.get('helper_extension') is not True or identity.get('automatic_run') is not True
            or identity.get('pairing_file') != 'pairingFile.plist'
            or identity.get('ready_gate') != 'helper_success_and_native_checks_after_detach'):
        raise ValueError('Integrated JIT build contract differs')
    if upstream != lock:
        raise ValueError('Bundled StikJIT source/binary disclosure differs')
    host_details = macho_details_data(host)
    if (host_details['kind'] != 2 or any('StikJIT' in p for p in host_details['linked'])
            or len(host_details['platforms']) != 1 or host_details['platforms'][0]['minimum'] != 0xf0000):
        raise ValueError('iOS15 host must not load StikJIT')
    if (helper_settings.get('CFBundleIdentifier') != settings['CFBundleIdentifier'] + '.JITHelper'
            or helper_settings.get('CFBundleExecutable') != 'CabrilloJITHelper'
            or helper_settings.get('CFBundleShortVersionString') != settings['CFBundleShortVersionString']
            or helper_settings.get('CFBundleVersion') != settings['CFBundleVersion']
            or helper_settings.get('MinimumOSVersion') != '17.4'
            or helper_settings.get('CFBundleSupportedPlatforms') != ['iPhoneOS']
            or helper_settings.get('UIDeviceFamily') != [1, 2]
            or helper_settings.get('NSExtension', {}).get('NSExtensionPointIdentifier') != 'com.apple.ar.viewer'
            or helper_settings.get('NSExtension', {}).get('NSExtensionPrincipalClass') != 'CabrilloJITHelperHandler'):
        raise ValueError('Helper extension identity/principal class differs')
    if (framework_settings.get('CFBundleExecutable') != 'StikJIT'
            or framework_settings.get('CFBundleIdentifier') != 'com.stik.StikJIT'
            or framework_settings.get('CFBundleSupportedPlatforms') != ['iPhoneOS']
            or framework_settings.get('MinimumOSVersion') != '17.4'):
        raise ValueError('Framework identity differs')
    for binary, kind in [(helper, 2), (framework, 6)]:
        details = macho_details_data(binary)
        if details['kind'] != kind or details['platforms'] != [dict(platform=2, minimum=0x110400, sdk=0x1a0500)]:
            raise ValueError('Helper/framework arm64 platform or minimum OS differs')
        if kind == 2 and '@rpath/StikJIT.framework/StikJIT' not in details['linked']:
            raise ValueError('Helper framework link missing')
        if kind == 2 and '@executable_path/../../Frameworks' not in details['rpaths']:
            raise ValueError('Helper framework run path missing')
        if kind == 6 and details['install_name'] != '@rpath/StikJIT.framework/StikJIT':
            raise ValueError('Framework install name differs')


def verify(directory):
    result = verify_owned(directory)
    receipt = json.loads((directory / 'build-receipt.json').read_text())
    prefix = 'Payload/CelesteJITEverest.app/'
    with zipfile.ZipFile(directory / receipt['ipa']) as archive:
        read = lambda name: archive.read(prefix + name)
        settings = plistlib.loads(read('Info.plist'))
        info = json.loads(read('BuildInfo.json'))
        verify_combined_notice(read('THIRD_PARTY_NOTICES.md').decode('utf-8'), info)
        if read('licenses/MORRO-LICENSE') != (Path(__file__).resolve().parents[1] / 'docs/licenses/MORRO-LICENSE.txt').read_bytes():
            raise ValueError('Missing or changed Morro licence')
        from check_input_fixes59_managed import catalogue_projection, ORIGINAL, LEGACY_ORIGINAL
        recipe = json.loads(read('OwnedGameRecipe.json'))
        verify_game_input_contract(info, recipe)
        _, catalogue = catalogue_projection(recipe,
            json.loads(ORIGINAL.read_text()), json.loads(LEGACY_ORIGINAL.read_text()))
        compatibility = info.get('game_input_compatibility', {})
        if (compatibility.get('schema') != 2 or compatibility.get('originals_preserved') is not True
                or sorted(compatibility.get('source_ids', [])) != catalogue['source_ids']):
            raise ValueError('Packaged game-input catalogue differs from build59')
        for name in ['touch_controls', 'input_preferences', 'feather_touch']:
            if not isinstance(info.get(name), dict):
                raise ValueError('Missing combined input feature contract: ' + name)
        verify_parts(settings, info, read('CelesteJITEverest'),
                     plistlib.loads(read('PlugIns/CabrilloJITHelper.appex/Info.plist')),
                     read('PlugIns/CabrilloJITHelper.appex/CabrilloJITHelper'),
                     plistlib.loads(read('Frameworks/StikJIT.framework/Info.plist')),
                     read('Frameworks/StikJIT.framework/StikJIT'),
                     json.loads(read('licenses/StikJIT/UPSTREAM.json')))
        for name in ['StikJIT-MPL-2.0.txt', 'idevice-MIT.txt']:
            expected = (__import__('build_stikjit57').LANE / 'notices' / name).read_bytes()
            if read('licenses/StikJIT/' + name) != expected:
                raise ValueError('Missing or changed StikJIT licence: ' + name)
        for name in ['universal.js', 'legacy.js']:
            if __import__('hashlib').sha256(read('Frameworks/StikJIT.framework/' + name)).hexdigest() != lock_value()['source_files']['Resources/' + name]:
                raise ValueError('Upstream script resource/notice changed')
        if any('pairingfile' in Path(n).name.lower() or Path(n).suffix.lower() == '.mobiledevicepairing' for n in archive.namelist()):
            raise ValueError('Pairing data must never enter the IPA')
        expected_components = {'Frameworks/StikJIT.framework/', 'PlugIns/CabrilloJITHelper.appex/'}
        verify_component_rows(receipt.get('stikjit_files'),
                              [name[len(prefix):] for name in archive.namelist() if name.startswith((prefix+'Frameworks/',prefix+'PlugIns/'))])
        for path, digest in receipt['stikjit_files'].items():
            bundled = ('Frameworks/' if path.startswith('StikJIT.framework/') else 'PlugIns/') + path
            if not any(bundled.startswith(p) for p in expected_components) or __import__('hashlib').sha256(read(bundled)).hexdigest() != digest:
                raise ValueError('Packaged helper/framework differs from its fresh build')
    return dict(result, status='PASS_INPUT_FIXES59_PACKAGE',
                integrated_jit_helper_isolated=True, host_minimum_ios='15.0', helper_minimum_ios='17.4',
                pairing_data_bundled=False, source_built_stikjit_swift=True,
                upstream_prebuilt_idevice_disclosed=True, jit_executed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
