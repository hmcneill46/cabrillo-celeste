#!/usr/bin/env python3
"""Production native planner, streamed hashes, transaction crash/recovery and installer tests."""
import hashlib,json,os,subprocess,sys,zipfile,shutil
from pathlib import Path
import xxhash,yaml
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-resolution-install-tests';N=R/'.build/ios-jit/launcher-resolution-native/host';D=R/'.build/ios-jit/launcher-resolution-native-dependencies';service=R/'.build/ios-jit/launcher-resolution-service/references'
O.mkdir(parents=True,exist_ok=True);F=O/'fixtures';F.mkdir(exist_ok=True)
for p in O.iterdir():
 if p.is_dir() and p.name!='fixtures' and p.name!='tests.dSYM':shutil.rmtree(p)
for p in O.glob('*.json'):p.unlink()
def mod(name,version,deps=[]):return dict(Name=name,Version=version,Dependencies=[dict(Name=n,Version=v) for n,v in deps])
metas={'root':[mod('Root','1.0',[('Helper','1.2')])],'helper-old':[mod('Helper','1.0')],'helper-new':[mod('Helper','1.3',[('Leaf','1.0')])],'leaf-new':[mod('Leaf','1.0')],'helper-repacked':[mod('Helper','1.0')]}
candidates={}
for key,modules in metas.items():
 p=F/(key+'.zip')
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  zi=zipfile.ZipInfo('everest.yaml',(2026,9,12,12,0,0));z.writestr(zi,yaml.safe_dump(modules,sort_keys=False))
  if key=='helper-repacked':z.writestr('readme.txt','Same version, different original archive.')
 data=p.read_bytes();candidates[key]=dict(url='https://mods.example.org/'+key+'.zip',bytes=len(data),hashes=[xxhash.xxh64(data).hexdigest()],pinnedSHA256=None,modules=[dict(name=m['Name'],version=m['Version'],dll=None,dependencies=[dict(name=d['Name'],version=d['Version']) for d in m['Dependencies']],optionalDependencies=[]) for m in modules])
(F/'candidates.json').write_text(json.dumps(candidates))
u={};g={}
for key in ['helper-new','leaf-new']:
 c=candidates[key];m=c['modules'][0];u[m['name']]={'Version':m['version'],'URL':c['url'],'Size':c['bytes'],'xxHash':c['hashes']};g[m['name']]={'URL':c['url'],'Dependencies':[{'Name':d['name'],'Version':d['version']} for d in m['dependencies']],'OptionalDependencies':[]}
(F/'index-updates.yaml').write_text(yaml.safe_dump(u));(F/'index-graph.yaml').write_text(yaml.safe_dump(g))
lengths=list(range(0,70))+[127,128,129,255,256,257,1023,4095,65535,65536,65537,1048577]
(F/'hash-vectors.json').write_text(json.dumps([dict(length=n,xxHash=xxhash.xxh64(bytes((i*131+(i>>3))&255 for i in range(n))).hexdigest()) for n in lengths]))
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
cmd=['xcrun','swiftc','-swift-version','5','-O','-g','-I',str(N),'-I',str(D/'Yams/Sources/CYaml/include'),*map(str,sorted((S/'native').glob('*.swift'))),str(S/'tests/InstallTests.swift'),str(N/'libZIPFoundation.a'),str(N/'libCYaml.a'),'-o',str(O/'tests')]
p=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(O/'compile.log').write_text(p.stdout)
if p.returncode:print(p.stdout[-12000:]);sys.exit(p.returncode)
def run(*args,expected=0):
 p=subprocess.run([str(O/'tests'),str(args[0]),str(O),*map(str,args[1:])],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
 (O/('-'.join(str(a).replace('/','_') for a in args[:2])+'.log')).write_text(p.stdout)
 if p.returncode!=expected:raise RuntimeError(str(args)+'\n'+p.stdout[-10000:])
 print(args[0],p.returncode,flush=True)
corpus=O/'corpus/Mods';corpus.mkdir(parents=True)
for p in (R/'.build/ios-jit/sj-lobby-mods').glob('*.zip'):os.link(p,corpus/p.name)
run('pure',service,S/'CompatibilityDownloads.json',corpus.parent)
run('engine')
run('automatic')
run('blocked')
crashes=[]
for fault in ['journal','file:0','file:1','state','throw:file:0','throw:state','tamper','stale','success']:
 name='journal-'+fault.replace(':','-');run('journal',name,fault,expected=75 if fault in ['journal','file:0','file:1','state'] else 0)
 run('recover',name)
 p=O/name;mods=p/'Mods';state=json.loads((p/'launcher-mod-state.json').read_text());files=sorted(f.name for f in mods.glob('*.zip'))
 assert (p/'unknown.save.dat').read_text()=='complete mod save and unknown sidecar'
 for f in ['root.zip','helper-old.zip']:assert (mods/f).read_bytes()==(F/f).read_bytes()
 committed=fault in ['state','success'];assert len(files)==(4 if committed else 2),(fault,files)
 if committed:assert state['disabled']==['helper-old.zip']
 elif fault!='stale':assert state['disabled']==[]
 receipts=json.loads((O/(name+'-recovery.json')).read_text())['diagnostics'];crashes.append(dict(fault=fault,committed=committed,files=files,diagnostics=receipts))
(O/'crash-recovery.json').write_text(json.dumps(dict(status='PASS_JOURNAL_PROCESS_CRASH_AND_ROLLBACK',cases=crashes),indent=2)+'\n')
unknown=[]
for change in ['installed-file','state','journal-path']:
 name='unknown-'+change;run('journal',name,'file:0',expected=75);profile=O/name
 jp=next((profile/'LauncherInstalls').glob('*.json'));j=json.loads(jp.read_text())
 if change=='installed-file':target=profile/'Mods'/j['files'][0]['filename'];target.write_bytes(b'unknown changed bytes')
 elif change=='state':target=profile/'launcher-mod-state.json';target.write_text('{"schema":1,"disabled":["owner-choice.zip"]}')
 else:
  target=jp;j['files'][0]['filename']='../outside.zip';jp.write_text(json.dumps(j))
 before=target.read_bytes();run('recover-fails',name)
 assert target.read_bytes()==before
 for f in ['root.zip','helper-old.zip']:assert (profile/'Mods'/f).read_bytes()==(F/f).read_bytes()
 unknown.append(change)
(O/'unknown-changes.json').write_text(json.dumps(dict(status='PASS_RECOVERY_PRESERVES_UNKNOWN_CHANGES',cases=unknown),indent=2)+'\n')
real=O/'real-memorialHelper.zip'
if real.exists():real.unlink()
run('network',service)
source={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((S/'native').glob('*.swift'))+ [Path(__file__),S/'tests/InstallTests.swift',S/'CompatibilityDownloads.json',S/'RuntimeCompatibleReleases.json']}
(O/'receipt.json').write_text(json.dumps(dict(status='PASS_NATIVE_INSTALLS_AND_UPDATES',source_sha256=source,results={f:hashlib.sha256((O/f).read_bytes()).hexdigest() for f in ['pure.json','engine.json','automatic.json','blocked.json','crash-recovery.json','unknown-changes.json','network.json']},commands=[cmd]),indent=2)+'\n');print('PASS_NATIVE_INSTALLS_AND_UPDATES')
