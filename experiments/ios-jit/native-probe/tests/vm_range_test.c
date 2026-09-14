#include "../src/VMRange.h"
#include <assert.h>
#include <mach/mach.h>
#include <mach/vm_map.h>
#include <stdio.h>
#include <unistd.h>

typedef struct { CJVMEntry entries[4]; size_t count; int fail_after; } Map;
static int query(uintptr_t cursor, CJVMEntry *entry, void *context) {
    Map *map = context;
    for (size_t i = 0; i < map->count; i++) {
        if (map->entries[i].address + map->entries[i].length > cursor) {
            if (map->fail_after >= 0 && i >= (size_t)map->fail_after) return 5;
            *entry = map->entries[i]; return 0;
        }
    }
    return 1;
}
static int zero_length(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (void)context; *entry = (CJVMEntry){.address = cursor, .length = 0}; return 0;
}
static int nonadvancing(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (void)context; *entry = (CJVMEntry){.address = cursor - 1, .length = 1}; return 0;
}
static int overflow(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (void)cursor; (void)context; *entry = (CJVMEntry){.address = UINTPTR_MAX - 1, .length = 4}; return 0;
}
static int tiny_entries(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (void)context; *entry = (CJVMEntry){.address = cursor, .length = 1, .protection = 5}; return 0;
}
static int cases = 0;
static void passed(const char *name) { cases++; printf("PASS %s\n", name); }

int main(void) {
    const uintptr_t base = 0x100000;
    const size_t page = 16384, length = page * 4;
    Map map = {.count = 4, .fail_after = -1};
    for (size_t i = 0; i < 4; i++) map.entries[i] = (CJVMEntry){base + i * page, page, 5, 7};
    CJVMRangeReport r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeComplete && r.covered_bytes == length && r.entry_count == 4 && r.common_protection == 5);
    passed("four 16 KiB RX entries cover one 64 KiB allocation (device regression)");
    map.entries[0].length = length; map.count = 1;
    r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeComplete && r.entry_count == 1 && r.common_protection == 5);
    passed("single-entry allocation remains supported");
    r = CJInspectVMRange(base + 17, 100, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeComplete && r.covered_bytes == 100 && r.entry_count == 1);
    passed("request inside a larger entry clips both boundaries");
    map.count = 4; map.entries[0].length = page;
    map.entries[2].protection = 7;
    r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeComplete && r.common_protection == -1 && r.union_protection == 7);
    passed("RX plus RWX is never reported as uniformly RX");
    map.entries[2].protection = 3;
    r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.common_protection == -1 && r.status == CJVMRangeComplete);
    passed("RW fragment in RX range is distinguishable and rejected by caller");
    map.entries[2].protection = 5; map.entries[2].address += page / 2;
    r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeGap && r.covered_bytes == page * 2);
    passed("next-mapping response cannot hide a hole");
    map.entries[2].address -= page / 2; map.count = 2;
    r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeQueryFailed && r.covered_bytes == page * 2);
    passed("missing tail is not accepted");
    map.count = 4; map.fail_after = 1;
    r = CJInspectVMRange(base, length, query, &map, NULL, NULL);
    assert(r.status == CJVMRangeQueryFailed && r.query_result == 5 && r.covered_bytes == page);
    passed("query error retains partial coverage and kernel result");
    assert(CJInspectVMRange(base, 0, query, &map, NULL, NULL).status == CJVMRangeInvalidBounds);
    assert(CJInspectVMRange(UINTPTR_MAX - 3, 4, query, &map, NULL, NULL).status == CJVMRangeInvalidBounds);
    passed("zero-length and overflowed requests fail before querying");
    assert(CJInspectVMRange(base, length, zero_length, NULL, NULL, NULL).status == CJVMRangeInvalidEntry);
    assert(CJInspectVMRange(base, length, nonadvancing, NULL, NULL, NULL).status == CJVMRangeInvalidEntry);
    assert(CJInspectVMRange(base, length, overflow, NULL, NULL, NULL).status == CJVMRangeInvalidEntry);
    passed("malformed entries cannot stall or overflow the walker");
    assert(CJInspectVMRange(base, 4097, tiny_entries, NULL, NULL, NULL).status == CJVMRangeTooManyEntries);
    passed("entry-count bound prevents unbounded traversal");

    // Exercise the SAME Darwin adapter against a real fragmented macOS map.
    // Different maximum protections force entry boundaries even though all
    // current protections are read-only. Nothing here executes generated code.
    vm_address_t region = 0;
    vm_size_t host_page = (vm_size_t)getpagesize(), host_length = host_page * 4;
    assert(vm_allocate(mach_task_self(), &region, host_length, VM_FLAGS_ANYWHERE) == KERN_SUCCESS);
    assert(vm_protect(mach_task_self(), region + host_page, host_page, TRUE, VM_PROT_READ) == KERN_SUCCESS);
    assert(vm_protect(mach_task_self(), region + 3 * host_page, host_page, TRUE, VM_PROT_READ) == KERN_SUCCESS);
    assert(vm_protect(mach_task_self(), region, host_length, FALSE, VM_PROT_READ) == KERN_SUCCESS);
    r = CJInspectVMRange(region, host_length, CJQueryDarwinVMEntry, NULL, NULL, NULL);
    assert(r.status == CJVMRangeComplete && r.covered_bytes == host_length && r.entry_count >= 2 && r.common_protection == VM_PROT_READ);
    assert(vm_deallocate(mach_task_self(), region, host_length) == KERN_SUCCESS);
    passed("real Darwin fragmented mapping, shared adapter, complete coverage");
    printf("{\"vm_range_tests_passed\":%d,\"device_jit_execution\":\"NOT_TESTED\"}\n", cases);
    return 0;
}
