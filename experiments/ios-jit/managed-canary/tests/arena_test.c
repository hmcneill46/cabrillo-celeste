#include "CJCodeArena.h"
#define G_DISABLE_ASSERT 1
#include <mono/arch/arm64/arm64-codegen.h>
#include <assert.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>

static CJCodeRegion create_region(size_t bytes) {
    char name[] = "/tmp/cjit-arena-test-XXXXXX";
    int fd = mkstemp(name); assert(fd >= 0); unlink(name); assert(ftruncate(fd, bytes) == 0);
    void *rx = mmap(NULL, bytes, PROT_READ, MAP_SHARED, fd, 0);
    void *rw = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); close(fd);
    assert(rx != MAP_FAILED && rw != MAP_FAILED);
    return (CJCodeRegion){(uintptr_t)rx, (uintptr_t)rw, bytes};
}
static void *allocate_worker(void *arg) { return cj_mono_code_alloc(*(size_t *)arg); }
int main(void) {
    size_t page = getpagesize(); CJCodeRegion r[2] = {create_region(8 * page), create_region(8 * page)};
    CJCodeRegion bad[2] = {r[0], r[0]};
    assert(!cj_code_arena_initialize(bad, page, NULL));
    assert(!cj_code_arena_initialize(r, 3, NULL));
    assert(cj_code_arena_initialize(r, page, NULL));
    assert(!cj_code_arena_initialize(r, page, NULL));
    assert(!cj_mono_code_alloc(0)); assert(!cj_mono_code_alloc(SIZE_MAX));
    guint8 *base = cj_mono_code_alloc(page + 1), *p = base;
    assert((uintptr_t)base == r[0].rx && cj_code_arena_used() == 2 * page);
    // These are the actual patched Mono macros. RX is read-only on this Intel
    // host: an unpatched direct store would fault. Do not execute ARM64 bytes.
    arm_movzw(p, ARMREG_R0, 123, 0);
    arm_b(p, base + 128);
    arm_retx(p, ARMREG_LR);
    assert(p == base + 12);
    assert(((guint32 *)base)[0] == (0x52800000U | (123U << 5)));
    assert(((guint32 *)base)[1] == 0x1400001fU); // branch computed from logical RX PC
    assert(((guint32 *)base)[2] == 0xd65f03c0U);
    arm_set_ins_bits(base, 5, 16, 456);
    assert(*(guint32 *)base == (0x52800000U | (456U << 5)));
    assert(memcmp(base, (void *)r[0].rw, 12) == 0);
    cj_mono_flush(base, 12);
    guint8 temporary[16], *heap = temporary;
    arm_retx(heap, ARMREG_LR); assert(*(guint32 *)temporary == 0xd65f03c0U);
    assert(cj_mono_writable(temporary, sizeof(temporary)) == temporary);
    assert(cj_mono_writable((void *)r[0].rw, page) == (void *)r[0].rw);
    assert(cj_code_arena_contains_allocation(base, 2 * page));
    assert(!cj_code_arena_contains_allocation(base, 2 * page + 1));
    assert(!cj_code_arena_contains_allocation((void *)r[0].rw, 1));
    assert(cj_mono_code_alloc(6 * page) == (void *)(r[0].rx + 2 * page));
    assert(!cj_mono_code_alloc(9 * page));
    // Concurrent reservations must be distinct, aligned and use the second arena.
    pthread_t threads[8]; void *results[8];
    for (int i = 0; i < 8; i++) assert(pthread_create(&threads[i], NULL, allocate_worker, &page) == 0);
    for (int i = 0; i < 8; i++) {
        assert(pthread_join(threads[i], &results[i]) == 0);
        assert((uintptr_t)results[i] >= r[1].rx && (uintptr_t)results[i] < r[1].rx + r[1].length);
        for (int j = 0; j < i; j++) assert(results[i] != results[j]);
    }
    assert(!cj_mono_code_alloc(1)); assert(cj_code_arena_used() == 16 * page);
    assert(cj_code_arena_allocations() == 10);
    struct rlimit limit = {0, 0}; setrlimit(RLIMIT_CORE, &limit);
    pid_t child = fork(); assert(child >= 0);
    if (!child) { cj_mono_writable((void *)(r[1].rx + r[1].length - 1), 2); _exit(99); }
    int status; assert(waitpid(child, &status, 0) == child);
    assert(WIFSIGNALED(status) && WTERMSIG(status) == SIGABRT);
    puts("PASS: real ARM64 emit/patch macros through read-only RX aliases; PC-relative branch; heap buffers; bounds; exhaustion; concurrent reservations.");
}
