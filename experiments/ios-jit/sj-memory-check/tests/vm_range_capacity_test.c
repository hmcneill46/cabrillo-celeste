#if CJ_VM_OLD_CONTROL
#include "../../native-probe/src/VMRange.h"
#else
#include "../src/VMRange.h"
#endif
#include <assert.h>
#include <mach/mach.h>
#include <mach/vm_map.h>
#include <stdio.h>
#include <unistd.h>
#include "physical-prefix.h"

static size_t cases;
static void passed(const char *name) { ++cases; printf("PASS %s\n", name); }
static int physical_query(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (void)context;
    size_t index = (cursor - physical_entries[0].address) / 16384;
    if (cursor < physical_entries[0].address || index >= 4096) return 5;
    *entry = physical_entries[index]; return 0;
}
#if !CJ_VM_OLD_CONTROL
typedef struct { uintptr_t base; size_t page, count, fault, calls; int kind; } Map;
static int query(uintptr_t cursor, CJVMEntry *entry, void *context) {
    Map *map = context; map->calls++;
    size_t index = (cursor - map->base) / map->page;
    if (cursor < map->base || index >= map->count) return 5;
    *entry = (CJVMEntry){map->base + index * map->page, map->page, 5, 7};
    if (index == map->fault) switch (map->kind) {
        case 1: entry->protection = 7; break;
        case 2: entry->protection = 3; break;
        case 3: entry->address += map->page; break;
        case 4: entry->length = 0; break;
        case 5: entry->address = cursor - 1; entry->length = 1; break;
        case 6: entry->address = UINTPTR_MAX - 1; entry->length = 4; break;
        case 7: return 42;
    }
    return 0;
}
static int tiny(uintptr_t cursor, CJVMEntry *entry, void *context) {
    (*(size_t *)context)++; *entry = (CJVMEntry){cursor, 1, 5, 7}; return 0;
}
typedef struct { size_t entries, bytes; uintptr_t next; } Visits;
static void visit(uintptr_t cursor, const CJVMEntry *entry, size_t checked, void *context) {
    (void)entry; Visits *v = context; assert(cursor == v->next);
    v->entries++; v->bytes += checked; v->next += checked;
}
static int accepted_rx(CJVMRangeReport r) { return r.status == CJVMRangeComplete && r.common_protection == 5; }
static CJVMRangeReport inspect(Map *m, size_t bytes) {
    m->calls=0; return CJInspectVMRangeForPageSize(m->base,bytes,m->page,query,m,NULL,NULL);
}
#endif
int main(void) {
    uintptr_t base=physical_entries[0].address;
#if CJ_VM_OLD_CONTROL
    CJVMRangeReport r=CJInspectVMRange(base,134217728,physical_query,NULL,NULL,NULL);
    assert(r.status==CJVMRangeTooManyEntries && r.covered_bytes==67108864 && r.entry_count==4096 && r.common_protection==5);
    passed("exact build17 recorded RX prefix reproduces the 4096-entry cutoff");
#else
    CJVMRangeReport r=CJInspectVMRangeForPageSize(base,134217728,16384,physical_query,NULL,NULL,NULL);
    assert(r.status==CJVMRangeQueryFailed && r.covered_bytes==67108864 && r.entry_count==4096 && r.entry_limit==8192);
    passed("recorded prefix alone remains insufficient: unobserved tail is not accepted");
    Map m={.base=base,.page=16384,.count=8192};
    Visits v={.next=base};
    r=CJInspectVMRangeForPageSize(base,134217728,16384,query,&m,visit,&v);
    assert(accepted_rx(r) && r.covered_bytes==134217728 && r.entry_count==8192 && r.entry_limit==8192);
    assert(v.entries==8192 && v.bytes==134217728 && v.next==base+134217728);
    passed("complete 128 MiB range visits all 8192 16 KiB RX fragments");
    for (size_t pages=4095;pages<=4097;pages++) {
        r=inspect(&m,pages*m.page); assert(accepted_rx(r) && r.entry_count==pages && r.entry_limit==pages);
    }
    passed("below, at and beyond the old 4096-entry boundary");
    m.count=32768; r=inspect(&m,m.count*m.page);
    assert(accepted_rx(r) && r.entry_count==32768 && r.entry_limit==32768);
    passed("larger future ranges derive their own bound without changing a fixed cap");
    for (size_t page=4096;page<=65536;page*=4) {
        m=(Map){.base=0x100000,.page=page,.count=8192};
        r=inspect(&m,m.count*page); assert(accepted_rx(r) && r.entry_count==8192);
    }
    passed("4 KiB, 16 KiB and 64 KiB page geometry");
    m=(Map){.base=base,.page=16384,.count=8192};
    r=CJInspectVMRangeForPageSize(base+17,32768,16384,query,&m,NULL,NULL);
    assert(accepted_rx(r) && r.entry_count==3 && r.entry_limit==3 && r.covered_bytes==32768);
    r=CJInspectVMRangeForPageSize(base+17,100,16384,query,&m,NULL,NULL);
    assert(accepted_rx(r) && r.entry_count==1 && r.entry_limit==1 && r.covered_bytes==100);
    passed("partial first and last pages include every intersected entry");
    m.page=134217728;m.count=1;r=inspect(&m,m.page);
    assert(accepted_rx(r) && r.entry_count==1);
    passed("single large VM entry remains accepted");
    m=(Map){.base=base,.page=16384,.count=8192,.fault=6000};
    for (int kind=1;kind<=7;kind++) {
        m.kind=kind;r=inspect(&m,134217728);assert(!accepted_rx(r));
        if(kind<=2) assert(r.status==CJVMRangeComplete && r.common_protection==-1 && r.covered_bytes==134217728);
        if(kind==3) assert(r.status==CJVMRangeGap && r.covered_bytes==6000*16384);
        if(kind>=4 && kind<=6) assert(r.status==CJVMRangeInvalidEntry && r.covered_bytes==6000*16384);
        if(kind==7) assert(r.status==CJVMRangeQueryFailed && r.query_result==42 && r.covered_bytes==6000*16384);
        passed(kind==1?"late RWX fragment rejected":kind==2?"late RW fragment rejected":kind==3?"late gap rejected":kind==4?"zero-size entry rejected":kind==5?"nonadvancing entry rejected":kind==6?"overflowing entry rejected":"late query failure preserved");
    }
    m.kind=0;m.count=8191;r=inspect(&m,134217728);
    assert(r.status==CJVMRangeQueryFailed && r.covered_bytes==134217728-16384);
    passed("missing final page never passes full-range validation");
    m.calls=0;
    assert(CJInspectVMRangeForPageSize(base,0,16384,query,&m,NULL,NULL).status==CJVMRangeInvalidBounds);
    assert(CJInspectVMRangeForPageSize(UINTPTR_MAX-3,4,16384,query,&m,NULL,NULL).status==CJVMRangeInvalidBounds);
    assert(CJInspectVMRangeForPageSize(base,4,0,query,&m,NULL,NULL).status==CJVMRangeInvalidBounds);
    assert(CJInspectVMRangeForPageSize(base,4,3,query,&m,NULL,NULL).status==CJVMRangeInvalidBounds);
    assert(CJInspectVMRangeForPageSize(base,4,16384,NULL,&m,NULL,NULL).status==CJVMRangeInvalidBounds);
    assert(m.calls==0);passed("invalid ranges, page sizes and callbacks fail before querying");
    size_t calls=0;r=CJInspectVMRangeForPageSize(base,16385,16384,tiny,&calls,NULL,NULL);
    assert(r.status==CJVMRangeTooManyEntries && r.entry_limit==2 && r.entry_count==2 && calls==2);
    passed("malformed sub-page query retains a finite page-derived traversal bound");
    // Real Darwin backend: alternate maximum protections force 8192 entries
    // while all current protections are R. No generated code is executed.
    vm_address_t region=0;vm_size_t page=(vm_size_t)getpagesize(),bytes=page*8192;
    assert(vm_allocate(mach_task_self(),&region,bytes,VM_FLAGS_ANYWHERE)==KERN_SUCCESS);
    for (size_t i=1;i<8192;i+=2) assert(vm_protect(mach_task_self(),region+i*page,page,TRUE,VM_PROT_READ)==KERN_SUCCESS);
    assert(vm_protect(mach_task_self(),region,bytes,FALSE,VM_PROT_READ)==KERN_SUCCESS);
    r=CJInspectVMRange(region,bytes,CJQueryDarwinVMEntry,NULL,NULL,NULL);
    assert(r.status==CJVMRangeComplete && r.entry_count==8192 && r.entry_limit==8192 && r.covered_bytes==bytes && r.common_protection==VM_PROT_READ);
    assert(vm_deallocate(mach_task_self(),region,bytes)==KERN_SUCCESS);
    passed("production wrapper and Darwin adapter traverse 8192 actual VM entries");
#endif
    printf("{\"cases\":%zu,\"device_execution\":false}\n",cases);return 0;
}
