#!/usr/bin/env python3
"""Check Cabrillo's file inventory, Git exclusions and locked migration inputs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    def git(*args, **kwargs):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, **kwargs)
    files = sorted(set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").stdout.decode().split("\0")) - {""})
    inventory = json.loads((ROOT / "docs/MIGRATION_FILE_INVENTORY.json").read_text())["files"]
    if set(files) != set(inventory):
        raise RuntimeError("Inventory mismatch: " + repr(sorted(set(files) ^ set(inventory))))
    for name in files:
        path, row = ROOT / name, inventory[name]
        if path.is_symlink() or not row.get("reason"):
            raise RuntimeError("Unjustified file or symlink: " + name)
        if row.get("sha256") and sha(path) != row["sha256"]:
            raise RuntimeError("Changed inventory file: " + name)
        if path.suffix.lower() in {".dll", ".exe", ".ipa", ".a", ".dylib", ".p12", ".p8", ".mobileprovision", ".bank", ".xnb", ".zip"}:
            raise RuntimeError("Unexpected binary, game or signing input in Git candidates: " + name)
        data = path.read_bytes()
        keys = [b"-----BEGIN " + kind + b" PRIVATE KEY-----" for kind in [b"RSA", b"EC", b"OPENSSH"]]
        keys.append(b"-----BEGIN " + b"PRIVATE KEY-----")
        if data.startswith((b"MZ", b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe")) or any(key in data for key in keys):
            raise RuntimeError("Unexpected binary or private key: " + name)
    for name in [".private/example.dll", ".build/example.o", "artifacts/example.ipa", "dist/example.ipa"]:
        if git("check-ignore", "-q", "--no-index", name).returncode:
            raise RuntimeError("Private/generated path is not ignored: " + name)
    metadata = json.loads((ROOT / ".private/migration/build28-replay.json").read_text())
    for name, digest in metadata["build"]["source_sha256"].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError("Delivered build28 source changed: " + name)
    for name, digest in metadata["native"]["source_sha256"].items():
        actual = ROOT / metadata["aliases"].get(name, name)
        if sha(actual) != digest:
            raise RuntimeError("Native or vendor source changed: " + name)
    private = json.loads((ROOT / ".private/migration/inputs.json").read_text())
    for name, row in private.items():
        if sha(ROOT / name) != row["sha256"]:
            raise RuntimeError("Pinned private input changed: " + name)
    for path in ROOT.rglob("*"):
        if path.is_symlink() and ROOT not in path.resolve().parents:
            raise RuntimeError("External symlink dependency: " + str(path))
    receipt = dict(status="PASS_CABRILLO_REPOSITORY_BOUNDARY", public_files=len(files), public_bytes=sum((ROOT / name).stat().st_size for name in files), locked_build_source_inputs=len(metadata["build"]["source_sha256"]), locked_native_source_inputs=len(metadata["native"]["source_sha256"]), private_input_files=len(private), private_input_bytes=sum(row["bytes"] for row in private.values()), head_exists=git("rev-parse", "--verify", "HEAD").returncode == 0, branch=git("symbolic-ref", "--short", "HEAD").stdout.decode().strip(), remotes=git("remote").stdout.decode().splitlines(), git_candidates_sha256=hashlib.sha256("\n".join(files).encode()).hexdigest())
    (ROOT / ".private/migration/repository-check.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
