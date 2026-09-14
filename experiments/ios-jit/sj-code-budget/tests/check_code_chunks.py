#!/usr/bin/env python3
"""Compile exact old/new Mono new_codechunk bodies; test sizing and failures."""
import hashlib,json,os,subprocess
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];ROOT=SOURCE.parents[2]
STAGE=ROOT/'.build/ios-jit/sj-budget-chunk-tests';STAGE.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=ROOT/'.build/ios-jit/managed-runtime/runtime-v8.0.28/src/mono/mono/utils/mono-codeman.c'
patched=ROOT/'.build/ios-jit/sj-budget-runtime/mono-codeman.c'
receipt=json.loads((patched.parent/'receipt.json').read_text())
assert sha(original)==receipt['original_codeman_sha256'] and sha(patched)==receipt['patched_codeman_sha256']
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int gint;typedef unsigned guint;typedef unsigned char guint8;typedef unsigned char mono_byte;
typedef struct _MonoCodeManager MonoCodeManager;
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN_PAGES 16
#define MIN_CHUNK_BYTES (64*1024)
#define MIN_BSIZE 32
#define MONO_MEM_ACCOUNT_CODE 1
#define MONO_RESOURCE_JIT_CODE 1
#define MONO_PROFILER_RAISE(a,b) ((void)0)
#define CJ_CODE_WRITE(p,n) (p)
#define g_malloc malloc
#define g_free free
static int page_bytes,granule_bytes,allocation_failure,malloc_mode;
static uintptr_t code_memory_used;
static const struct {void (*chunk_new)(void *,int);} *code_manager_callbacks;
static int mono_pagesize(void) {return page_bytes;}
static int mono_valloc_granule(void) {return granule_bytes;}
static void *mono_codeman_malloc(int size) {return allocation_failure?NULL:calloc(1,(size_t)size);}
static void mono_codeman_free(void *p) {free(p);}
static void *codechunk_valloc(void *preferred,int size,int no_exec) {(void)preferred;(void)no_exec;return mono_codeman_malloc(size);}
static void mono_vfree(void *p,int size,int account) {(void)size;(void)account;free(p);}
static void mono_runtime_resource_check_limit(int resource,uintptr_t bytes) {(void)resource;(void)bytes;}
static void mono_codeman_enable_write(void) {}
static void mono_codeman_disable_write(void) {}
'''
suffix=r'''
int main(void) {
  const int pages[]={4096,16384,65536};
  const int boundaries[]={1,7,8,15,16,31,32,4095,4096,4097,16383,16384,16385,49151,49152,49153,65535,65536,65537,262143,262144,262145,1048576};
  int cases=0;
  for(int p=0;p<3;p++)for(int g=p;g<3;g++)for(int dynamic=0;dynamic<2;dynamic++)for(malloc_mode=0;malloc_mode<2;malloc_mode++) {
    page_bytes=pages[p];granule_bytes=pages[g];
    for(int i=0;i<280;i++) {
      int size=i<23?boundaries[i]:1+(i-23)*4093;
      MonoCodeManager manager={0};manager.dynamic=(unsigned)dynamic;
      CodeChunk *chunk=new_codechunk(&manager,size);assert(chunk);
      assert(chunk->size-chunk->pos>=size && chunk->pos==chunk->bsize);
      assert(chunk->pos%MIN_ALIGN==0);
      if(!dynamic) {
        assert(chunk->size%granule_bytes==0);
        assert(chunk->size>=page_bytes && chunk->size>=granule_bytes);
        if(size==1) {
#ifdef OLD_POLICY
          assert(chunk->size==MAX(page_bytes*16,granule_bytes));
#else
          assert(chunk->size==MAX(MAX(65536,page_bytes),granule_bytes));
#endif
        }
      }
#ifdef BIND_ROOM
      assert(chunk->bsize>=32);
      if(dynamic)assert(chunk->bsize>=size/2);
#else
      assert(chunk->bsize==0);
#endif
      memset(chunk->data+chunk->pos,0xA3,(size_t)size);
      free(chunk->data);free(chunk);cases++;
    }
    MonoCodeManager manager={0};manager.dynamic=(unsigned)dynamic;
    allocation_failure=1;assert(!new_codechunk(&manager,100));allocation_failure=0;cases++;
  }
  printf("PASS_ACTUAL_MONO_CHUNK_SIZING cases=%d align=%d binding_divisor=%d\n",cases,MIN_ALIGN,
#ifdef BIND_ROOM
  BIND_ROOM
#else
  0
#endif
  );
}
'''
results={}
for old,source in [(True,original),(False,patched)]:
 text=source.read_text()
 structures=text[text.index('typedef struct _CodeChunk CodeChunk;'):text.index('#define ALIGN_INT')]
 begin=text.index('static CodeChunk*\nnew_codechunk');end=text.index('\n/**',begin)
 function=text[begin:end]
 # The whole production function is included verbatim; only its OS/allocation
 # dependencies are stubbed so page geometry and allocation failure are controllable.
 for bind,align in [(False,16),(True,8)]:
  name=('old' if old else 'new')+('-arm64-sizing' if bind else '-x64-sizing')
  c=STAGE/(name+'.c');c.write_text(prefix+structures+'\nstatic int mono_codeman_allocation_type(MonoCodeManager *m){(void)m;return malloc_mode?CODE_FLAG_MALLOC:CODE_FLAG_MMAP;}\n'+function+suffix)
  binary=STAGE/name;cmd=['xcrun','clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined',f'-DMIN_ALIGN={align}']
  if bind:cmd+=['-DBIND_ROOM=4']
  if old:cmd+=['-DOLD_POLICY=1']
  cmd += [str(c),'-o',str(binary)]
  subprocess.run(cmd,env=env,check=True)
  run=subprocess.run([binary],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
  assert 'PASS_ACTUAL_MONO_CHUNK_SIZING' in run.stdout
  (STAGE/(name+'.log')).write_text(run.stdout);results[name]=dict(command=cmd,output=run.stdout,function_sha256=hashlib.sha256(function.encode()).hexdigest(),generated_test_sha256=sha(c))
  print(name,run.stdout.strip())
(STAGE/'receipt.json').write_text(json.dumps(dict(status='PASS_EXACT_MONO_CODE_CHUNK_BODY_4K_16K_64K_AND_THUNK_SPACE',runs=results,input_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),original,patched]},scope='Actual function extracted without edits; allocation stubs, ASan/UBSan, page/granule/binding/large-request/dynamic/failure controls; no ARM64 execution'),indent=2)+'\n')
