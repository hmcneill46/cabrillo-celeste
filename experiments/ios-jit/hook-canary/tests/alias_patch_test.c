// Executes CJHookNative's DEVICE branch with real RX/RW host mappings.
// Mono metadata/GC queries are narrow mocks; no ARM64 instructions execute here.
#include "CJHookNative.h"
#include "CJCodeArena.h"
#include "CJMonoThread.h"
#include <mono/jit/jit.h>
#include <mono/metadata/appdomain.h>
#include <mono/metadata/loader.h>
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static void *method_start;
static int method_size, gc_depth, checked, rejected;
char *mono_get_runtime_build_info(void) { return "8.0.28 (46295af5828b062bbbf93a9cef50fd8cb9fbcb09)"; }
MonoDomain *mono_domain_get(void) { return (MonoDomain *)1; }
MonoJitInfo *mono_jit_info_table_find(MonoDomain *domain, void *address) {
    assert(domain == (MonoDomain *)1 && gc_depth == 1);
    uintptr_t p=(uintptr_t)address, start=(uintptr_t)method_start;
    return p>=start && p-start<(size_t)method_size ? (MonoJitInfo *)1 : NULL;
}
void *mono_jit_info_get_code_start(MonoJitInfo *info) { assert(info == (MonoJitInfo *)1); return method_start; }
int mono_jit_info_get_code_size(MonoJitInfo *info) { assert(info == (MonoJitInfo *)1); return method_size; }
uint32_t mono_method_get_flags(MonoMethod *method, uint32_t *impl) { (void)method; *impl=8; return 0; }
void *mono_threads_enter_gc_unsafe_region(void **anchor) { (void)anchor; assert(gc_depth++ == 0); return (void *)1; }
void mono_threads_exit_gc_unsafe_region(void *cookie, void **anchor) { (void)anchor; assert(cookie == (void *)1 && gc_depth-- == 1); }
static void record(const char *event, uintptr_t rx, uintptr_t rw, size_t bytes, const char *detail, int actual, int expected) {
    (void)bytes; (void)actual; (void)expected;
    if (!strcmp(event,"hook_code_patch")) {
        if (!strcmp(detail,"executable_backup_write_flush_verified")) assert(rx!=rw);
        checked++;
    }
    if (!strcmp(event,"hook_patch_rejected")) rejected++;
}
static CJCodeRegion region(size_t size) {
    char path[]="/tmp/cjit-hook-alias-XXXXXX"; int fd=mkstemp(path); assert(fd>=0); unlink(path); assert(!ftruncate(fd,size));
    void *rx=mmap(NULL,size,PROT_READ|PROT_EXEC,MAP_SHARED,fd,0);
    void *rw=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0); close(fd);
    assert(rx!=MAP_FAILED && rw!=MAP_FAILED && rx!=rw);
    return (CJCodeRegion){(uintptr_t)rx,(uintptr_t)rw,size};
}
int main(void) {
    size_t page=getpagesize(); CJCodeRegion r[2]={region(4*page),region(4*page)};
    assert(cj_code_arena_initialize(r,page,NULL)); CJHookSetLog(record);
    int (*patch)(void *,const void *,int,void *,int)=CJResolveHookNative("CJHookNative","CJHookPatch");
    void *(*allocate)(int,int,int,void *,void *)=CJResolveHookNative("CJHookNative","CJHookAllocate");
    int (*release)(void *)=CJResolveHookNative("CJHookNative","CJHookRelease");
    intptr_t (*readable)(void *,intptr_t)=CJResolveHookNative("CJHookNative","CJHookReadable");
    assert(patch && allocate && release && readable);
    unsigned char *rx=cj_mono_code_alloc(page), *rw=cj_mono_writable(rx,page);
    method_start=rx; method_size=32;
    uint32_t original[8]={1,2,3,4,5,6,7,8}, backup[4]={0}; memcpy(rw,original,32);
    uint32_t detour[4]={0x58000049,0xd61f0120,0x87654320,0x12345678};
    assert(patch(rx,detour,16,backup,16)); assert(!memcmp(backup,original,16));
    assert(!memcmp(rx,detour,16) && !memcmp(rw,detour,16) && !memcmp(rx+16,original+4,16));
    assert(patch(rx,backup,16,NULL,0)); assert(!memcmp(rx,original,32));
    assert(patch(rx+28,detour,4,NULL,0)); assert(!memcmp(rx+28,detour,4));
    assert(!patch(rx+28,detour,8,NULL,0)); // Starts in method, exceeds actual code.
    assert(!patch(rx+32,detour,4,NULL,0)); // Reserved arena padding is not method code.
    assert(!patch(rx+1,detour,4,NULL,0)); assert(!patch(rx,detour,6,NULL,0));
    assert(!patch(rx,detour,16,backup,4)); assert(!patch(NULL,detour,4,NULL,0));
    assert(!patch(rw,detour,4,NULL,0)); // RW alias is never accepted as an entry PC.
    assert(!mprotect(rx,page,PROT_READ)); assert(!patch(rx,detour,4,NULL,0));
    assert(!mprotect(rx,page,PROT_READ|PROT_EXEC));
    assert(!mprotect(rw,page,PROT_READ)); assert(!patch(rx,detour,4,NULL,0));
    assert(!mprotect(rw,page,PROT_READ|PROT_WRITE));
    assert(readable(rx,32)==32 && readable(rx,0)==0);
    assert(!mprotect(rx+page,page,PROT_NONE)); assert(readable(rx+page-4,8)==0);
    assert(!mprotect(rx+page,page,PROT_READ|PROT_EXEC));
    void *code=allocate(64,16,1,NULL,NULL); assert(code && (uintptr_t)code%16==0);
    assert(patch(code,detour,16,backup,16)); assert(!patch((char *)code+60,detour,8,NULL,0));
    size_t used=cj_code_arena_used(); assert(release(code)); assert(!release(code));
    assert(cj_code_arena_used()==used && !patch(code,detour,4,NULL,0));
    void *data=allocate(16,8,0,NULL,NULL); assert(data); assert(patch(data,detour,3,NULL,0));
    assert(!memcmp(data,detour,3)); assert(release(data));
    assert(!allocate(0,8,1,NULL,NULL) && !allocate(16,3,1,NULL,NULL));
    assert(!allocate(16,16,1,(void *)1,(void *)128));
    assert(CJHookPatchCount()==5 && CJHookRejectedCount()==11 && checked==5 && rejected==11 && gc_depth==0);
    printf("PASS_DEVICE_ALIAS_PATCH_BRANCH successful=%d rejected=%d; RX backup/RW stores, exact method bounds, protection checks, restore and allocation lifecycle\n",checked,rejected);
    for(int i=0;i<2;i++){munmap((void *)r[i].rx,r[i].length);munmap((void *)r[i].rw,r[i].length);}
}
