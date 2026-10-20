"""Build56 selectors, frozen-source boundaries and compatibility transport repair."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compile_release55 as previous
import compile_release56 as build
import check_dependency56_compile as check
from release_pipeline import readiness


class Dependency56BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = build.read_json(build.IDENTITY / 'Dependencies.json')

    def test_preserved_public_recipe_builds56_with_matching_identity(self):
        config = build.read_json(build.ROOT / 'release/public56.json')
        self.assertEqual(config['public_build_script'], 'tools/build_release56.py')
        self.assertEqual((config['version'], config['build_number']), ('0.25.1', '56'))
        self.assertEqual(build.read_json(build.IDENTITY/'BuildIdentity.json')['version'], config['version'])

    def test_exact_frozen55_map_and_all_old_inputs_remain_valid(self):
        rows = self.lock['retained_build55_source_sha256']
        self.assertEqual(len(rows), 261)
        self.assertEqual(hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                         '051c1612715137f78e7355a96ad45364c8132edacf1b6b29300752bfc11a5b1f')
        build.validate_overlay(self.lock)

    def test_missing_or_replaced_frozen_map_is_rejected(self):
        for mode in ['missing', 'replaced']:
            lock = copy.deepcopy(self.lock)
            name = next(iter(lock['retained_build55_source_sha256']))
            if mode == 'missing': del lock['retained_build55_source_sha256'][name]
            else: lock['retained_build55_source_sha256'][name] = '0' * 64
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'retained build55 source lock'):
                build.validate_overlay(lock)

    def test_selected_production_swift_uses_three56_files_and_exact55_runtime(self):
        native, swift, objc = check.selected_production_sources(build, self.lock)
        names = {p.name: p for p in swift}
        self.assertEqual(names['RuntimeIdentity.swift'], build.EVEREST_OVERLAY / 'native/RuntimeIdentity.swift')
        for name in ['DependencyPlan.swift', 'DependencyInstaller.swift', 'ModLibrary.swift']:
            self.assertEqual(names[name], build.DEPENDENCY_OVERLAY / 'native' / name)
        self.assertEqual(native, previous.selected_native_sources(build.read_json(previous.IDENTITY / 'Dependencies.json')))
        self.assertEqual(objc, [build.OVERLAY / 'src/main.m', build.OVERLAY / 'src/CJDocumentPickerCompatibility.m'])
        self.assertEqual(len(swift), len(previous.selected_swift_sources()))

    def test_silently_reusing_previous_swift_selection_is_rejected(self):
        with patch.object(build, 'selected_swift_sources', previous.selected_swift_sources):
            with self.assertRaises(ValueError): check.selected_production_sources(build, self.lock)

    def test_missing_or_redirected_swift_override_is_rejected(self):
        for value in [{}, {'native/DependencyPlan.swift': 'experiments/ios-jit/launcher-shortcut-cellular/native/DependencyPlan.swift'}]:
            lock = copy.deepcopy(self.lock); lock['swift_source_overrides'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'dependency source selection'):
                build.validate_overlay(lock)

    def test_runtime_and_dependency_builtin_identity_still6642(self):
        identity = build.validate_runtime_identity()
        check.require_expected_identity(identity)
        self.assertEqual(identity['builtins']['Everest'], '1.6642.0')
        self.assertEqual(identity['builtins']['EverestCore'], '1.6642.0')
        self.assertEqual(identity, previous.validate_runtime_identity())

    def test_femto_transport_relocates_identical_archive(self):
        rows = build.validate_download_metadata()
        row = next(row for row in rows if any(m['name'] == 'FemtoHelper' for m in row['modules']))
        self.assertEqual(row['url'], 'https://gamebanana.com/mmdl/1838255')
        self.assertEqual(row['mirrorName'], '1838255')
        self.assertEqual(row['bytes'], 11103153)
        self.assertEqual(row['pinnedSHA256'], '5a845805bae30490ed7c9da84410fbe672628b8fe927a830f5f2eb148eb88419')
        self.assertEqual(row['modules'][0]['version'], '1.15.22')

    def altered_metadata(self, mutate, filename='CompatibilityDownloads.json'):
        original = build.read_json
        target = build.DEPENDENCY_OVERLAY / filename
        changed = copy.deepcopy(original(target)); mutate(changed)
        with patch.object(build, 'read_json', lambda path: changed if path == target else original(path)):
            with self.assertRaises(ValueError): build.validate_download_metadata()

    def test_old_broken_femto_url_is_rejected(self):
        self.altered_metadata(lambda rows: rows[-1].update(url='https://gamebanana.com/mmdl/1776026'))

    def test_helper_version_integrity_and_dependency_drift_are_rejected(self):
        changes = [lambda rows: rows[-1].update(pinnedSHA256='0' * 64),
                   lambda rows: rows[-1].update(bytes=11103154),
                   lambda rows: rows[-1]['modules'][0].update(version='1.16.2'),
                   lambda rows: rows[-1]['modules'][0]['dependencies'][0].update(version='9.0.0'),
                   lambda rows: rows[-1].update(mirrorName='1776026'),
                   lambda rows: rows[-1].update(gameBananaPage='https://gamebanana.com/mods/1')]
        for change in changes:
            with self.subTest(change=change): self.altered_metadata(change)

    def test_stale_build_contract_and_unrelated_transport_change_are_rejected(self):
        self.altered_metadata(lambda d: d['mod_download_manifest']['FemtoHelper-v1.15.22.zip'].update(url='https://gamebanana.com/mmdl/1776026'), 'BuildContract.json')
        self.altered_metadata(lambda d: d['mod_download_manifest']['GravityHelper-v1.2.28.zip'].update(url='https://example.invalid/unreviewed'), 'BuildContract.json')


if __name__ == '__main__': unittest.main()
