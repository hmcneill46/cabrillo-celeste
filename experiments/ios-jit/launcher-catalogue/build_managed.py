#!/usr/bin/env python3
"""Read-only verification of the exact physically accepted build27 managed payload."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=R/'.build/ios-jit/launcher-runtime-managed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((P/'receipt.json').read_text())
for name,digest in r['managed_sha256'].items(): assert sha(P/name)==digest,name
for name,digest in r['source_sha256'].items(): assert sha(R/name)==digest,name
assert sha(P/'CelesteJITEverest.dll')=='65b8dca51055627ad8a7da5fb59add7166cf9a39e435b7ac211d9c2df7a4f378'
assert r['runtime_identity']==json.loads((Path(__file__).parent/'RuntimeIdentity.json').read_text())
print('PASS_ACCEPTED_BUILD27_MANAGED_READ_ONLY',P)
