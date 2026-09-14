#!/usr/bin/env python3
"""Stage exact original SJ archives and the accepted diagnostic code canary."""
import hashlib,json,shutil
from pathlib import Path
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[2];STAGE=ROOT/'.build/ios-jit/sj-lobby-mods';INPUT=ROOT/'.build/ios-jit/sj-lobby-inputs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 STAGE.mkdir(parents=True,exist_ok=True);prior=json.loads((INPUT/'receipt.json').read_text())
 for name,row in prior['files'].items():
  p=INPUT/name;assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'];shutil.copy2(p,STAGE/name)
 canary=ROOT/'artifacts/ios-jit/everest-canary-20260911-13/CJITCodeCanary-v1.0.0.zip'
 assert sha(canary)=='d30cc5b1d28d7821764fb18a35a182aa808cee56f4d0c4c778d9fa7bd4ef450b';shutil.copy2(canary,STAGE/canary.name)
 receipt=dict(schema=1,status='PASS_53_ORIGINAL_ZIPS_STAGED',files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(STAGE.glob('*.zip'))},original_helpers=prior,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),SOURCE/'fetch_sj.py',SOURCE/'sj-pins.json']},device_tested=False)
 (STAGE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
