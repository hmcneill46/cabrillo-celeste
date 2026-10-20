"""Build58 integration controls for both input catalogues and selected source lanes."""
from copy import deepcopy
import json
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_unified58_managed as audit
import compile_release58 as build
import compile_unified58 as managed
from release_pipeline import readiness


class UnifiedCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = audit.read(audit.ORIGINAL)
        self.legacy = audit.read(audit.LEGACY_ORIGINAL)
        self.recipe = dict(deepcopy(self.catalogue), tools={'Celeste.Mod.mm.dll': '1' * 64})

    def validate(self, recipe=None, catalogue=None, legacy=None):
        return audit.catalogue_projection(
            self.recipe if recipe is None else recipe,
            self.catalogue if catalogue is None else catalogue,
            self.legacy if legacy is None else legacy)

    def test_all_store_variants_and_legacy_identity_survive(self):
        before = deepcopy(self.recipe)
        projection, report = self.validate()
        self.assertEqual(report['source_count'], 4)
        self.assertEqual(report['kinds'], ['empty-content', 'standard', 'steam', 'steam'])
        self.assertEqual(projection['inputs'], self.legacy['inputs'])
        self.assertEqual(projection['source_id'], self.legacy['source_id'])
        self.assertEqual(projection['tools'], self.recipe['tools'])
        self.assertEqual(self.recipe, before)
        self.assertEqual(self.catalogue, audit.read(audit.LOCAL_CATALOGUE))

    def test_schema1_recipe_cannot_silently_replace_combined_importer(self):
        with self.assertRaisesRegex(ValueError, 'schema2'):
            self.validate(dict(self.legacy, tools=self.recipe['tools']))

    def test_missing_steam_source_is_rejected(self):
        recipe = deepcopy(self.recipe); recipe['sources'].pop()
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.validate(recipe)
        catalogue = {k: v for k, v in recipe.items() if k != 'tools'}
        with self.assertRaisesRegex(ValueError, 'all four'):
            self.validate(recipe, catalogue)

    def test_changed_input_pin_is_rejected(self):
        recipe = deepcopy(self.recipe)
        recipe['sources'][0]['inputs']['Celeste.exe']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.validate(recipe)
        catalogue = {k: v for k, v in recipe.items() if k != 'tools'}
        with self.assertRaisesRegex(ValueError, 'canonical'):
            self.validate(recipe, catalogue)

    def test_duplicate_source_cannot_replace_a_store_variant(self):
        recipe = deepcopy(self.recipe); recipe['sources'][-1] = deepcopy(recipe['sources'][-2])
        catalogue = {k: v for k, v in recipe.items() if k != 'tools'}
        with self.assertRaisesRegex(ValueError, 'unique'):
            self.validate(recipe, catalogue)

    def test_input_adaptation_must_match_its_files(self):
        recipe = deepcopy(self.recipe); recipe['sources'][0]['kind'] = 'steam'
        catalogue = {k: v for k, v in recipe.items() if k != 'tools'}
        with self.assertRaisesRegex(ValueError, 'adaptation'):
            self.validate(recipe, catalogue)

    def test_invalid_file_sizes_and_hashes_are_rejected(self):
        for field, value in [('bytes', 0), ('bytes', True), ('bytes', 32 * 1024 * 1024 + 1),
                             ('sha256', '../untrusted'), ('sha256', 'A' * 64)]:
            recipe = deepcopy(self.recipe)
            recipe['sources'][0]['inputs']['Celeste.exe'][field] = value
            catalogue = {k: v for k, v in recipe.items() if k != 'tools'}
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, 'file pin'):
                self.validate(recipe, catalogue)

    def test_legacy_migration_target_cannot_be_changed(self):
        recipe = deepcopy(self.recipe); recipe['legacy_source_id'] = recipe['sources'][0]['source_id']
        catalogue = {k: v for k, v in recipe.items() if k != 'tools'}
        with self.assertRaisesRegex(ValueError, 'schema1 game identity'):
            self.validate(recipe, catalogue)

    def test_cache_recipe_covers_new_adapter_and_all_original_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for name in ['Cabrillo.Bootstrap.dll', 'Celeste.Mod.mm.dll', 'NETCoreifier.dll',
                         'FNA.dll', 'Mono.Cecil.dll']:
                (work / name).write_bytes(('fixture ' + name).encode())
            output = work / 'recipe.json'
            recipe = managed.write_recipe(self.catalogue, work, output)
            self.validate(recipe)
            original_hash = audit.sha(output)
            (work / 'Cabrillo.Bootstrap.dll').write_bytes(b'new merged preparation')
            updated = managed.write_recipe(self.catalogue, work, output)
            self.assertNotEqual(audit.sha(output), original_hash)
            self.assertEqual(updated['sources'], recipe['sources'])
            self.assertEqual(updated['legacy_source_id'], recipe['legacy_source_id'])
            self.assertNotEqual(updated['tools']['Cabrillo.Bootstrap.dll'], recipe['tools']['Cabrillo.Bootstrap.dll'])


