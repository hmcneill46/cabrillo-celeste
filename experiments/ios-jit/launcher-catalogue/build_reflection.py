#!/usr/bin/env python3
"""Read-only reuse of the physically accepted build26 CoreLib correction."""
import hashlib, json
from pathlib import Path
R = Path(__file__).resolve().parents[3]
P = R / '.build/ios-jit/launcher-resolution-reflection'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
r = json.loads((P / 'receipt.json').read_text())
assert sha(P / 'receipt.json') == '6cf61c1e74f1b50706d64447ab25600f77c7b4ddfdeb08e3c960f65236c68a91'
for name, digest in r['source_sha256'].items(): assert sha(R / name) == digest
for v in r['targets'].values():
    assert sha(R / v['input']) == v['input_sha256']
    assert sha(R / v['output']) == v['output_sha256']
print('PASS_ACCEPTED_BUILD26_REFLECTION_READ_ONLY')
