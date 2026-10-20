"""Reject a mixed-version helper or weakened platform boundary in the merged IPA."""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_unified58 import verify_parts
import test_integrated57_package as retained


class UnifiedPackageChecks(unittest.TestCase):
    @staticmethod
    def parts():
        parts = copy.deepcopy(retained.IntegratedPackageChecks().parts())
        for settings in [parts[0], parts[3]]:
            settings.update(CFBundleVersion='58', CFBundleShortVersionString='0.29.0')
        return parts

    def test_combined_host_and_helper_share_version(self):
        verify_parts(*self.parts())

    def test_retained57_helper_cannot_ship_with58_host(self):
        parts = self.parts()
        parts[3].update(CFBundleVersion='57', CFBundleShortVersionString='0.26.0')
        with self.assertRaisesRegex(ValueError, 'Helper extension identity'):
            verify_parts(*parts)

    def test_lowering_helper_requirement_does_not_make_it_ios15_compatible(self):
        parts = self.parts()
        parts[3]['MinimumOSVersion'] = '15.0'
        with self.assertRaisesRegex(ValueError, 'Helper extension identity'):
            verify_parts(*parts)


if __name__ == '__main__':
    unittest.main()
