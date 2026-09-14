#!/usr/bin/env python3
"""Download exact original release archives for private real-SJ testing."""
import concurrent.futures,hashlib,json,subprocess,zipfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[2];STAGE=ROOT/'.build/ios-jit/sj-lobby-inputs'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def fetch(row):
 name=row['name']+'-v'+row['resolvedVersion']+'.zip';path=STAGE/name
 if not path.exists():
  temp=path.with_suffix('.download')
  subprocess.run(['curl','--fail','--location','--silent','--show-error','--retry','2','--max-time','600',row['publicUrl'],'--output',str(temp)],check=True)
  assert temp.stat().st_size==row['zipBytes'] and digest(temp)==row['zipSha256'],name
  temp.replace(path)
 assert path.stat().st_size==row['zipBytes'] and digest(path)==row['zipSha256'],name
 with zipfile.ZipFile(path) as z:
  for dll in row['distributedDlls']:
   names=[n for n in z.namelist() if Path(n).name==Path(dll['path']).name]
   matches=[n for n in names if z.getinfo(n).file_size==dll['bytes'] and hashlib.sha256(z.read(n)).hexdigest()==dll['sha256']]
   assert matches,(name,dll['path'],names)
  manifests=[n for n in z.namelist() if Path(n).name.lower() in ['everest.yaml','everest.yml']]
  (STAGE/(row['name']+'.metadata.txt')).write_text('\n'.join(n+'\n'+z.read(n).decode('utf-8-sig') for n in manifests))
 print('VERIFIED',name,path.stat().st_size,flush=True)
 return name,dict(bytes=path.stat().st_size,sha256=digest(path),url=row['publicUrl'])
def main():
 STAGE.mkdir(parents=True,exist_ok=True);pins=json.loads((SOURCE/'sj-pins.json').read_text())
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:files=dict(pool.map(fetch,pins['nodes']))
 (STAGE/'receipt.json').write_text(json.dumps(dict(schema=1,status='PASS_52_ORIGINAL_SJ_ARCHIVES',pins_sha256=digest(SOURCE/'sj-pins.json'),files=files,total_bytes=sum(f['bytes'] for f in files.values())),indent=2)+'\n')
if __name__=='__main__':main()
