"""Host-specific dependency pinning must retain the complete package boundary."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_release_nuget import ROOT, HOST_X64, HOST_ARM64, expected_packages, verify_packages


class NuGetHostControls(unittest.TestCase):
    def test_original_intel_lock_and_single_pinned_arm_replacement(self):
        original = json.loads((ROOT / 'release/owned-game-nuget.json').read_text())['packages']
        verify_packages(original, 'x64')
        arm = dict(original)
        del arm[HOST_X64]
        arm[HOST_ARM64] = '49096459ff377750e1e3c6572374053a8c4468b013d3f1ed3334d08594b1e4d9'
        verify_packages(arm, 'arm64')
        self.assertEqual(len(original), len(arm))

    def test_wrong_host_is_rejected(self):
        for actual, arch in [('x64', 'arm64'), ('arm64', 'x64')]:
            with self.subTest(arch=arch), self.assertRaisesRegex(ValueError, 'NuGet lock mismatch'):
                verify_packages(expected_packages(actual), arch)

    def test_changes_missing_packages_and_additions_are_rejected(self):
        for arch in ['x64', 'arm64']:
            for change in ['missing', 'extra', 'changed', 'host_changed']:
                actual = expected_packages(arch)
                common = next(k for k in actual if 'microsoft.netcore.app.host.osx-' not in k)
                if change == 'missing':
                    del actual[common]
                elif change == 'extra':
                    actual['unreviewed/1.0/unreviewed.1.0.nupkg'] = 'a' * 64
                else:
                    key = (HOST_X64 if arch == 'x64' else HOST_ARM64) if change == 'host_changed' else common
                    actual[key] = 'b' * 64
                with self.subTest(arch=arch, change=change), self.assertRaises(ValueError):
                    verify_packages(actual, arch)

    def test_unknown_architecture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            expected_packages('unknown')
