"""Controls for build isolation and rejecting misleading package identities."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_development import fresh_output, local_path
from verify_development_build import macho


class OutputBoundaryTests(unittest.TestCase):
    def test_new_work_and_output(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            self.assertEqual(fresh_output(".build/new", ".build", root), root / ".build/new")
            self.assertEqual(fresh_output("artifacts/new", "artifacts", root), root / "artifacts/new")

    def test_existing_and_wrong_category_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            (root / "artifacts/accepted").mkdir(parents=True)
            for path in ["artifacts/accepted", ".build/new", "experiments/new", "artifacts"]:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    fresh_output(path, "artifacts", root)

    def test_traversal_and_aliases_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            (root / "real").mkdir()
            (root / "alias").symlink_to(root / "real", target_is_directory=True)
            for path in ["../outside", "alias/file", "real/../other"]:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    local_path(path, root)


class MachOControls(unittest.TestCase):
    @staticmethod
    def image(extra=b"", platform=2, cpu=0x100000c):
        uuid = struct.pack("<II", 0x1b, 24) + bytes(range(16))
        build = struct.pack("<6I", 0x32, 24, platform, 0x1a0000, 0x1a0500, 0)
        commands = uuid + build + extra
        return struct.pack("<8I", 0xfeedfacf, cpu, 0, 2, 2 + bool(extra), len(commands), 0, 0) + commands

    def test_unsigned_ios_uuid(self):
        self.assertEqual(macho(self.image(), executable=True), bytes(range(16)).hex())

    def test_signature_simulator_wrong_cpu_and_duplicate_uuid_rejected(self):
        examples = [self.image(struct.pack("<4I", 0x1d, 16, 0, 0)),
                    self.image(platform=7), self.image(cpu=0x1000007),
                    self.image(struct.pack("<II", 0x1b, 24) + bytes(16))]
        for data in examples:
            with self.subTest(data=data.hex()), self.assertRaises(ValueError):
                macho(data, executable=True)

    def test_truncated_commands_rejected(self):
        for data in [b"", self.image()[:31], self.image()[:-1]]:
            with self.subTest(data=data.hex()), self.assertRaises(ValueError):
                macho(data, executable=True)


if __name__ == "__main__":
    unittest.main()
