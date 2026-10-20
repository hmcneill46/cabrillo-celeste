"""Reject a mixed-version helper or weakened platform boundary in the merged IPA."""
import copy
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_unified58 import verify_parts, verify_game_input_contract
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

    def test_preparation_recipe_alone_cannot_make_native_retained_inputs_available(self):
        root = Path(__file__).resolve().parents[2]
        recipe = json.loads((root/'experiments/ios-jit/launcher-unified58/OriginalGameIdentity.json').read_text())
        info = dict(game_code_legacy_source_id=recipe['legacy_source_id'],
                    game_code_sources=[dict(source_id=r['source_id'], kind=r['kind']) for r in recipe['sources']])
        verify_game_input_contract(info, recipe)
        for name in ['game_code_legacy_source_id', 'game_code_sources']:
            broken = dict(info)
            del broken[name]
            with self.subTest(missing=name), self.assertRaisesRegex(ValueError, 'retained-game'):
                verify_game_input_contract(broken, recipe)
        broken = copy.deepcopy(info)
        broken['game_code_sources'].pop()
        with self.assertRaisesRegex(ValueError, 'retained-game'):
            verify_game_input_contract(broken, recipe)


if __name__ == '__main__':
    unittest.main()
