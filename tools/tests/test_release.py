"""Release controls: blocked packaging, tag identity and unsafe artifacts cannot publish."""
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import BUNDLE_ID, ROOT, preflight, readiness, validate_ref, verify_ipa, verify_provenance
from ci.check_public_repository import audit


class ReleaseControls(unittest.TestCase):
    def test_current_private_build_is_blocked(self):
        _, result = readiness(ROOT)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertFalse(result['public_ipa_publishing_allowed'])
        self.assertGreaterEqual(len(result['blockers']), 3)
        with self.assertRaisesRegex(ValueError, 'Public IPA release is blocked'):
            preflight(ROOT, 'refs/tags/v' + result['version'])

    def test_branch_wrong_version_and_injected_refs_rejected(self):
        for ref in ['refs/heads/main', 'v0.21.0', 'refs/tags/v0.20.0',
                    'refs/tags/v0.21.0\nextra=1', 'refs/tags/v0.21.0;exit 0']:
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                validate_ref(ref, '0.21.0')
        self.assertEqual(validate_ref('refs/tags/v0.21.0', '0.21.0'), 'v0.21.0')
        self.assertEqual(validate_ref('refs/tags/v0.21.0-rc.1', '0.21.0'), 'v0.21.0-rc.1')

    def test_ready_release_requires_clean_checkout_at_tagged_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()

            def git(*args):
                return subprocess.check_output(['git', '-c', 'user.name=CI fixture',
                    '-c', 'user.email=fixture@example.invalid', *args], cwd=root, text=True).strip()

            git('init', '-q')
            for folder in ['release', 'lane', 'tools']:
                (root / folder).mkdir()
            identity = dict(version='0.21.0', build_number='38')
            (root / 'lane/BuildIdentity.json').write_text(json.dumps(identity))
            (root / 'tools/build_public_release.py').write_text('# synthetic tag-gate fixture\n')
            (root / 'release/current.json').write_text(json.dumps(dict(schema=1, lane='lane',
                **identity, public_ipa_ready=True, blockers=[],
                public_build_script='tools/build_public_release.py')))
            git('add', '.')
            git('commit', '-qm', 'Synthetic public recipe')
            git('tag', 'v0.21.0')
            self.assertEqual(preflight(root, 'refs/tags/v0.21.0')[1]['source_commit'], git('rev-parse', 'HEAD'))
            (root / 'tools/build_public_release.py').write_text('# changed fixture\n')
            with self.assertRaisesRegex(ValueError, 'clean public checkout'):
                preflight(root, 'refs/tags/v0.21.0')
            git('commit', '-qam', 'Different commit')
            with self.assertRaisesRegex(ValueError, 'differs from the version tag'):
                preflight(root, 'refs/tags/v0.21.0')

    def test_ready_flag_alone_cannot_unlock_private_builder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'release').mkdir()
            (root / 'lane').mkdir()
            identity = dict(version='0.21.0', build_number='38')
            (root / 'lane/BuildIdentity.json').write_text(json.dumps(identity))
            config = dict(schema=1, lane='lane', **identity, public_ipa_ready=True,
                          public_build_script='tools/build_everest6580.py', blockers=[])
            (root / 'release/current.json').write_text(json.dumps(config))
            self.assertFalse(readiness(root)[1]['public_ipa_publishing_allowed'])
            config['public_build_script'] = 'tools/build_public_release.py'
            (root / 'release/current.json').write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, 'Missing, private or aliased'):
                readiness(root)

    @staticmethod
    def executable(platform=2, signed=False):
        commands = struct.pack('<II', 0x1b, 24) + bytes(range(16))
        commands += struct.pack('<6I', 0x32, 24, platform, 0xf0000, 0x1a0500, 0)
        if signed:
            commands += struct.pack('<4I', 0x1d, 16, 0, 0)
        return struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 2, 2 + signed, len(commands), 0, 0) + commands

    def make_ipa(self, path, extra=None, version='0.21.0', platform=2, signed=False):
        info = dict(CFBundleIdentifier=BUNDLE_ID, CFBundleVersion='38',
                    CFBundleShortVersionString=version, CFBundleExecutable='Cabrillo')
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('Payload/Cabrillo.app/Info.plist', plistlib.dumps(info))
            z.writestr('Payload/Cabrillo.app/Cabrillo', self.executable(platform, signed))
            if extra:
                z.writestr(extra, 'fixture')

    def test_package_rejects_game_signing_material_and_path_tricks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.ipa'
            self.make_ipa(path)
            verify_ipa(path, '0.21.0', '38')
            for extra in ['Payload/Cabrillo.app/Managed/Celeste.dll',
                          'Payload/Cabrillo.app/Managed/Celeste.Content.dll',
                          'Payload/Cabrillo.app/embedded.mobileprovision',
                          'Payload/Cabrillo.app/Content/test.bank',
                          'Payload/Cabrillo.app/_CodeSignature/CodeResources',
                          'Payload/Cabrillo.app/../outside', '/outside',
                          'Payload/Cabrillo.app/info.plist']:
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    self.make_ipa(path, extra)
                    verify_ipa(path, '0.21.0', '38')

    def test_package_rejects_wrong_version_simulator_and_signed_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.ipa'
            for kwargs in [dict(version='0.20.0'), dict(platform=7), dict(signed=True)]:
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    self.make_ipa(path, **kwargs)
                    verify_ipa(path, '0.21.0', '38')

    def test_provenance_binds_commit_and_discloses_binary_dependencies(self):
        revision = 'a' * 40
        data = dict(schema=1, source_commit=revision, private_inputs_used=False,
                    dependencies=[dict(name='fixture', kind='binary', license='example permission',
                                       sha256='b' * 64, url='https://example.invalid/fixture')])
        verify_provenance(data, revision)
        for update in [dict(source_commit='c' * 40), dict(private_inputs_used=True),
                       dict(dependencies=[]), dict(dependencies=[dict(name='undisclosed')])]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                verify_provenance(dict(data, **update), revision)


class PublicCheckoutControls(unittest.TestCase):
    def test_public_audit_works_without_private_capsule_and_rejects_leaks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'docs').mkdir()
            (root / '.gitignore').write_text('.private/\n.build/\nartifacts/\ndist/\n')
            (root / 'main.py').write_text('print("public fixture")\n')
            inventory = root / 'docs/MIGRATION_FILE_INVENTORY.json'

            def refresh(names):
                entries = {n: dict(reason='test input', bytes=(root / n).stat().st_size,
                                  sha256=hashlib.sha256((root / n).read_bytes()).hexdigest()) for n in names}
                entries['docs/MIGRATION_FILE_INVENTORY.json'] = dict(reason='self', self_describing=True)
                inventory.write_text(json.dumps(dict(files=entries)))

            refresh(['.gitignore', 'main.py'])
            self.assertEqual(audit(root)['status'], 'PASS_PUBLIC_SOURCE_CHECKOUT')
            (root / 'main.py').write_text('print("changed")\n')
            with self.assertRaisesRegex(ValueError, 'hash/size mismatch'):
                audit(root)
            (root / '.private').mkdir()
            (root / '.private/log.txt').write_text('private fixture')
            subprocess.run(['git', 'add', '-f', '.private/log.txt'], cwd=root, check=True)
            refresh(['.gitignore', 'main.py', '.private/log.txt'])
            with self.assertRaisesRegex(ValueError, 'Private/generated directory'):
                audit(root)


if __name__ == '__main__':
    unittest.main()