class UnifiedSelectionTests(unittest.TestCase):
    def setUp(self):
        self.lock = build.read_json(build.IDENTITY / 'Dependencies.json')

    def test_historical58_recipe_remains_independent_of_active59_trial(self):
        active, _ = readiness(build.ROOT)
        historical = build.read_json(build.ROOT / 'release/public58.json')
        self.assertEqual((active['version'], active['build_number']), ('0.29.1', '59'))
        self.assertEqual(active['public_build_script'], 'tools/build_release59.py')
        self.assertEqual((historical['version'], historical['build_number']), ('0.29.0', '58'))
        self.assertEqual(historical['public_build_script'], 'tools/build_release58.py')

    def test_new_identity_preserves_installed_data_container(self):
        config = build.read_json(build.ROOT / 'release/public58.json')
        identity = build.read_json(build.IDENTITY / 'BuildIdentity.json')
        settings = plistlib.loads((build.IDENTITY / 'Info.plist').read_bytes())
        old = plistlib.loads((build.ROOT / 'release/app57/Info.plist').read_bytes())
        self.assertEqual((config['version'], config['build_number']), ('0.29.0', '58'))
        self.assertEqual((identity['version'], identity['build_number']), ('0.29.0', '58'))
        self.assertEqual(settings['CFBundleIdentifier'], old['CFBundleIdentifier'])
        self.assertEqual(settings['MinimumOSVersion'], '15.0')
        self.assertEqual(config['public_build_script'], 'tools/build_release58.py')

    def test_selected_host_contains_editor_and_integrated_jit(self):
        native = build.selected_native_sources(self.lock)
        swift = build.selected_swift_sources()
        for name in ['main.m', 'CJGraphicsPlatform.m', 'CJDocumentPickerCompatibility.m',
                     'CJPlatformOptions.m', 'CJIntegratedJITCoordinator.m', 'CJIntegratedJITLaunch.m']:
            self.assertIn(build.SOURCE / 'src' / name, native)
        for name in ['LauncherUI.swift', 'TouchEditor.swift', 'TouchProfile.swift',
                     'IntegratedJITViews.swift', 'DependencyPlan.swift', 'DependencyInstaller.swift',
                     'ModLibrary.swift', 'RuntimeIdentity.swift']:
            self.assertIn(build.SOURCE / 'native' / name, swift)
        self.assertEqual(len({p.stem for p in native}), len(native))
        self.assertEqual(len({p.stem for p in swift}), len(swift))

    def test_selected_numeric_runtime_is_stable6642(self):
        expected = audit.native_identity()
        manifest = build.validate_runtime_identity()
        self.assertEqual(manifest, audit.read(expected))
        self.assertEqual(manifest['builtins']['Everest'], '1.6642.0')
        self.assertEqual(manifest['everestSourceCommit'], audit.COMMIT)

    def test_old_dependency_url_is_rejected_in_combined_metadata(self):
        original = build.read_json
        path = build.SOURCE / 'CompatibilityDownloads.json'
        changed = deepcopy(original(path))
        row = next(row for row in changed if any(m['name'] == 'FemtoHelper' for m in row['modules']))
        row['url'] = 'https://gamebanana.com/mmdl/1776026'
        with patch.object(build, 'read_json', lambda p: changed if p == path else original(p)):
            with self.assertRaisesRegex(ValueError, 'archive selection'):
                build.validate_download_metadata()


if __name__ == '__main__':
    unittest.main()
