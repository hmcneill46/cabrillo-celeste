#pragma once
#include <stddef.h>
#include <stdint.h>

// vm_region describes one entry, not the complete original allocation. Debugger
// page writes can leave several adjacent entries with identical current access.
typedef struct {
    uintptr_t address;
    size_t length;
    int protection;
    int maximum_protection;
} CJVMEntry;

typedef int (*CJVMQuery)(uintptr_t cursor, CJVMEntry *entry, void *context);
typedef void (*CJVMVisit)(uintptr_t cursor, const CJVMEntry *entry, size_t checked, void *context);

typedef enum {
    CJVMRangeComplete = 0,
    CJVMRangeInvalidBounds,
    CJVMRangeQueryFailed,
    CJVMRangeGap,
    CJVMRangeInvalidEntry,
    CJVMRangeTooManyEntries,
} CJVMRangeStatus;

typedef struct {
    CJVMRangeStatus status;
    int query_result;
    size_t covered_bytes;
    size_t entry_count;
    // Bound derived from the pages intersected by the request, including
    // partial first/last pages. It is never a fixed arena-size assumption.
    size_t entry_limit;
    // Equal access on EVERY traversed entry, or -1 for mixed protections.
    // An intersection alone would incorrectly accept RX + RWX as RX.
    int common_protection;
    int union_protection;
    int maximum_protection_intersection;
} CJVMRangeReport;

CJVMRangeReport CJInspectVMRange(uintptr_t start, size_t length, CJVMQuery query,
                                void *query_context, CJVMVisit visit, void *visit_context);
// Explicit geometry for host tests; the production wrapper uses getpagesize().
CJVMRangeReport CJInspectVMRangeForPageSize(uintptr_t start, size_t length, size_t page_size,
                                         CJVMQuery query, void *query_context,
                                         CJVMVisit visit, void *visit_context);
const char *CJVMRangeStatusName(CJVMRangeStatus status);
int CJQueryDarwinVMEntry(uintptr_t cursor, CJVMEntry *entry, void *context);
