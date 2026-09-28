#!/usr/bin/env python3
"""Fresh source recipe. Public mode requires approved FMOD distribution inputs.

Use --fmod-sdk only for an explicitly private local build from a licensed SDK.
No Celeste input or historical Cabrillo capsule is accepted by this recipe.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path
from compile_owned_game import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True);p.add_argument('--output',required=True)
    p.add_argument('--fmod-sdk',help='Explicit SDK directory for a private local build; never a public release')
    a=p.parse_args(); config=json.loads((ROOT/'release/current.json').read_text())
    distribution=config.get('fmod_distribution',{})
    if not a.fmod_sdk:
        if not (config.get('public_ipa_ready') is True and distribution.get('approved') is True
                and str(distribution.get('permission_reference','')).strip()
                and str(distribution.get('sdk_zip_url','')).startswith('https://')
                and len(distribution.get('sdk_zip_sha256',''))==64):
            raise ValueError('FMOD redistribution is not approved or its authorized CI SDK input is not configured. Public IPA output remains blocked.')
    work=(ROOT/a.work).absolute();output=(ROOT/a.output).absolute()
    for path in [work,output]:
        if path.resolve()!=path or ROOT/'.build' not in path.parents: raise ValueError('Use unaliased .build paths')
    if work.exists() or output.exists(): raise ValueError('Choose fresh output paths')
    work.mkdir(parents=True)
    def run(tool,*arguments): subprocess.run([sys.executable,str(ROOT/'tools'/tool),*map(str,arguments)],cwd=ROOT,check=True)
    inputs=work/'inputs'; managed=work/'managed'; native=work/'native'; fmod=work/'fmod'
    run('prepare_owned_public.py','--work',inputs,'--cache',ROOT/'.build/public-download-cache')
    run('build_owned_managed.py','--inputs',inputs,'--work',managed)
    run('build_owned_native.py','--inputs',inputs,'--work',native)
    if a.fmod_sdk: sdk=Path(a.fmod_sdk).resolve()
    else:
        archive=work/'fmod-sdk.zip'
        with urllib.request.urlopen(distribution['sdk_zip_url'],timeout=120) as response,archive.open('xb') as stream: shutil.copyfileobj(response,stream)
        if sha(archive)!=distribution['sdk_zip_sha256']: raise ValueError('Authorized FMOD SDK checksum differs')
        sdk=work/'fmod-sdk'
        with zipfile.ZipFile(archive) as z:
            for i in z.infolist():
                if Path(i.filename).is_absolute() or '..' in Path(i.filename).parts or '\\' in i.filename or (i.external_attr>>16)&0o170000==0o120000:
                    raise ValueError('Unsafe SDK archive member')
            z.extractall(sdk)
        if not (sdk/'api/lowlevel/lib/libfmod_iphoneos.a').is_file(): raise ValueError('SDK ZIP must contain api/ and doc/ at its root')
    run('prepare_owned_fmod.py','--sdk',sdk,'--native',native/'receipt.json','--work',fmod)
    artifacts=ROOT/'artifacts'/('source-'+work.name)
    run('build_owned_game.py','--managed',managed/'receipt.json','--native',native/'receipt.json','--fmod',fmod/'receipt.json',
        '--work',work/'app','--output',artifacts)
    r=json.loads((artifacts/'build-receipt.json').read_text());output.mkdir(parents=True)
    shutil.copyfile(artifacts/r['ipa'],output/'Cabrillo.ipa')
    dependencies=[];lock=json.loads((inputs/'receipt.json').read_text())['dependencies']
    cache=ROOT/'.build/public-download-cache'
    for name,row in lock.items():
        archive=cache/(name+'.archive')
        dependencies.append(dict(name=name,kind='binary' if name.startswith(('sdk','mono-')) else 'source',url=row['url'],
            sha256=sha(archive),license='Upstream license and component notices included in the app licenses directory.'))
    for name,digest in json.loads((managed/'receipt.json').read_text())['nuget_packages'].items():
        package,version,filename=name.split('/')
        dependencies.append(dict(name=package+'/'+version,kind='binary',url='https://api.nuget.org/v3-flatcontainer/'+name,
            sha256=digest,license='Exact package license expression and available texts in licenses/nuget-packages.json.'))
    fmod_receipt=json.loads((fmod/'receipt.json').read_text())
    dependencies.append(dict(name='FMOD Engine iOS 1.10.09',kind='binary',url=distribution.get('sdk_zip_url') or 'https://www.fmod.com/download',
        sha256=sha(work/'fmod-sdk.zip') if not a.fmod_sdk else fmod_receipt['sdk_input_sha256']['lowLevel'],
        license=distribution.get('permission_reference') or 'User-supplied SDK; private test only; public redistribution blocked.'))
    provenance=dict(schema=1,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        private_inputs_used=bool(a.fmod_sdk),private_capsule_used=False,game_inputs_used=False,dependencies=dependencies,
        package_receipt_sha256=sha(artifacts/'build-receipt.json'),payload_audit_sha256=sha(artifacts/'payload-audit.json'))
    (output/'BUILD_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (output/'RELEASE_NOTES.md').write_text('# Cabrillo '+config['version']+'\n\nImport your original Celeste FNA 1.4.0.0 ZIP and enable JIT. The first launch prepares your copy; later launches reuse the verified cache. No Celeste game code or assets are bundled.\n\n'+('Private local test. FMOD redistribution is not approved.\n' if a.fmod_sdk else 'FMOD is a declared licensed binary dependency. See the included permissions and notices.\n'))
    print('PASS_PRIVATE_SOURCE_BUILD' if a.fmod_sdk else 'PASS_PUBLIC_SOURCE_BUILD')
if __name__=='__main__':main()
