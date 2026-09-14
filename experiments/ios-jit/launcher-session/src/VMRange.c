#include "VMRange.h"
#include <unistd.h>

CJVMRangeReport CJInspectVMRangeForPageSize(uintptr_t start, size_t length, size_t page_size,
                                         CJVMQuery query, void *query_context,
                                         CJVMVisit visit, void *visit_context) {
    CJVMRangeReport report = {.status = CJVMRangeInvalidBounds, .common_protection = -1};
    if (!query || length == 0 || length > UINTPTR_MAX - start ||
        page_size == 0 || (page_size & (page_size - 1)) != 0) return report;
    uintptr_t cursor = start, end = start + length;
    // Subtract page indices, avoiding overflow in length + page_size - 1.
    // Darwin VM entries cannot divide an OS page. Malformed synthetic query
    // results still have a finite traversal bound, with no skipped tail.
    report.entry_limit = (end - 1) / page_size - start / page_size + 1;
    while (cursor < end) {
        if (report.entry_count >= report.entry_limit) { report.status = CJVMRangeTooManyEntries; return report; }
        CJVMEntry entry = {0};
        report.query_result = query(cursor, &entry, query_context);
        if (report.query_result != 0) { report.status = CJVMRangeQueryFailed; return report; }
        report.entry_count++;
        if (entry.length == 0 || entry.length > UINTPTR_MAX - entry.address || entry.address + entry.length <= cursor) {
            if (visit) visit(cursor, &entry, 0, visit_context);
            report.status = CJVMRangeInvalidEntry; return report;
        }
        // vm_region may return the NEXT mapping when the requested address is a
        // hole. Never advance across that hole or count those bytes as covered.
        if (entry.address > cursor) {
            if (visit) visit(cursor, &entry, 0, visit_context);
            report.status = CJVMRangeGap; return report;
        }
        uintptr_t next = entry.address + entry.length;
        if (next > end) next = end;
        size_t checked = next - cursor;
        if (report.entry_count == 1) {
            report.common_protection = entry.protection;
            report.maximum_protection_intersection = entry.maximum_protection;
        } else {
            if (report.common_protection != entry.protection) report.common_protection = -1;
            report.maximum_protection_intersection &= entry.maximum_protection;
        }
        report.union_protection |= entry.protection;
        report.covered_bytes += checked;
        if (visit) visit(cursor, &entry, checked, visit_context);
        cursor = next;
    }
    report.status = CJVMRangeComplete;
    return report;
}

CJVMRangeReport CJInspectVMRange(uintptr_t start, size_t length, CJVMQuery query,
                                void *query_context, CJVMVisit visit, void *visit_context) {
    int page_size = getpagesize();
    return CJInspectVMRangeForPageSize(start, length, page_size > 0 ? (size_t)page_size : 0,
                                      query, query_context, visit, visit_context);
}

const char *CJVMRangeStatusName(CJVMRangeStatus status) {
    switch (status) {
        case CJVMRangeComplete: return "complete";
        case CJVMRangeInvalidBounds: return "invalid_bounds";
        case CJVMRangeQueryFailed: return "query_failed";
        case CJVMRangeGap: return "gap";
        case CJVMRangeInvalidEntry: return "invalid_entry";
        case CJVMRangeTooManyEntries: return "too_many_entries";
    }
    return "unknown";
}
