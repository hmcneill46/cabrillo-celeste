#!/usr/bin/env python3
"""New native browser XCUITest, external fixtures plus live browsing appearance."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/launcher-catalogue-browser-ui';O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--device',required=True);p.add_argument('--only');a=p.parse_args()
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer');bundle='io.github.hmcneill46.celeste.everest.jit.everest'
def run(cmd):
 if cmd[0]=='xcodebuild':
  with (O/'xcode-live.log').open('w') as f:r=subprocess.run(cmd,env=env,text=True,stdout=f,stderr=subprocess.STDOUT)
  output=(O/'xcode-live.log').read_text()
 else:
  r=subprocess.run(cmd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);output=r.stdout
 with (O/'commands.log').open('a') as f:f.write(repr(cmd)+'\n'+output)
 if r.returncode:raise RuntimeError(output[-9000:])
 return output.strip()
subprocess.run(['xcrun','simctl','terminate',a.device,bundle],env=env,capture_output=True)
app=R/'artifacts/ios-jit/launcher-catalogue-20260913-28-simulator/CelesteJITEverest.app';run(['xcrun','simctl','install',a.device,str(app)])
container=Path(run(['xcrun','simctl','get_app_container',a.device,bundle,'data']))
f=container/'Documents/CatalogueFixtures';f.mkdir(parents=True,exist_ok=True)
fixtures=R/'.build/ios-jit/launcher-catalogue-install-tests/fixtures';candidates=json.loads((fixtures/'candidates.json').read_text())
install=container/'Documents/InstallerFixtures';install.mkdir(parents=True,exist_ok=True)
for source in fixtures.iterdir():shutil.copy2(source,install/source.name)
profile=container/'Documents/LauncherCatalogueUITestProfile'
if profile.exists():shutil.rmtree(profile)
cache=container/'Library/Caches/CelesteCatalogue/v1/simulator-fixture'
if cache.exists():shutil.rmtree(cache)
refs=R/'.build/ios-jit/launcher-catalogue-service'
for source,dest in [('community-categories.json','categories.yaml'),('community-subcategories.yaml','subcategories.yaml')]:shutil.copy2(refs/source,f/dest)
record=dict(PageURL='https://gamebanana.com/mods/900001',Name='Alpine paths',Author='Catalogue test fixture',CategoryName='Maps',SubcategoryName='Standalone',CategoryId='GameBanana_Mod_6800',SubcategoryId='GameBanana_Mod_6801',Description='A small climb with a few new friends.',Text='A native browser installation fixture.\nChoose the map file; required helpers will be included in the review. Unknown save sidecars are preserved.',Screenshots=[],Downloads=12430,Likes=152,Views=15340,CreatedDate=1789290000,UpdatedDate=1789290000,Files=[])
for name,id,title in [('root',900001,'Map pack'),('leaf-new',900003,'Optional extras')]:
 record['Files'].append(dict(ID='GameBanana/'+str(id),URL='https://gamebanana.com/mmdl/'+str(id),Name=name+'.zip',Description=title,Size=candidates[name]['bytes'],HasEverestYaml=True,IsLatestVersion=True,CreatedDate=1789290000))
rows=json.loads((refs/'community-downloads.json').read_text());rows[0]=record
(f/'list.json').write_text(json.dumps(rows));(f/'search.json').write_text(json.dumps([record]));shutil.copy2(refs/'community-page2.json',f/'page2.json')
detail=dict(_idRow=900001,_aGame={'_idRow':6460},_aSubmitter={'_sName':'Catalogue test fixture'},_sText=record['Text'],_aFiles=[{'_idRow':900001},{'_idRow':900003}],_nDownloadCount=12430,_nLikeCount=152,_nViewCount=15340,_tsDateUpdated=1789290000)
(f/'profile.json').write_text(json.dumps(detail))
prior=R/'.build/ios-jit/picker-ui-tests/Picker.xcodeproj';project=O/'Catalogue.xcodeproj';project.mkdir(exist_ok=True)
(project/'project.pbxproj').write_text((prior/'project.pbxproj').read_text().replace(str(R/'experiments/ios-jit/content-picker/tests/PickerUITests.swift'),str(S/'tests/CatalogueUITests.swift')).replace('Picker','Catalogue').replace('celeste.picker.uitests','celeste.catalogue.uitests'))
scheme=project/'xcshareddata/xcschemes';scheme.mkdir(parents=True,exist_ok=True)
(scheme/'CatalogueUITests.xcscheme').write_text((prior/'xcshareddata/xcschemes/PickerUITests.xcscheme').read_text().replace('Picker','Catalogue'))
result=O/'UITests.xcresult'
if result.exists():shutil.rmtree(result)
cmd=['xcodebuild','test','-project',str(project),'-scheme','CatalogueUITests','-destination','platform=iOS Simulator,id='+a.device,'-derivedDataPath',str(O/'DerivedData'),'-parallel-testing-enabled','NO','-maximum-concurrent-test-simulator-destinations','1','-resultBundlePath',str(result)]
cmd+=['-test-timeouts-enabled','YES','-default-test-execution-time-allowance','300','-maximum-test-execution-time-allowance','360']
if a.only:cmd+=['-only-testing:CatalogueUITests/CatalogueUITests/'+a.only]
output=run(cmd);(O/'run.log').write_text(output)
if a.only:print(output[-2000:]);raise SystemExit(0)
for flag in ['PASS_CATALOGUE_NATIVE_FILE_CHOICE_REVIEW_COMMIT_REPORT_REUSE','PASS_CATALOGUE_FILTERS_SORT_PAGINATION_SEARCH_CANCELLATION_EMPTY','PASS_CATALOGUE_OFFLINE_CACHE_FAILURE_DOES_NOT_LOCK_PLAY','PASS_LIVE_NATIVE_CATALOGUE_PORTRAIT_LANDSCAPE_DETAILS']:assert flag in output,flag
report=json.loads((profile/'LauncherReports/last-installation.json').read_text());assert report['outcome']=='completed' and len([x for x in report['changes'] if x['action']=='installed' and x['enabled']])==3
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'installed-report.json').write_text(json.dumps(report,indent=2))
(O/'receipt.json').write_text(json.dumps(dict(status='PASS_NATIVE_CATALOGUE_XCUITEST',source_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),S/'tests/CatalogueUITests.swift']},simulator_build_info_sha256=sha(app/'BuildInfo.json'),simulator_executable_sha256=sha(app/'CelesteJITEverest'),fixture_transport_excluded_from_device=True,live_appearance=True,results={'installed-report.json':sha(O/'installed-report.json'),'run.log':sha(O/'run.log')},command=cmd),indent=2)+'\n');print('PASS_NATIVE_CATALOGUE_XCUITEST')
