#!/usr/bin/env python3
"""Check the repair's scope and reject repeat application or changed provenance."""
import argparse,json,shutil,subprocess
from pathlib import Path
from save_transfer_inputs import validate_managed
from loading_inputs import ROOT, local, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--managed',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    source=local(a.managed);receipt,resources=validate_managed(source);work=local(a.work)
    assert ROOT/'.build' in work.parents and not work.exists();work.mkdir(parents=True)
    report=receipt['repair'];assert report['unchanged_method_bodies']==17300 and not report['mixed_after'] and not report['float_sinks_after']
    sdk=ROOT/'.private/loading-inputs/sdk8'
    command=[str(sdk/'dotnet'),str(source.parent/'Repair.dll'),str(resources/'Managed/Celeste.dll'),str(work/'twice.dll'),str(work/'twice.json')]
    r=subprocess.run(command,cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (work/'repeat.log').write_bytes(r.stdout)
    assert r.returncode and b'Unexpected historical precision sites' in r.stdout
    bad=dict(receipt,base_receipt_sha256='0'*64);(work/'receipt.json').write_text(json.dumps(bad))
    shutil.copyfile(source.parent/'repair.json',work/'repair.json')
    try:validate_managed(work/'receipt.json')
    except ValueError as e:assert str(e)=='Changed precision baseline'
    else:raise AssertionError('Changed baseline accepted')
    result=dict(status='PASS_PRECISION_REPAIR_CONTROLS',managed_receipt_sha256=sha(source),unchanged_method_bodies=report['unchanged_method_bodies'],fixed_arithmetic_sites=11,explicit_float_setter_boundaries=2,preserved_double_sites=10,checks=['exact four-method change set','zero known mixed arithmetic after repair','zero known double-to-float call/field boundaries after repair','ten intentional movement precision sites preserved','second application rejected','changed baseline receipt rejected'],source_sha256={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__))})
    (work/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
