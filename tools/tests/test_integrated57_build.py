"""Retained published57 source selection and immutable56 preservation boundaries."""
import copy
import json
from pathlib import Path
import plistlib
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compile_release57 as build


class IntegratedBuildChecks(unittest.TestCase):
    def setUp(self):
        self.lock = build.read_json(build.IDENTITY/'Dependencies.json')

    def test_retained_recipe_and_identity(self):
        config = build.read_json(build.ROOT/'release/public57.json')
        self.assertEqual(config['public_build_script'], 'tools/build_release57.py')
        self.assertEqual((config['version'], config['build_number']), ('0.26.0', '57'))
        self.assertFalse(config['physical_device_tested'])
        settings = plistlib.loads((build.IDENTITY/'Info.plist').read_bytes())
        previous = plistlib.loads((build.ROOT/'release/app56/Info.plist').read_bytes())
        self.assertEqual(settings['CFBundleIdentifier'], previous['CFBundleIdentifier'])
        self.assertTrue(settings['UIFileSharingEnabled'])
        self.assertEqual(settings['MinimumOSVersion'], '15.0')

    def test_all274_actual_accepted56_inputs_remain_exact(self):
        build.validate_overlay(self.lock)
        self.assertEqual(len(self.lock['retained_build56_source_sha256']), 274)

    def test_missing_or_substituted_frozen_map_rejected(self):
        for mode in ['missing', 'substituted']:
            lock = copy.deepcopy(self.lock)
            name = next(iter(lock['retained_build56_source_sha256']))
            if mode=='missing': del lock['retained_build56_source_sha256'][name]
            else: lock['retained_build56_source_sha256'][name] = '0'*64
            with self.subTest(mode=mode), self.assertRaises(ValueError): build.validate_overlay(lock)

    def test_actual_new_ui_main_and_coordinator_are_selected(self):
        native = build.selected_native_sources(self.lock)
        swift = build.selected_swift_sources()
        for name in ['main.m','CJPlatformOptions.m','CJIntegratedJITCoordinator.m','CJIntegratedJITLaunch.m']:
            self.assertIn(build.INTEGRATED_OVERLAY/'src'/name, native)
        self.assertIn(build.OVERLAY/'src/CJDocumentPickerCompatibility.m', native)
        self.assertIn(build.INTEGRATED_OVERLAY/'native/LauncherUI.swift', swift)
        self.assertIn(build.INTEGRATED_OVERLAY/'native/IntegratedJITViews.swift', swift)
        self.assertNotIn(build.SOURCE/'native/LauncherUI.swift', swift)
        self.assertEqual(len({p.stem for p in native}), len(native))
        self.assertEqual(len({p.stem for p in swift}), len(swift))

    def test_missing_or_redirected_ui_and_native_sources_rejected(self):
        for change in [('source_overrides', {}), ('added_native_sources', []),
                       ('swift_source_overrides', {}), ('added_swift_sources', [])]:
            lock = copy.deepcopy(self.lock); lock[change[0]] = change[1]
            with self.subTest(field=change[0]), self.assertRaises(ValueError): build.validate_overlay(lock)

    def test_stikjit_cannot_replace_everest_or_download_pins(self):
        previous = build.read_json(build.ROOT/'release/app56/Dependencies.json')
        for key in ['public_download_lock','nuget_lock','nuget_host_lock','shared_source_sha256','fmod_input_policy']:
            self.assertEqual(self.lock[key], previous[key])
        self.assertEqual(build.validate_runtime_identity()['builtins']['Everest'], '1.6642.0')
        build.validate_download_metadata()


if __name__ == '__main__':
    unittest.main()
