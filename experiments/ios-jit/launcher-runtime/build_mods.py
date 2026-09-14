#!/usr/bin/env python3
"""Read-only reuse of the accepted build19 dependency."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'.build/ios-jit/sj-lobby-mods '
P=Path(str(P).rstrip());r=json.loads((P/'receipt.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,row in r['files'].items():assert sha(P/name)==row['sha256']
print('PASS_ACCEPTED_READ_ONLY_REUSE',P)
