"""Build55 compile-check controls for source preservation and actual selection."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_everest6642_compile as check


class RetainedBuild54Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / 'public'
        self.root.mkdir()
        self.rows = {}
        for name, data in [('src/main.m', b'original picker source\n'),
                           ('native/RuntimeIdentity.swift', b'original runtime identity\n')]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            self.rows[name] = check.sha(path)
        self.expected_map = check.map_sha256(self.rows)

    def validate(self, rows=None):
        return check.validate_retained_build54(
            {'retained_build54_source_sha256': self.rows if rows is None else rows},
            root=self.root, expected_count=2, expected_map_sha256=self.expected_map)

    def test_unchanged_files_and_original_map_are_accepted(self):
        self.assertEqual(self.validate(), self.rows)

    def test_captured_input_cannot_be_omitted(self):
        rows = dict(self.rows)
        rows.pop('src/main.m')
        with self.assertRaisesRegex(ValueError, 'all253'):
            self.validate(rows)

    def test_changed_source_is_rejected_with_original_pins(self):
        (self.root / 'src/main.m').write_bytes(b'changed source\n')
        with self.assertRaisesRegex(ValueError, 'Retained build54 source differs'):
            self.validate()

    def test_changed_source_cannot_be_blessed_by_rewriting_pin(self):
        (self.root / 'src/main.m').write_bytes(b'changed source\n')
        rows = dict(self.rows, **{'src/main.m': check.sha(self.root / 'src/main.m')})
        with self.assertRaisesRegex(ValueError, 'source-pin map differs'):
            self.validate(rows)

    def test_private_escape_and_symlink_inputs_are_rejected(self):
        outside = self.root.parent / 'outside.c'
        outside.write_bytes(b'not a public input\n')
        alias = self.root / 'alias.c'
        alias.symlink_to(outside)
        for name in ['../outside.c', str(outside), '.private/source.c', '.build/generated.c', 'alias.c']:
            with self.subTest(name=name):
                rows = {name: check.sha(outside)}
                with self.assertRaisesRegex(ValueError, 'public repository path|aliased'):
                    check.validate_retained_build54(
                        {'retained_build54_source_sha256': rows}, root=self.root,
                        expected_count=1, expected_map_sha256=check.map_sha256(rows))

    def test_production_lock_matches_all253_published54_pins(self):
        path = check.ROOT / 'release/app55/Dependencies.json'
        lock = json.loads(path.read_text())
        rows = check.validate_retained_build54(lock)
        self.assertEqual(len(rows), 253)
        self.assertEqual(check.map_sha256(rows), check.RETAINED54_MAP_SHA256)


class ProductionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name).resolve()
        base, picker, everest = [root / name for name in ['base50', 'picker54', 'everest55']]
        for path in [base / 'src/main.m', base / 'src/Session.c',
                     base / 'native/RuntimeIdentity.swift', base / 'native/Views.swift',
                     picker / 'src/main.m', picker / 'src/CJDocumentPickerCompatibility.m',
                     everest / 'native/RuntimeIdentity.swift']:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('// synthetic public selection fixture\n')
        self.native = [base / 'src/Session.c', picker / 'src/main.m',
                       picker / 'src/CJDocumentPickerCompatibility.m']
        self.swift = [base / 'native/Views.swift', everest / 'native/RuntimeIdentity.swift']
        self.build = SimpleNamespace(SOURCE=base, OVERLAY=picker, EVEREST_OVERLAY=everest,
                                     selected_native_sources=lambda lock: self.native,
                                     selected_swift_sources=lambda: self.swift)

    def test_new_identity_and_retained_picker_sources_are_selected(self):
        native, swift, compiled = check.selected_production_sources(self.build, {})
        self.assertEqual(native, self.native)
        self.assertEqual(swift, self.swift)
        self.assertEqual(compiled, [self.build.OVERLAY / 'src/main.m',
                                    self.build.OVERLAY / 'src/CJDocumentPickerCompatibility.m'])

    def test_old_swift_runtime_identity_is_rejected(self):
        self.swift[-1] = self.build.SOURCE / 'native/RuntimeIdentity.swift'
        with self.assertRaisesRegex(ValueError, 'actual55 RuntimeIdentity'):
            check.selected_production_sources(self.build, {})

    def test_old_main_cannot_replace_the_copy_picker(self):
        self.native[1] = self.build.SOURCE / 'src/main.m'
        with self.assertRaisesRegex(ValueError, 'exact54 native source selection'):
            check.selected_production_sources(self.build, {})

    def test_compatibility_module_cannot_be_omitted(self):
        self.native.pop()
        with self.assertRaisesRegex(ValueError, 'exact54 native source selection'):
            check.selected_production_sources(self.build, {})

    def test_duplicate_runtime_identity_is_rejected(self):
        self.swift.append(self.build.SOURCE / 'native/RuntimeIdentity.swift')
        with self.assertRaisesRegex(ValueError, 'actual55 RuntimeIdentity'):
            check.selected_production_sources(self.build, {})


class RuntimeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.identity = {'schema': 1, 'everestSourceCommit': check.EVEREST_COMMIT,
                         'compatibilityPolicy': 1,
                         'builtins': {'Celeste': '1.4.0.0', 'CelesteIOS': '1.0.0',
                                      'Everest': '1.6642.0', 'EverestCore': '1.6642.0'}}

    def test_current_version_and_source_commit_are_accepted(self):
        self.assertEqual(check.require_expected_identity(self.identity), self.identity)

    def test_stale_version_source_or_policy_is_rejected(self):
        stale = []
        for key, value in [('everestSourceCommit', '082e21b0b6dd7ff7c96d65b2ca2c632f4fd8df75'),
                           ('compatibilityPolicy', 2)]:
            identity = deepcopy(self.identity)
            identity[key] = value
            stale.append(identity)
        for module in ['Everest', 'EverestCore']:
            identity = deepcopy(self.identity)
            identity['builtins'][module] = '1.6580.0'
            stale.append(identity)
        for identity in stale:
            with self.subTest(identity=identity):
                with self.assertRaisesRegex(ValueError, 'actual build55 Everest1.6642'):
                    check.require_expected_identity(identity)


if __name__ == '__main__':
    unittest.main()
