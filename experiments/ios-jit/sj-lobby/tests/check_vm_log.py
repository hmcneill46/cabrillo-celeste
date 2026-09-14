#!/usr/bin/env python3
"""Run the production compact VM logger over 16,384 real Darwin VM entries."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
S=Path(__file__).resolve().parents[1];R=S.parents[2];O=R/'.build/ios-jit/sj-lobby-vmlog-tests';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=(S/'src/main.m').read_text();block=source[source.index('typedef struct { __unsafe_unretained NSMutableArray *first;'):source.index('typedef struct { uintptr_t rx, rw; size_t length; } CJArena;')]
harness='''#import <Foundation/Foundation.h>
#import <CommonCrypto/CommonDigest.h>
#include <unistd.h>
#include <assert.h>
#include <mach/mach.h>
#include "VMRange.h"
'''+block+'''
int main(void){@autoreleasepool{
 vm_address_t whole=0;size_t page=getpagesize(),count=16384;
 assert(vm_allocate(mach_task_self(),&whole,page*(count+2),VM_FLAGS_ANYWHERE)==KERN_SUCCESS);
 assert(vm_protect(mach_task_self(),whole,page,TRUE,VM_PROT_NONE)==KERN_SUCCESS);
 assert(vm_protect(mach_task_self(),whole+page*(count+1),page,TRUE,VM_PROT_NONE)==KERN_SUCCESS);
 vm_address_t base=whole+page;
 for(size_t i=0;i<count;i++)assert(vm_protect(mach_task_self(),base+i*page,page,TRUE,i%2?VM_PROT_READ:VM_PROT_READ|VM_PROT_WRITE)==KERN_SUCCESS);
 assert(vm_protect(mach_task_self(),base,count*page,FALSE,VM_PROT_READ)==KERN_SUCCESS);
 NSDictionary *r=CJRegion(base,page*count);NSData *json=[NSJSONSerialization dataWithJSONObject:r options:0 error:NULL];assert(json);
 fwrite(json.bytes,1,json.length,stdout);puts("");assert(vm_deallocate(mach_task_self(),whole,page*(count+2))==KERN_SUCCESS);
 return 0;
}}
'''
(O/'test.m').write_text(harness)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-26.6.app/Contents/Developer',ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
cmd=['xcrun','clang','-fobjc-arc','-O1','-g','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-fsanitize=address,undefined','-I'+str(S/'src'),str(O/'test.m'),str(S/'src/VMRange.c'),str(S/'src/VMRangeDarwin.c'),'-framework','Foundation','-o',str(O/'test')]
subprocess.run(cmd,env=env,check=True)
x=subprocess.run([O/'test'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
assert x.returncode==0,x.stderr
(O/'report.json').write_text(x.stdout);r=json.loads(x.stdout)
assert r['covers_requested_bytes'] and r['entry_count']==r['entry_trace_count']==r['entry_limit']==16384
assert r['protection']==1 and r['union_protection']==1 and len(r['entries'])==16 and r['entries_sampled']
base=int(r['address'],16);page=r['page_bytes'];digest=hashlib.sha256()
for i in range(16384):digest.update(struct.pack('<6Q',base+i*page,base+i*page,page,page,1,1 if i%2 else 3))
assert r['entry_trace_sha256']==digest.hexdigest()
assert [int(e['query_address'],16) for e in r['entries']]==[base+i*page for i in [*range(8),*range(16376,16384)]]
assert r['mapped_bytes']==16384*page and len(x.stdout)<6000
files=[Path(__file__),S/'src/main.m',S/'src/VMRange.c',S/'src/VMRangeDarwin.c',S/'src/VMRange.h',O/'test.m',O/'test',O/'report.json']
receipt=dict(status='PASS_PRODUCTION_COMPACT_VM_LOG_FULL_TRACE_SHA256',real_darwin_entries=16384,retained_entries=16,json_bytes=len(x.stdout),actual_trace_sha256=digest.hexdigest(),source_block_sha256=hashlib.sha256(block.encode()).hexdigest(),files={str(p.relative_to(R)):sha(p) for p in files},command=cmd,sanitizers=['address','undefined'],device_execution=False)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],receipt['json_bytes'])
