"""Reject broken helper packaging before a sideloaded app reaches a device."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_stikjit57 import COMMIT, ARCHIVE_SHA256, lock_value, macho_details_data
from verify_integrated_jit57 import verify_parts, verify_component_rows, COMPONENT_FILES
from release_pipeline import verify_integrated_provenance


def string_command(command, text, header=24):
    size = (header + len(text.encode()) + 1 + 7) // 8 * 8
    return struct.pack('<III', command, size, header) + bytes(header - 12) + text.encode() + bytes(size - header - len(text.encode()))


def binary(kind=2, minimum=0x110400, linked=(), install=None, rpaths=(), signed=False):
    commands = [struct.pack('<6I', 0x32, 24, 2, minimum, 0x1a0500, 0)]
    commands += [string_command(0xc, p) for p in linked]
    if install:
        commands.append(string_command(0xd, install))
    commands += [string_command(0x8000001c, p, 12) for p in rpaths]
    if signed:
        commands.append(struct.pack('<4I', 0x1d, 16, 0, 0))
    return struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, kind, len(commands), sum(map(len, commands)), 0, 0) + b''.join(commands)


class IntegratedPackageChecks(unittest.TestCase):
    def parts(self):
        lock = lock_value()
        host = dict(CFBundleIdentifier='io.github.hmcneill46.celeste.everest.jit.everest',
                    CFBundleDisplayName='Cabrillo', CFBundleVersion='57', CFBundleShortVersionString='0.26.0',
                    MinimumOSVersion='15.0', UIFileSharingEnabled=True)
        info = dict(integrated_jit=dict(upstream_commit=COMMIT, upstream_archive_sha256=ARCHIVE_SHA256,
                    bundled_idevice_ffi=lock['bundled_idevice_ffi'], framework_in_host=False,
                    livecontainer_supported=False, helper_extension=True, automatic_run=True,
                    pairing_file='pairingFile.plist', ready_gate='helper_success_and_native_checks_after_detach'))
        helper = dict(CFBundleIdentifier=host['CFBundleIdentifier'] + '.JITHelper', CFBundleExecutable='CabrilloJITHelper',
                      CFBundleVersion='57', CFBundleShortVersionString='0.26.0', MinimumOSVersion='17.4',
                      CFBundleSupportedPlatforms=['iPhoneOS'], UIDeviceFamily=[1, 2],
                      NSExtension=dict(NSExtensionPointIdentifier='com.apple.ar.viewer', NSExtensionPrincipalClass='CabrilloJITHelperHandler'))
        framework = dict(CFBundleIdentifier='com.stik.StikJIT', CFBundleExecutable='StikJIT', MinimumOSVersion='17.4', CFBundleSupportedPlatforms=['iPhoneOS'])
        return [host, info, binary(minimum=0xf0000), helper,
                binary(linked=['@rpath/StikJIT.framework/StikJIT'], rpaths=['@executable_path/../../Frameworks']),
                framework, binary(kind=6, install='@rpath/StikJIT.framework/StikJIT'), lock]

    def test_valid_isolated_components(self):
        verify_parts(*self.parts())

    def test_ordinary_host_remains_usable_without_loading_stikjit(self):
        for update in [dict(minimum=0x110400), dict(minimum=0xf0000, linked=['@rpath/StikJIT.framework/StikJIT'])]:
            parts = self.parts(); parts[2] = binary(**update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                verify_parts(*parts)

    def test_helper_must_resolve_exact_framework(self):
        for update in [dict(linked=[]), dict(linked=['@rpath/StikJIT.framework/StikJIT'], rpaths=[]),
                       dict(linked=['@rpath/StikJIT.framework/StikJIT'], rpaths=['@executable_path/../../Frameworks'], signed=True)]:
            parts = self.parts(); parts[4] = binary(**update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                verify_parts(*parts)

    def test_post_signing_lookup_cannot_replace_package_identity(self):
        for change in [dict(CFBundleIdentifier='example.wrong'), dict(CFBundleVersion='56'),
                       dict(MinimumOSVersion='15.0'), dict(NSExtension={})]:
            parts = self.parts(); parts[3].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_parts(*parts)

    def test_pairing_placement_is_discoverable_without_bundling_credentials(self):
        for change in [dict(UIFileSharingEnabled=False), dict(CFBundleDisplayName='Other name')]:
            parts = self.parts(); parts[0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_parts(*parts)

    def test_source_and_binary_inputs_must_be_disclosed(self):
        parts = self.parts(); parts[7] = copy.deepcopy(parts[7]); parts[7]['bundled_idevice_ffi']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): verify_parts(*parts)
        for change in [dict(ready_gate='helper_success'), dict(framework_in_host=True), dict(livecontainer_supported=True)]:
            parts = self.parts(); parts[1]['integrated_jit'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): verify_parts(*parts)

    def test_malformed_or_signed_macho_rejected(self):
        for data in [b'', b'\xcf\xfa\xed\xfe', binary(signed=True), binary()[:-1], binary()[:16] + struct.pack('<I', 1000) + binary()[20:]]:
            with self.subTest(bytes=len(data)), self.assertRaises((ValueError, struct.error)):
                macho_details_data(data)

    def test_receipt_cannot_omit_components_or_ship_symbols(self):
        rows = {name.removeprefix('Frameworks/').removeprefix('PlugIns/'): 'a' * 64 for name in COMPONENT_FILES}
        verify_component_rows(rows, COMPONENT_FILES)
        for changed in [{}, dict(list(rows.items())[:-1]), dict(rows, **{'StikJIT.framework/StikJIT.dSYM/symbols': 'b' * 64})]:
            with self.subTest(count=len(changed)), self.assertRaises(ValueError):
                verify_component_rows(changed, COMPONENT_FILES)
        with self.assertRaises(ValueError):
            verify_component_rows(rows, COMPONENT_FILES | {'PlugIns/unexpected.appex/binary'})

    def test_provenance_cannot_describe_prebuilt_ffi_as_fresh_source(self):
        lock = lock_value()
        rows = {name.removeprefix('Frameworks/').removeprefix('PlugIns/'): 'a' * 64 for name in COMPONENT_FILES}
        value = dict(integrated_jit=dict(upstream_commit=COMMIT, archive_sha256=ARCHIVE_SHA256,
            bundled_idevice_ffi=lock['bundled_idevice_ffi'], framework_linked_into_host=False,
            helper_minimum_ios='17.4', helper_files=rows, physical_device_tested=False),
            dependencies=[dict(name='StikJIT/'+COMMIT, kind='mixed', sha256=ARCHIVE_SHA256),
                          dict(name='StikJIT/idevice-ffi', kind='binary', sha256=lock['bundled_idevice_ffi']['sha256'])])
        verify_integrated_provenance(value)
        for transform in [lambda v: v['dependencies'][1].update(kind='source'),
                          lambda v: v['dependencies'].pop(),
                          lambda v: v['integrated_jit'].update(helper_files={}),
                          lambda v: v['integrated_jit'].update(framework_linked_into_host=True)]:
            changed = copy.deepcopy(value); transform(changed)
            with self.assertRaises(ValueError): verify_integrated_provenance(changed)


if __name__ == '__main__':
    unittest.main()
