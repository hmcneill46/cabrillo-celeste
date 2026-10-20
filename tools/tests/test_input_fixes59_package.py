"""Reject mixed58/59 app metadata while retaining the isolated helper boundary."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_input_fixes59 import verify_parts, verify_component_rows, COMPONENT_FILES
import test_integrated57_package as retained


class InputFixes59PackageChecks(unittest.TestCase):
    @staticmethod
    def parts():
        parts = copy.deepcopy(retained.IntegratedPackageChecks().parts())
        for settings in [parts[0], parts[3]]:
            settings.update(CFBundleVersion='59', CFBundleShortVersionString='0.29.1')
        return parts

    def test_new_host_and_helper_share59_identity(self):
        verify_parts(*self.parts())

    def test_a58_helper_cannot_ship_with59_host(self):
        parts = self.parts()
        parts[3].update(CFBundleVersion='58', CFBundleShortVersionString='0.29.0')
        with self.assertRaisesRegex(ValueError, 'Helper extension identity'):
            verify_parts(*parts)

    def test_a58_host_cannot_claim59_package_validation(self):
        parts = self.parts()
        parts[0].update(CFBundleVersion='58', CFBundleShortVersionString='0.29.0')
        with self.assertRaisesRegex(ValueError, 'Host identity'):
            verify_parts(*parts)

    def test_same_version_does_not_allow_helper_to_lower_its_ios_requirement(self):
        parts = self.parts()
        parts[3]['MinimumOSVersion'] = '15.0'
        with self.assertRaisesRegex(ValueError, 'Helper extension identity'):
            verify_parts(*parts)

    def test_framework_cannot_be_strongly_linked_into_host(self):
        parts = self.parts()
        parts[2] = retained.binary(kind=2, minimum=0xf0000, linked=['@rpath/StikJIT.framework/StikJIT'])
        with self.assertRaisesRegex(ValueError, 'must not load StikJIT'):
            verify_parts(*parts)

    def test_runtime_component_set_rejects_missing_and_extra_build_products(self):
        rows = {name.removeprefix('Frameworks/').removeprefix('PlugIns/'): '0' * 64
                for name in COMPONENT_FILES}
        verify_component_rows(rows, COMPONENT_FILES)
        for files in [COMPONENT_FILES - {'Frameworks/StikJIT.framework/legacy.js'},
                      COMPONENT_FILES | {'Frameworks/StikJIT.framework/Modules/StikJIT.swiftmodule'},
                      COMPONENT_FILES | {'PlugIns/CabrilloJITHelper.appex/embedded.mobileprovision'}]:
            with self.subTest(files=files), self.assertRaisesRegex(ValueError, 'package members'):
                verify_component_rows(rows, files)


if __name__ == '__main__':
    unittest.main()
