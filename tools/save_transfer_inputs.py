"""Validate the native save lane's explicitly derived managed dependency."""
import json
from loading_inputs import ROOT, local, sha, validate_managed as validate_loading
BASE_SHA='2c7392aa313865137c74cfd13bfb89168eb32d6e9da31421d88ec059581c26e4'
def validate_managed(receipt_path):
    path=local(receipt_path); receipt=json.loads(path.read_text())
    if receipt.get('status')=='PASS_LOADING_MANAGED_BUILD':
        if sha(path)!=BASE_SHA:raise ValueError('Unpinned baseline managed dependency')
        return validate_loading(path)
    if receipt.get('status')!='PASS_PLAYER_PRECISION_REPAIR_BUILD' or receipt.get('schema')!=1:raise ValueError('Unverified precision repair')
    base=local(receipt['base_receipt'])
    if sha(base)!=BASE_SHA or receipt['base_receipt_sha256']!=BASE_SHA:raise ValueError('Changed precision baseline')
    original,_=validate_loading(base)
    for name,digest in receipt['source_sha256'].items():
        if sha(local(name))!=digest:raise ValueError('Precision repair source changed: '+name)
    resources=local(receipt['resource_root'])
    if ROOT/'.build' not in resources.parents:raise ValueError('Managed stage must be private build output')
    files={str(f.relative_to(resources)):sha(local(f)) for f in resources.rglob('*') if f.is_file()}
    if files!=receipt['resources'] or files.keys()!=original['resources'].keys():raise ValueError('Changed derived managed payload')
    if {n for n in files if files[n]!=original['resources'][n]}!={'Managed/Celeste.dll'}:raise ValueError('Unrelated managed resource changed')
    repair=json.loads((path.parent/'repair.json').read_text())
    expected={'System.Void Celeste.PlayerHair::AfterUpdate()':1,'System.Void Celeste.PlayerSeeker::Update()':6,'System.Boolean Celeste.Player/<BirdDashTutorialCoroutine>d__561::MoveNext()':3,'System.Void Celeste.LavaRect::Resize(System.Single,System.Single,System.Int32)':3}
    if sha(path.parent/'repair.json')!=receipt['repair_sha256'] or repair!=receipt['repair'] or repair['changed_methods']!=expected or repair['preserved_double_precision_sites']!=10 or repair['mixed_after'] or repair['float_sinks_after']:raise ValueError('Changed precision repair contract')
    return receipt,resources
