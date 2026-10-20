"""The active unsigned59 trial must reject a valid-looking58 or mixed kit."""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_pipeline as pipeline
from build_stikjit57 import COMMIT, ARCHIVE_SHA256, lock_value
import test_integrated57_package as retained


class Release59PipelineChecks(unittest.TestCase):
    def test_active59_is_ready_and_old58_cannot_replace_the_recipe(self):
        config, report = pipeline.readiness(pipeline.ROOT)
        self.assertEqual((config['version'], config['build_number']), ('0.29.1', '59'))
        self.assertEqual(report['status'], 'READY')
        self.assertFalse(report['physical_device_tested'])
        with patch.object(pipeline, 'CONFIG', 'release/public58.json'):
            with self.assertRaisesRegex(ValueError, 'fresh public source recipe'):
                pipeline.readiness(pipeline.ROOT)

    def test_existing_trial_branch_still_cannot_publish(self):
        self.assertEqual(pipeline.release_ref('refs/heads/codex/actions-release', '0.29.1', False), '')
        with self.assertRaises(ValueError):
            pipeline.release_ref('refs/heads/codex/actions-release', '0.29.1', True)

    @staticmethod
    def fixture(root, host_build='59', helper_build='59', metadata_build='59', provenance_build='59', extra=None):
        parts = copy.deepcopy(retained.IntegratedPackageChecks().parts())
        host, info, binary, helper, helper_binary, framework, framework_binary, lock = parts
        host.update(CFBundleVersion=host_build, CFBundleShortVersionString='0.29.1', CFBundleExecutable='CelesteJITEverest')
        helper.update(CFBundleVersion=helper_build, CFBundleShortVersionString='0.29.1')
        info.update(version='0.29.1', build_number=metadata_build)
        # Add the UUID required by the real public IPA verifier to the synthetic
        # Mach-O header. The fixture never executes these bytes.
        header = list(struct.unpack('<8I', binary[:32]))
        header[4] += 1
        header[5] += 24
        binary = struct.pack('<8I', *header) + binary[32:] + struct.pack('<II', 0x1b, 24) + bytes(range(1, 17))
        components = {'StikJIT.framework/StikJIT': framework_binary,
                      'StikJIT.framework/Info.plist': plistlib.dumps(framework),
                      'StikJIT.framework/universal.js': b'synthetic script fixture',
                      'StikJIT.framework/legacy.js': b'synthetic legacy fixture',
                      'CabrilloJITHelper.appex/CabrilloJITHelper': helper_binary,
                      'CabrilloJITHelper.appex/Info.plist': plistlib.dumps(helper)}
        files = {'Info.plist': plistlib.dumps(host), 'BuildInfo.json': json.dumps(info).encode(),
                 'CelesteJITEverest': binary, 'licenses/StikJIT/UPSTREAM.json': json.dumps(lock).encode()}
        files.update({('Frameworks/' if n.startswith('StikJIT.framework/') else 'PlugIns/') + n: data
                      for n, data in components.items()})
        if extra:
            files[extra] = b'synthetic unapproved component'
        ipa = root / 'Cabrillo-0.29.1-unsigned.ipa'
        with zipfile.ZipFile(ipa, 'w') as archive:
            for name, data in files.items():
                archive.writestr('Payload/CelesteJITEverest.app/' + name, data)
        provenance = dict(version='0.29.1', build_number=provenance_build,
            ipa_sha256=hashlib.sha256(ipa.read_bytes()).hexdigest(),
            integrated_jit=dict(upstream_commit=COMMIT, archive_sha256=ARCHIVE_SHA256,
                bundled_idevice_ffi=lock_value()['bundled_idevice_ffi'], framework_linked_into_host=False,
                helper_minimum_ios='17.4', physical_device_tested=False,
                helper_files={name: hashlib.sha256(data).hexdigest() for name, data in components.items()}),
            dependencies=[dict(name='StikJIT/' + COMMIT, kind='mixed', sha256=ARCHIVE_SHA256),
                          dict(name='StikJIT/idevice-ffi', kind='binary', sha256=lock['bundled_idevice_ffi']['sha256'])])
        (root / 'BUILD_PROVENANCE.json').write_text(json.dumps(provenance))
        return ipa

    def test_valid_synthetic59_kit_passes_real_identity_and_component_parsers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            pipeline.verify_integrated_kit(root, '0.29.1')

    def test_mixed_host_helper_metadata_and_provenance_builds_are_rejected(self):
        changes = [(dict(host_build='58'), 'IPA identity'),
                   (dict(helper_build='58'), 'Helper extension identity'),
                   (dict(metadata_build='58'), 'app metadata'),
                   (dict(provenance_build='58'), 'provenance does not identify')]
        for change, message in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.fixture(root, **change)
                with self.assertRaisesRegex(ValueError, message):
                    pipeline.verify_integrated_kit(root, '0.29.1')

    def test_changed_ipa_and_extra_embedded_component_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ipa = self.fixture(root)
            ipa.write_bytes(ipa.read_bytes() + b'changed after sealing')
            with self.assertRaisesRegex(ValueError, 'IPA differs from its provenance'):
                pipeline.verify_integrated_kit(root, '0.29.1')
            self.fixture(root, extra='PlugIns/Unapproved.appex/binary')
            with self.assertRaisesRegex(ValueError, 'package members'):
                pipeline.verify_integrated_kit(root, '0.29.1')

    def test_old_version_request_is_rejected_before_reading_a_kit(self):
        with self.assertRaisesRegex(ValueError, 'requires build59'):
            pipeline.verify_integrated_kit(Path('/nonexistent-synthetic-kit'), '0.29.0')


if __name__ == '__main__':
    unittest.main()
