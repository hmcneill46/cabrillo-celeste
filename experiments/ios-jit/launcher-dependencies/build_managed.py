#!/usr/bin/env python3
"""Verify the exact accepted build24 managed payload without rebuilding it."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'.build/ios-jit/launcher-backbuffer-managed'
r=json.loads((P/'receipt.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in r['managed_sha256'].items():assert sha(P/name)==digest,name
for name,digest in r['source_sha256'].items():assert sha(R/name)==digest,name
assert sha(P/'CelesteJITEverest.dll')=='97d6484545e464a1e6953a9a162ca11d3395a37a1cb797b26e6ae49d3dffea9f'
assert sha(P/'FNA.dll')=='7a7c416101b17c2f5c2c6602bcaf5b8daad7395ee63ca9fc74f9034fb9f239ff'
print('PASS_ACCEPTED_BUILD24_MANAGED_READ_ONLY',P)
