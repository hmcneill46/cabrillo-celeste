"""Keep the input repairs on59 and preserve the complete published58 recipe."""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compile_release59 as build
import compile_input_fixes59 as bootstrap
import check_input_fixes59_managed as audit
from release_pipeline import readiness


class InputFixes59BuildChecks(unittest.TestCase):
    def setUp(self):
        self.lock = build.read_json(build.IDENTITY / 'Dependencies.json')

    def test_new_recipe_and_both_app_identities_agree(self):
        identity, settings = build.validate_build_identity()
        self.assertEqual((identity['version'], identity['build_number']), ('0.29.1', '59'))
        previous = plistlib.loads((build.ROOT / 'release/app58/Info.plist').read_bytes())
        self.assertEqual(settings['CFBundleIdentifier'], previous['CFBundleIdentifier'])
        self.assertEqual(settings['MinimumOSVersion'], '15.0')
        self.assertEqual(bootstrap.SOURCE, build.SOURCE)
        self.assertEqual(audit.ORIGINAL, build.SOURCE / 'OriginalGameIdentity.json')

    def test_global_trial_recipe_selects59_without_changing_published58(self):
        config, _ = readiness(build.ROOT)
        self.assertEqual((config['version'], config['build_number']), ('0.29.1', '59'))
        self.assertEqual(config['public_build_script'], 'tools/build_release59.py')
        previous = build.read_json(build.ROOT / 'release/public58.json')
        self.assertEqual((previous['version'], previous['build_number']), ('0.29.0', '58'))
        self.assertEqual(previous['public_build_script'], 'tools/build_release58.py')

    def test_complete_published58_map_and_dependencies_are_preserved(self):
        rows = self.lock['retained_build58_source_sha256']
        self.assertEqual(len(rows), 345)
        self.assertEqual(hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                         '6a194b902ac0b30e02ad3e1d8501d7edf23b5e3c715123495a003709792f849c')
        build.validate_overlay(self.lock)
        previous = build.read_json(build.ROOT / 'release/app58/Dependencies.json')
        self.assertEqual({k: v for k, v in self.lock.items()
                          if k not in {'application_source', 'retained_build58_source_sha256',
                                       'retained_build57_source_sha256'}}, previous)

    def test_complete_published57_map_is_preserved_too(self):
        rows = self.lock['retained_build57_source_sha256']
        self.assertEqual(len(rows), 299)
        self.assertEqual(hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                         'c4c87269dd81a91a335e33671da4103a7ca935c47f0be9522c19159d468c5624')
        for mode in ['omit', 'rewrite']:
            value = copy.deepcopy(self.lock)
            older = value['retained_build57_source_sha256']
            name = next(iter(older))
            if mode == 'omit':
                del older[name]
            else:
                older[name] = '0' * 64
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'retained build57 source lock'):
                build.validate_overlay(value)

    def test_changed57_source_outside58_map_is_rejected(self):
        name = next(name for name in self.lock['retained_build57_source_sha256']
                    if name not in self.lock['retained_build58_source_sha256'])
        target = build.ROOT / name
        original = build.sha
        with patch.object(build, 'sha', lambda p: '0' * 64 if p == target else original(p)):
            with self.assertRaisesRegex(ValueError, 'Retained build57 source differs'):
                build.validate_overlay(self.lock)

    def test_omitting_or_rewriting_a_frozen_input_cannot_bless_a_new_map(self):
        for mode in ['omit', 'rewrite', 'replace_map']:
            value = copy.deepcopy(self.lock)
            rows = value['retained_build58_source_sha256']
            name = next(iter(rows))
            if mode == 'omit':
                del rows[name]
            elif mode == 'rewrite':
                rows[name] = '0' * 64
            else:
                value['retained_build58_source_sha256'] = {}
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'retained build58 source lock'):
                build.validate_overlay(value)

    def test_a_changed_frozen_source_is_rejected(self):
        target = build.ROOT / next(iter(self.lock['retained_build58_source_sha256']))
        original = build.sha
        with patch.object(build, 'sha', lambda p: '0' * 64 if p == target else original(p)):
            with self.assertRaisesRegex(ValueError, 'Retained build58 source differs'):
                build.validate_overlay(self.lock)

    def test_dependency_or_helper_lock_drift_is_rejected(self):
        for key, value in [('public_download_lock', 'release/owned-game-dependencies.json'),
                           ('nuget_lock', 'unreviewed.json'),
                           ('stikjit_dependency_lock', 'unreviewed.json'),
                           ('shared_source_sha256', {})]:
            changed = copy.deepcopy(self.lock)
            changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'retained dependency selection'):
                build.validate_overlay(changed)

    def test_substituting_the_old_application_lane_is_rejected(self):
        changed = copy.deepcopy(self.lock)
        changed['application_source'] = 'experiments/ios-jit/launcher-unified58'
        with self.assertRaisesRegex(ValueError, 'source or retained dependency selection'):
            build.validate_overlay(changed)

    def test_complete_source_selection_uses59_including_both_repair_paths(self):
        native = build.selected_native_sources(self.lock)
        swift = build.selected_swift_sources()
        self.assertEqual(len(native), 24)
        self.assertEqual(len(swift), 25)
        self.assertTrue(all(p.parent == build.SOURCE / 'src' for p in native))
        self.assertTrue(all(p.parent == build.SOURCE / 'native' for p in swift))
        self.assertIn(build.SOURCE / 'native/TouchEditor.swift', swift)
        self.assertIn(build.SOURCE / 'src/CJIntegratedJITCoordinator.m', native)
        captured = set(build.application_source_inputs())
        for name in ['native/TouchEditor.swift', 'managed/ControllerIntegration.cs',
                     'managed/GameEntry.cs', 'tests/RetainedPackageInputTests.m']:
            self.assertIn(build.SOURCE / name, captured)
        self.assertTrue(all(p in captured for p in native + swift))

    def test_changed_lane_or_public_identity_is_rejected(self):
        original = build.read_json
        for target, key, value in [(build.SOURCE / 'BuildIdentity.json', 'build_number', '58'),
                                   (build.IDENTITY / 'BuildIdentity.json', 'version', '0.29.0'),
                                   (build.ROOT / 'release/public59.json', 'public_build_script', 'tools/build_release58.py')]:
            changed = copy.deepcopy(original(target))
            changed[key] = value
            with self.subTest(target=target), patch.object(build, 'read_json', lambda p: changed if p == target else original(p)):
                with self.assertRaisesRegex(ValueError, 'identities differ'):
                    build.validate_build_identity()

    def test_public_regression_checkers_are_captured_for_future_package_provenance(self):
        captured = build.regression_source_inputs()
        self.assertEqual(len(captured), 8)
        self.assertEqual(len(set(captured)), len(captured))
        self.assertIn(build.ROOT / 'tools/check_input_fixes59_saved_shortcuts.py', captured)
        self.assertTrue(all(p.is_file() and not p.is_symlink() for p in captured))

    def test_runtime_downloads_and_all_original_sources_stay_unchanged(self):
        self.assertEqual(build.validate_runtime_identity()['builtins']['Everest'], '1.6642.0')
        build.validate_download_metadata()
        previous = build.ROOT / 'experiments/ios-jit/launcher-unified58'
        for name in ['OriginalGameIdentity.json', 'GameContentManifest.json', 'RuntimeIdentity.json',
                     'RuntimeCompatibleReleases.json', 'CompatibilityDownloads.json']:
            self.assertEqual((build.SOURCE / name).read_bytes(), (previous / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
