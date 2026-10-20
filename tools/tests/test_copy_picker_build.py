"""Build54 source-selection and preserved installation/dependency boundaries."""
import json
from pathlib import Path
import plistlib
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compile_release54 as build
from release_pipeline import readiness


class CopyPickerBuildTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((build.IDENTITY / 'Dependencies.json').read_text())

    def test_current_recipe_retains_build54_picker(self):
        config, report = readiness(build.ROOT)
        self.assertEqual(config['public_build_script'], 'tools/build_release56.py')
        self.assertEqual(report['build_number'], '56')
        self.assertFalse(report['physical_device_tested'])
        sources = build.selected_native_sources(self.lock)
        self.assertIn(build.OVERLAY / 'src/main.m', sources)
        self.assertIn(build.OVERLAY / 'src/CJDocumentPickerCompatibility.m', sources)
        self.assertNotIn(build.SOURCE / 'src/main.m', sources)
        self.assertEqual(len({path.stem for path in sources}), len(sources))

    def test_version_only_plist_change_preserves_installed_data_identity(self):
        original = plistlib.loads((build.ROOT / 'release/app53/Info.plist').read_bytes())
        repaired = plistlib.loads((build.IDENTITY / 'Info.plist').read_bytes())
        self.assertEqual(repaired.pop('CFBundleVersion'), '54')
        self.assertEqual(repaired.pop('CFBundleShortVersionString'), '0.24.3')
        original.pop('CFBundleVersion')
        original.pop('CFBundleShortVersionString')
        self.assertEqual(repaired, original)

    def test_dependency_and_compatibility_inputs_remain_exact53(self):
        original = json.loads((build.ROOT / 'release/app53/Dependencies.json').read_text())
        for key in ['public_download_lock', 'nuget_lock', 'shared_source_sha256', 'fmod_input_policy',
                    'private_capsule_required', 'nuget_host_lock', 'base_source_sha256']:
            self.assertEqual(self.lock[key], original[key], key)
        for ext in ['h', 'm']:
            preserved = build.ROOT / ('experiments/ios-jit/launcher-signing-picker/src/'
                                      'CJDocumentPickerCompatibility.' + ext)
            current = build.OVERLAY / 'src' / ('CJDocumentPickerCompatibility.' + ext)
            self.assertEqual(build.sha(current), build.sha(preserved))

    def test_recipe_cannot_silently_build_open_in_place_main53(self):
        self.lock['source_overrides']['src/main.m'] = ('experiments/ios-jit/'
                                                     'launcher-signing-picker/src/main.m')
        with self.assertRaisesRegex(ValueError, 'exact main and compatibility'):
            build.selected_native_sources(self.lock)

    def test_recipe_cannot_omit_compatibility(self):
        self.lock['added_native_sources'] = []
        with self.assertRaisesRegex(ValueError, 'exact main and compatibility'):
            build.selected_native_sources(self.lock)

    def test_recipe_rejects_incomplete_base_lock(self):
        self.lock['base_source_sha256'].pop(next(iter(self.lock['base_source_sha256'])))
        with self.assertRaisesRegex(ValueError, 'Incomplete frozen source lock'):
            build.selected_native_sources(self.lock)

    def test_recipe_rejects_modified_base_pin(self):
        name = next(iter(self.lock['base_source_sha256']))
        self.lock['base_source_sha256'][name] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Frozen source differs'):
            build.selected_native_sources(self.lock)

    def test_recipe_rejects_incomplete_retained_compatibility_lock(self):
        self.lock['retained_picker_compatibility_sha256'].pop(
            next(iter(self.lock['retained_picker_compatibility_sha256'])))
        with self.assertRaisesRegex(ValueError, 'Incomplete retained picker compatibility lock'):
            build.selected_native_sources(self.lock)

    def test_recipe_rejects_modified_retained_compatibility_pin(self):
        name = next(iter(self.lock['retained_picker_compatibility_sha256']))
        self.lock['retained_picker_compatibility_sha256'][name] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Retained picker compatibility differs'):
            build.selected_native_sources(self.lock)


if __name__ == '__main__':
    unittest.main()
