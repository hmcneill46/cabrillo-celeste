#!/usr/bin/env python3
"""Isolate a scoped lazy-beforefieldinit policy in copies of accepted Mono."""
import collections,difflib,hashlib,importlib.util,json,os,shlex,shutil,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[2];RUNTIME=ROOT/'.build/ios-jit/managed-runtime';STAGE=ROOT/'.build/ios-jit/sj-lobby-runtime'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('accepted_builder',SOURCE.parent/'sj-code-budget/build_runtime.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def main():
 STAGE.mkdir(parents=True,exist_ok=True);sources={};patches=[]
 for name in ['mini.c','mini-runtime.c','method-to-ir.c','mono-codeman.c']:
  source=RUNTIME/'runtime-v8.0.28/src/mono/mono'/('utils' if name=='mono-codeman.c' else 'mini')/name
  before=(ROOT/'.build/ios-jit/sj-budget-runtime/mono-codeman.c').read_text() if name=='mono-codeman.c' else source.read_text();after=before
  # Include after existing headers: mini.h already defines class internals.
  anchor='#include "mini.h"'
  if name!='mono-codeman.c':
   assert after.count(anchor)==1;after=after.replace(anchor,anchor+'\n#include "cjit-bfi-policy.h"')
  if name=='mini.c':
   a='\tif (!mono_runtime_class_init_full (vtable, error))\n\t\treturn NULL;\n\treturn MINI_ADDR_TO_FTNPTR (code);'
   b='\tif (!cjit_defer_beforefieldinit (method->klass) && !mono_runtime_class_init_full (vtable, error))\n\t\treturn NULL;\n\treturn MINI_ADDR_TO_FTNPTR (code);'
   assert after.count(a)==1;after=after.replace(a,b)
  elif name=='mini-runtime.c':
   a='\t\tg_assert (vtable);\n\t\tif (!mono_runtime_class_init_full (vtable, error))\n\t\t\treturn NULL;\n\n\t\tcode = MINI_ADDR_TO_FTNPTR (info->code_start);'
   b=a.replace('if (!mono_runtime_class_init_full','if (!cjit_defer_beforefieldinit (method->klass) && !mono_runtime_class_init_full')
   assert after.count(a)==1;after=after.replace(a,b)
  elif name=='mono-codeman.c':
   assert after.count('#define MIN_CHUNK_BYTES (64 * 1024)')==1;after=after.replace('#define MIN_CHUNK_BYTES (64 * 1024)','#define MIN_CHUNK_BYTES (16 * 1024)').replace('keep the usual 64 KiB floor independent of OS page size.','use a 16 KiB floor, clamped to OS page and granule sizes.')
  else:
   replacements=[('if (cfg->compile_aot && !for_field_access && mono_class_is_before_field_init (klass))','if (!for_field_access && (cfg->compile_aot || cjit_defer_beforefieldinit (klass)) && mono_class_is_before_field_init (klass))'),
    ('if (cfg->method == method)\n\t\t\treturn FALSE;','if (cfg->method == method && !cjit_defer_beforefieldinit (klass))\n\t\t\treturn FALSE;'),
    ('if (! (method->flags & METHOD_ATTRIBUTE_STATIC) && (klass == method->klass))','if (! (method->flags & METHOD_ATTRIBUTE_STATIC) && (klass == method->klass) && !cjit_defer_beforefieldinit (klass))')]
   for a,b in replacements:assert after.count(a)==1;after=after.replace(a,b)
  output=STAGE/name;output.write_text(after);sources[name]=dict(source=source,patched=output)
  patches.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
 patch=STAGE/'mono8-femto-beforefieldinit.patch';patch.write_text(''.join(patches))
 inherited=ROOT/'.build/ios-jit/sj-budget-runtime';prior=json.loads((inherited/'receipt.json').read_text());env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer')
 receipt=dict(schema=1,status='PASS_SCOPED_FEMTO_BFI_RUNTIME_BUILD',inherited_receipt_sha256=sha(inherited/'receipt.json'),policy_header_sha256=sha(SOURCE/'src/cjit-bfi-policy.h'),builder_sha256=sha(Path(__file__)),patch_sha256=sha(patch),scope='FemtoHelper beforefieldinit types only; ordinary explicit cctors and other assemblies unchanged',targets={})
 for target,build in [('host','mono-build-host-coop'),('ios','mono-build-ios')]:
  stage=STAGE/target;stage.mkdir(exist_ok=True);db=RUNTIME/build/'compile_commands.json';commands=json.loads(db.read_text());objects=[];used={}
  for name,row in sources.items():
   argv=shlex.split(next(c['command'] for c in commands if c['file']==str(row['source'])));obj=stage/(name+'.o');argv[argv.index('-o')+1]=str(obj);argv[argv.index(str(row['source']))]=str(row['patched']);argv+=['-iquote',str(row['source'].parent),'-I'+str(SOURCE/'src'),'-MMD','-MF',str(stage/(name+'.d'))]
   if target=='host' and name=='mono-codeman.c':argv+=['-Dmono_pagesize=cjit_test_pagesize','-Dmono_valloc_granule=cjit_test_valloc_granule','-DBIND_ROOM=4']
   run=subprocess.run(argv,cwd=stage,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(stage/(name+'.log')).write_text(run.stdout)
   if run.returncode:raise RuntimeError(run.stdout)
   objects.append(obj);used[name]=dict(command=argv,original_source_sha256=sha(row['source']),patched_source_sha256=sha(row['patched']),object_sha256=sha(obj))
  original=inherited/target/'libmonosgen-2.0.a';assert sha(original)==prior['targets'][target]['sha256'];output=stage/'libmonosgen-2.0.a';shutil.copy2(original,output)
  subprocess.run(['xcrun','ar','-r',str(output),*map(str,objects)],env=env,check=True);before=old.members(original);after=old.members(output);names={p.name for p in objects}
  assert collections.Counter((n,h) for n,h in before if n not in names)==collections.Counter((n,h) for n,h in after if n not in names)
  assert all(sum(n==name for n,h in after)==1 for name in names)
  receipt['targets'][target]=dict(archive=str(output.relative_to(ROOT)),sha256=sha(output),original_sha256=sha(original),replaced_members=sorted(names),unchanged_members=len(before)-len(names),objects=used,compile_database_sha256=sha(db));print('PASS_SCOPED_BFI_RUNTIME',target,flush=True)
 (STAGE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
