#!/usr/bin/env python3
"""Read-only verification of the seven unchanged build17 ZIPs."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'.build/ios-jit/sj-gravity-mods'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((S/'receipt.json').read_text())
assert len(r['files'])==7
assert all(sha(S/n)==v['sha256'] and (S/n).stat().st_size==v['bytes'] for n,v in r['files'].items())
print('PASS_REUSE_SEVEN_UNCHANGED_BUILD17_MOD_ZIPS')
