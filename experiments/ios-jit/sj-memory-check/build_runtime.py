#!/usr/bin/env python3
"""Verify the immutable build 16 runtime; no runtime compilation or mutation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'.build/ios-jit/sj-budget-runtime/receipt.json';r=json.loads(p.read_text())
assert sha(ROOT/'experiments/ios-jit/sj-code-budget/build_runtime.py')==r['builder_sha256']
for t in r['targets'].values():
 assert sha(ROOT/t['archive'])==t['sha256']
 for name,h in t['source_sha256'].items():assert sha(Path(name))==h
print('PASS_REUSE_PHYSICALLY_ACCEPTED_BUILD16_RUNTIME')
