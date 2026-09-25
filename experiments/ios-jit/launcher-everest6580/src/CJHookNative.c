#include "CJHookNative.h"
#include "CJCodeArena.h"
#include "CJMonoThread.h"
#include "VMRange.h"
#include <mono/jit/jit.h>
#include <mono/metadata/appdomain.h>
#include <mono/metadata/class.h>
#include <mono/metadata/object.h>
#include <libkern/OSCacheControl.h>
#include <mach/mach.h>
#include <mach-o/dyld.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static CJHookLog log_event;
static _Atomic size_t patch_count, rejected_count;
static pthread_mutex_t patch_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t allocation_lock = PTHREAD_MUTEX_INITIALIZER;
typedef struct { void *address; size_t length, reserved; int executable, active; } HookAllocation;
static HookAllocation allocations[256];
static size_t allocation_count;

void CJHookSetLog(CJHookLog log) { log_event = log; }
size_t CJHookPatchCount(void) { return atomic_load(&patch_count); }
size_t CJHookRejectedCount(void) { return atomic_load(&rejected_count); }
static void record(const char *event, uintptr_t rx, uintptr_t rw, size_t length, const char *detail, int actual, int expected) {
    if (log_event) log_event(event, rx, rw, length, detail, actual, expected);
}
void CJHookMark(const char *stage, int state, int actual, int expected) {
    record(state == 0 ? "hook_stage_start" : state == 1 ? "hook_stage_pass" : "hook_stage_fail", 0, 0, 0, stage, actual, expected);
}
static int CJHookEnvironment(void) {
    if (!strstr(mono_get_runtime_build_info(), "46295af5828b062bbbf93a9cef50fd8cb9fbcb09")) return 0;
#if CJ_HOOK_HOST_TEST
    return 2;
#else
    return cj_code_arena_allocations() ? 1 : 0;
#endif
}
static int CJHookMethodLayout(void *method) {
    if (!method) return 0;
    void *anchor = NULL, *cookie = mono_threads_enter_gc_unsafe_region(&anchor);
    uint32_t impl = 0; (void)mono_method_get_flags(method, &impl);
    uint16_t field; memcpy(&field, (const char *)method + 2, sizeof(field));
    mono_threads_exit_gc_unsafe_region(cookie, &anchor);
    return field == impl && (impl & 8) != 0;
}
static intptr_t CJHookReadable(void *start, intptr_t guess) {
    if (!start || guess <= 0 || guess > 65536) return 0;
    CJVMRangeReport range = CJInspectVMRange((uintptr_t)start, (size_t)guess, CJQueryDarwinVMEntry, NULL, NULL, NULL);
    // -1 denotes mixed protections, not a readable bitmask. Be conservative
    // when this bounded probe crosses mappings with different protections.
    return range.status == CJVMRangeComplete && range.common_protection >= 0 &&
        (range.common_protection & VM_PROT_READ) ? guess : 0;
}
static int CJHookImageCount(void) { return (int)_dyld_image_count(); }
static const char *CJHookImageName(int index) { return index >= 0 ? _dyld_get_image_name((uint32_t)index) : NULL; }

static int allocation_contains(void *address, size_t size, int *executable) {
    uintptr_t p = (uintptr_t)address; int found = 0;
    pthread_mutex_lock(&allocation_lock);
    for (size_t i = 0; i < allocation_count; i++) {
        HookAllocation *a = &allocations[i]; uintptr_t base = (uintptr_t)a->address;
        if (a->active && p >= base && p - base < a->length && size <= a->length - (p - base)) {
            *executable = a->executable; found = 1; break;
        }
    }
    pthread_mutex_unlock(&allocation_lock); return found;
}
static int known_jit_range(void *address, size_t size) {
    void *anchor = NULL, *cookie = mono_threads_enter_gc_unsafe_region(&anchor);
    MonoJitInfo *info = mono_jit_info_table_find(mono_domain_get(), address);
    uintptr_t start = info ? (uintptr_t)mono_jit_info_get_code_start(info) : 0;
    size_t bytes = info ? (size_t)mono_jit_info_get_code_size(info) : 0;
    uintptr_t p = (uintptr_t)address;
    int valid = info && p >= start && p - start < bytes && size <= bytes - (p - start);
    mono_threads_exit_gc_unsafe_region(cookie, &anchor); return valid;
}
static int CJHookPatch(void *target, const void *data, int size, void *backup, int backup_size) {
    const char *error = NULL; void *writable = target; int executable = 1;
    if (!target || !data || size <= 0 || size > 65536 || (backup && backup_size < size)) error = "invalid_arguments";
    if (!error && !allocation_contains(target, (size_t)size, &executable) && !known_jit_range(target, (size_t)size)) error = "outside_compiled_method_or_hook_allocation";
#if !CJ_HOOK_HOST_TEST
    if (!error && executable) {
        if (!cj_code_arena_contains_allocation(target, (size_t)size)) error = "outside_prepared_code_allocation";
        else writable = cj_mono_writable(target, (size_t)size);
        if (!error && ((uintptr_t)target % 4 || size % 4)) error = "unaligned_arm64_patch";
        if (!error) {
            CJVMRangeReport rx = CJInspectVMRange((uintptr_t)target, (size_t)size, CJQueryDarwinVMEntry, NULL, NULL, NULL);
            CJVMRangeReport rw = CJInspectVMRange((uintptr_t)writable, (size_t)size, CJQueryDarwinVMEntry, NULL, NULL, NULL);
            if (target == writable || rx.status != CJVMRangeComplete || rw.status != CJVMRangeComplete ||
                rx.common_protection != (VM_PROT_READ | VM_PROT_EXECUTE) || rw.common_protection != (VM_PROT_READ | VM_PROT_WRITE)) error = "alias_protection_mismatch";
        }
    }
#endif
    if (error) {
        atomic_fetch_add(&rejected_count, 1);
        record("hook_patch_rejected", (uintptr_t)target, (uintptr_t)writable, size > 0 ? (size_t)size : 0, error, 0, 0); return 0;
    }
    pthread_mutex_lock(&patch_lock);
    if (backup) memcpy(backup, target, (size_t)size);
    // MonoMod serializes its chain transitions. This canary does not install
    // initial entry patches while unrelated threads execute the same method.
    if (size == 4 && (uintptr_t)writable % 4 == 0) {
        uint32_t instruction; memcpy(&instruction, data, 4);
        atomic_store_explicit((_Atomic uint32_t *)writable, instruction, memory_order_release);
    } else memcpy(writable, data, (size_t)size);
    if (executable) {
#if CJ_HOOK_HOST_TEST
        sys_dcache_flush(writable, (size_t)size); sys_icache_invalidate(target, (size_t)size);
#else
        cj_mono_flush(target, (size_t)size);
#endif
    }
    int matches = memcmp(target, data, (size_t)size) == 0;
    pthread_mutex_unlock(&patch_lock);
    if (matches) atomic_fetch_add(&patch_count, 1); else atomic_fetch_add(&rejected_count, 1);
    record(matches ? "hook_code_patch" : "hook_patch_rejected", (uintptr_t)target, (uintptr_t)writable, (size_t)size,
           matches ? (executable ? "executable_backup_write_flush_verified" : "owned_data_write_verified") : "readback_mismatch", 0, 0);
    return matches;
}

