#include "CJCodeArena.h"
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <libkern/OSCacheControl.h>

static CJCodeRegion regions[2];
static size_t used[2], page_size, allocations;
static CJCodeEvent record;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static int overlaps(uintptr_t a, size_t n, uintptr_t b, size_t m) {
    return n && m && a < b + m && b < a + n;
}
int cj_code_arena_initialize(const CJCodeRegion input[2], size_t page, CJCodeEvent event) {
    if (!page || (page & (page - 1))) return 0;
    for (int i = 0; i < 2; ++i) {
        const CJCodeRegion *r = &input[i];
        if (!r->rx || !r->rw || !r->length || r->rx % page || r->rw % page || r->length % page ||
            r->length > UINTPTR_MAX - r->rx || r->length > UINTPTR_MAX - r->rw) return 0;
    }
    uintptr_t starts[4] = {input[0].rx, input[0].rw, input[1].rx, input[1].rw};
    size_t lengths[4] = {input[0].length, input[0].length, input[1].length, input[1].length};
    for (int i = 0; i < 4; i++) for (int j = i + 1; j < 4; j++)
        if (overlaps(starts[i], lengths[i], starts[j], lengths[j])) return 0;
    pthread_mutex_lock(&lock);
    if (page_size) { pthread_mutex_unlock(&lock); return 0; }
    memcpy(regions, input, sizeof(regions)); page_size = page; record = event;
    pthread_mutex_unlock(&lock);
    return 1;
}
size_t cj_code_arena_used(void) {
    pthread_mutex_lock(&lock); size_t result = used[0] + used[1]; pthread_mutex_unlock(&lock); return result;
}
size_t cj_code_arena_allocations(void) {
    pthread_mutex_lock(&lock); size_t result = allocations; pthread_mutex_unlock(&lock); return result;
}
void *cj_mono_code_alloc(size_t length) {
    void *result = NULL;
    pthread_mutex_lock(&lock);
    if (page_size && length && length <= SIZE_MAX - (page_size - 1)) {
        size_t rounded = (length + page_size - 1) & ~(page_size - 1);
        for (int i = 0; i < 2; i++) {
            if (rounded > regions[i].length - used[i]) continue;
            result = (void *)(regions[i].rx + used[i]);
            memset((void *)(regions[i].rw + used[i]), 0, rounded);
            used[i] += rounded; allocations++; break;
        }
    }
    size_t total = used[0] + used[1];
    pthread_mutex_unlock(&lock);
    if (record) record(result ? "code_allocation" : "code_allocation_failed", (uintptr_t)result, length, total);
    return result;
}
int cj_mono_owns_code(const void *address) {
    uintptr_t p = (uintptr_t)address;
    for (int i = 0; i < 2; ++i) if (p >= regions[i].rx && p - regions[i].rx < regions[i].length) return 1;
    return 0;
}
int cj_code_arena_contains_allocation(const void *address, size_t length) {
    uintptr_t p = (uintptr_t)address; int result = 0;
    pthread_mutex_lock(&lock);
    for (int i = 0; i < 2; ++i)
        if (length && p >= regions[i].rx && p - regions[i].rx <= used[i] && length <= used[i] - (p - regions[i].rx)) result = 1;
    pthread_mutex_unlock(&lock); return result;
}
void *cj_mono_writable(void *address, size_t length) {
    uintptr_t p = (uintptr_t)address;
    if (length > UINTPTR_MAX - p) goto invalid;
    for (int i = 0; i < 2; ++i) {
        CJCodeRegion *r = &regions[i];
        if (p >= r->rx && p - r->rx < r->length) {
            if (length > r->length - (p - r->rx)) goto invalid;
            return (void *)(r->rw + (p - r->rx));
        }
        if (overlaps(p, length, r->rx, r->length)) goto invalid;
        if (overlaps(p, length, r->rw, r->length) && !(p >= r->rw && length <= r->length - (p - r->rw))) goto invalid;
    }
    // Mono also emits temporary method buffers and data in ordinary writable memory.
    return address;
invalid:
    if (record) record("code_write_bounds_failure", p, length, cj_code_arena_used());
    abort();
}
void cj_mono_flush(void *address, size_t length) {
    void *write_address = cj_mono_writable(address, length);
    sys_dcache_flush(write_address, length);
    sys_icache_invalidate(address, length);
}
