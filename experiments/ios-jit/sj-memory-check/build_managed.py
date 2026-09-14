#!/usr/bin/env python3
"""Read-only verification of the reused build17 managed payload."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'.build/ios-jit/sj-gravity-managed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((S/'receipt.json').read_text())
assert all(sha(S/n)==h for n,h in r['managed_sha256'].items())
assert all(sha(R/n)==h for n,h in r['source_sha256'].items())
print('PASS_REUSE_EXACT_BUILD17_MANAGED_PAYLOAD')