static void *CJHookAllocate(int size, int alignment, int executable, void *low, void *high) {
    if (size <= 0 || size > 65536 || alignment <= 0 || (alignment & (alignment - 1)) || alignment > getpagesize()) return NULL;
    void *address = NULL; size_t reserved = (size_t)size;
    pthread_mutex_lock(&allocation_lock);
    if (allocation_count == sizeof(allocations)/sizeof(allocations[0])) goto done;
    if (executable) {
#if CJ_HOOK_HOST_TEST
        reserved = ((size_t)size + getpagesize() - 1) & ~((size_t)getpagesize() - 1);
        address = mmap(NULL, reserved, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANON, -1, 0);
        if (address == MAP_FAILED) address = NULL;
#else
        address = cj_mono_code_alloc((size_t)size);
#endif
    } else {
        size_t align = (size_t)alignment < sizeof(void *) ? sizeof(void *) : (size_t)alignment;
        if (posix_memalign(&address, align, (size_t)size) != 0) address = NULL;
        if (address) memset(address, 0, (size_t)size);
    }
    if (address && (low || high) && ((uintptr_t)address < (uintptr_t)low || (uintptr_t)high < (uintptr_t)address || (size_t)size > (uintptr_t)high - (uintptr_t)address)) {
        if (!executable) free(address);
#if CJ_HOOK_HOST_TEST
        else munmap(address, reserved);
#endif
        // Device executable reservations have process lifetime and are never
        // unsafely recycled. A rejected range remains reserved and budgeted.
        address = NULL;
    }
    if (address) allocations[allocation_count++] = (HookAllocation){address, (size_t)size, reserved, executable, 1};
done:
    pthread_mutex_unlock(&allocation_lock);
    record(address ? "hook_memory_allocated" : "hook_memory_unavailable", (uintptr_t)address, 0, (size_t)size, executable ? "code" : "data", 0, 0);
    return address;
}
static int CJHookRelease(void *address) {
    int found = 0;
    pthread_mutex_lock(&allocation_lock);
    for (size_t i = 0; i < allocation_count; i++) {
        HookAllocation *a = &allocations[i];
        if (a->address != address || !a->active) continue;
        a->active = 0; found = 1;
        if (!a->executable) free(a->address);
#if CJ_HOOK_HOST_TEST
        else munmap(a->address, a->reserved);
#endif
        break;
    }
    pthread_mutex_unlock(&allocation_lock);
    record(found ? "hook_memory_released" : "hook_memory_release_rejected", (uintptr_t)address, 0, 0, "code_reservations_live_until_process_exit", 0, 0);
    return found;
}
void *CJResolveHookNative(const char *library, const char *entry) {
    if (!library || !entry || strcmp(library, "CJHookNative")) return NULL;
#define ENTRY(name) if (!strcmp(entry, #name)) return (void *)&name
    ENTRY(CJHookEnvironment); ENTRY(CJHookMethodLayout); ENTRY(CJHookPatch); ENTRY(CJHookReadable);
    ENTRY(CJHookAllocate); ENTRY(CJHookRelease); ENTRY(CJHookImageCount); ENTRY(CJHookImageName); ENTRY(CJHookMark);
#undef ENTRY
    return NULL;
}
