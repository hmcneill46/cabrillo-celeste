"""Public release boundaries, credential-free PR checks and signed document controls."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_pipeline import ROOT, readiness, release_ref, verify_kit, verify_provenance, kit_names
from verify_release_shortcuts import check_contents, check_members
from build_shortcut_files49 import generate
from fetch_fmod_sdk import ARCHIVE_SHA256


class PublicReleaseControls(unittest.TestCase):
    def test_new_recipe_is_ready_while_historical_manifest_stays_blocked(self):
        self.assertEqual(readiness(ROOT)[1]['status'], 'READY')
        legacy = json.loads((ROOT / 'release/current.json').read_text())
        self.assertEqual(legacy['build_number'], '38')
        self.assertFalse(legacy['public_ipa_ready'])

    def test_manual_branch_build_cannot_publish(self):
        self.assertEqual(release_ref('refs/heads/main', '0.24.0', False), '')
        for ref in ['refs/heads/main', 'refs/heads/codex/actions-release', 'refs/pull/4/merge',
                    'refs/tags/v0.23.2', 'refs/tags/v0.24.0\nextra=true']:
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                release_ref(ref, '0.24.0', True)
        for ref in ['refs/pull/4/merge', 'refs/heads/untrusted']:
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                release_ref(ref, '0.24.0', False)
        self.assertEqual(release_ref('refs/tags/v0.24.0-rc.1', '0.24.0', True), 'v0.24.0-rc.1')

    @staticmethod
    def provenance():
        return dict(schema=2, source_commit='a' * 40, game_inputs_used=False,
            private_capsule_used=False, prebuilt_app_used=False, bit_reproducibility_claimed=False,
            licensed_inputs_used=['FMOD Engine iOS 1.10.09'], fmod_acquisition='official-authenticated-download',
            fmod_installer_sha256=ARCHIVE_SHA256,
            dependencies=[dict(name='FMOD 1.10.09/' + kind, kind='licensed-binary',
                url='https://www.fmod.com/download', sha256='b' * 64,
                license='runtime-only permission', sdk_redistribution_permitted=False)
                for kind in ['lowLevel', 'studio']],
            shortcut_verification=dict(status='PASS_SIGNED_SHORTCUT_SOURCE_MATCH',
                signatures_verified=True, actions_match_generated_source=True))

    def test_licensed_input_is_disclosed_without_allowing_game_or_capsule(self):
        value = self.provenance()
        verify_provenance(value, 'a' * 40, True)
        for update in [dict(source_commit='c' * 40), dict(game_inputs_used=True),
                       dict(private_capsule_used=True), dict(prebuilt_app_used=True),
                       dict(licensed_inputs_used=[]), dict(fmod_installer_sha256='d' * 64),
                       dict(fmod_acquisition='developer-supplied-sdk'), dict(dependencies=[]),
                       dict(shortcut_verification={}), dict(bit_reproducibility_claimed=True)]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                verify_provenance(dict(value, **update), 'a' * 40, True)

    def test_public_dependency_metadata_cannot_carry_signed_urls_or_sdk_permission(self):
        for change in [dict(url='https://example.invalid/file?token=fixture'),
                       dict(url='https://user:fixture@example.invalid/file'),
                       dict(kind='source'), dict(sdk_redistribution_permitted=True)]:
            value = self.provenance()
            value['dependencies'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_provenance(value, 'a' * 40, True)

    def test_kit_rejects_extra_files_and_incomplete_or_changed_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            expected = kit_names('0.24.0') - {'SHA256SUMS'}
            for name in expected:
                (root / name).write_text('synthetic release artifact')
            rows = ''.join(hashlib.sha256((root / name).read_bytes()).hexdigest() + '  ' + name + '\n'
                           for name in sorted(expected))
            (root / 'SHA256SUMS').write_text(rows)
            verify_kit(root, '0.24.0')
            for name in ['fmod-sdk.dmg', 'libfmod.a', 'build.log', '.credentials']:
                (root / name).write_text('synthetic unapproved input')
                with self.subTest(name=name), self.assertRaises(ValueError):
                    verify_kit(root, '0.24.0')
                (root / name).unlink()
            (root / 'SHA256SUMS').write_text(rows.splitlines()[0] + '\n')
            with self.assertRaises(ValueError):
                verify_kit(root, '0.24.0')
            (root / 'SHA256SUMS').write_text(rows)
            (root / 'BUILD_PROVENANCE.json').write_text('changed artifact')
            with self.assertRaises(ValueError):
                verify_kit(root, '0.24.0')


class SignedShortcutControls(unittest.TestCase):
    def test_apple_metadata_adjustments_do_not_hide_action_or_connection_changes(self):
        expected = generate('livecontainer')
        signed = copy.deepcopy(expected)
        signed.pop('WFWorkflowName')
        signed['WFWorkflowClientVersion'] = '4711'
        check_contents(signed, expected)
        for transform in [lambda x: x['WFWorkflowActions'].pop(),
                          lambda x: x['WFWorkflowActions'].reverse(),
                          lambda x: x['WFWorkflowActions'][0].update(WFWorkflowActionIdentifier='unreviewed'),
                          lambda x: x.update(WFWorkflowClientVersion='unknown')]:
            altered = copy.deepcopy(signed)
            transform(altered)
            with self.assertRaises(ValueError):
                check_contents(altered, expected)

    def test_archive_member_validation_rejects_traversal_links_and_extras(self):
        members = [dict(TYP='D', PAT=''), dict(TYP='F', PAT='Shortcut.wflow', DAT=6535)]
        check_members(members)
        for row in [dict(TYP='F', PAT='../outside', DAT=6535),
                    dict(TYP='L', PAT='Shortcut.wflow', DAT=6535),
                    dict(TYP='F', PAT='Shortcut.wflow', DAT=1000000)]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                check_members([members[0], row])
        with self.assertRaises(ValueError):
            check_members(members + [dict(TYP='F', PAT='extra', DAT=5)])


if __name__ == '__main__':
    unittest.main()
