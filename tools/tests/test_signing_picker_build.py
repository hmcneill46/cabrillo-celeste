import json
from pathlib import Path
import plistlib
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compile_release53 as build
from release_pipeline import readiness


class SigningPickerBuildTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((build.IDENTITY / 'Dependencies.json').read_text())

    def test_build_selects_repair_and_preserves_bundle_identity(self):
        sources = build.selected_native_sources(self.lock)
        self.assertIn(build.OVERLAY / 'src/main.m', sources)
        self.assertIn(build.OVERLAY / 'src/CJDocumentPickerCompatibility.m', sources)
        self.assertNotIn(build.SOURCE / 'src/main.m', sources)
        self.assertEqual(len({path.stem for path in sources}), len(sources))
        original = plistlib.loads((build.ROOT / 'release/app52/Info.plist').read_bytes())
        repaired = plistlib.loads((build.IDENTITY / 'Info.plist').read_bytes())
        self.assertEqual(repaired['CFBundleVersion'], '53')
        self.assertEqual(repaired['CFBundleIdentifier'], original['CFBundleIdentifier'])
        self.assertEqual(repaired['CFBundleURLTypes'], original['CFBundleURLTypes'])

    def test_preserved_build53_manifest_remains_independent(self):
        preserved = json.loads((build.ROOT / 'release/public53.json').read_text())
        self.assertEqual(preserved['public_build_script'], 'tools/build_release53.py')
        self.assertEqual(preserved['build_number'], '53')
        config, report = readiness(build.ROOT)
        self.assertEqual(config['public_build_script'], 'tools/build_release54.py')
        self.assertEqual(report['build_number'], '54')
        self.assertFalse(report['physical_device_tested'])

    def test_recipe_cannot_silently_build_original_main(self):
        self.lock['source_overrides']['src/main.m'] = str((build.SOURCE / 'src/main.m').relative_to(build.ROOT))
        with self.assertRaisesRegex(ValueError, 'exact main and compatibility'):
            build.selected_native_sources(self.lock)

    def test_recipe_cannot_omit_compatibility_implementation(self):
        self.lock['added_native_sources'] = []
        with self.assertRaisesRegex(ValueError, 'exact main and compatibility'):
            build.selected_native_sources(self.lock)

    def test_recipe_rejects_incomplete_frozen_source_lock(self):
        self.lock['base_source_sha256'].pop(next(iter(self.lock['base_source_sha256'])))
        with self.assertRaisesRegex(ValueError, 'Incomplete frozen source lock'):
            build.selected_native_sources(self.lock)

    def test_recipe_rejects_modified_frozen_source(self):
        name = next(iter(self.lock['base_source_sha256']))
        self.lock['base_source_sha256'][name] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Frozen source differs'):
            build.selected_native_sources(self.lock)

    def test_recipe_cannot_change_base_lane(self):
        self.lock['application_source'] = 'experiments/ios-jit/launcher-catalogue'
        with self.assertRaisesRegex(ValueError, 'Unexpected signing-picker source lanes'):
            build.selected_native_sources(self.lock)


if __name__ == '__main__':
    unittest.main()
