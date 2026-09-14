#include "CJCodeArena.h"
#include "CJHookMemory.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>

static const size_t page = 16384;
static void *aligned_mapping(int fd, size_t length, int protection) {
    void *reservation = mmap(NULL, length + page, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    assert(reservation != MAP_FAILED);
    uintptr_t start = ((uintptr_t)reservation + page - 1) & ~(page - 1);
    size_t prefix = start - (uintptr_t)reservation;
    if (prefix) assert(!munmap(reservation, prefix));
    if (page - prefix) assert(!munmap((void *)(start + length), page - prefix));
    // Replace only our own reserved address range, leaving adjacent memory alone.
    void *mapped = mmap((void *)start, length, protection, MAP_SHARED | MAP_FIXED, fd, 0);
    assert(mapped == (void *)start); return mapped;
}
static CJCodeRegion region(size_t length) {
    char name[] = "/tmp/cjit-hook-capacity-XXXXXX";
    int fd = mkstemp(name); assert(fd >= 0); unlink(name); assert(!ftruncate(fd, length));
    void *rx = aligned_mapping(fd, length, PROT_READ);
    void *rw = aligned_mapping(fd, length, PROT_READ | PROT_WRITE); close(fd);
    return (CJCodeRegion){(uintptr_t)rx, (uintptr_t)rw, length};
}
static void event(const char *name, uintptr_t address, size_t length, size_t used) {
    (void)address;
    if (strstr(name, "failed") || strstr(name, "exhausted")) {
        printf("EVENT %s requested=%zu reserved=%zu\n", name, length, used); fflush(stdout);
    }
}
int main(int argc, char **argv) {
    assert(argc == 2); struct rlimit limit = {0, 0}; setrlimit(RLIMIT_CORE, &limit);
    size_t sizes[20000], count = 0; FILE *file = fopen(argv[1], "r"); assert(file);
    while (count < 20000 && fscanf(file, "%zu", &sizes[count]) == 1) count++;
    assert(feof(file) && count); fclose(file);
    size_t length = CJ_HOOK_ARENA_LENGTH;
    CJCodeRegion r[2] = {region(length), region(length)};
    assert(cj_code_arena_initialize(r, page, event));
#ifdef CJ_TEST_PHYSICAL_FAILURE
    assert(count == 562);
    const int repetitions = 1;
#else
    const int repetitions = 1;
#endif
    for (int repetition = 0; repetition < repetitions; repetition++) {
        for (size_t i = 0; i < count; i++) {
            unsigned char *address = cj_mono_code_alloc(sizes[i]);
#ifdef CJ_TEST_PHYSICAL_FAILURE
            if (!address) {
                assert(repetition == 0 && i == 561 && sizes[i] == 262144 && cj_code_arena_used() == 134037504);
                puts("PASS_REPRODUCED_BUILD15_EXACT_EXHAUSTION"); return 0;
            }
#else
            assert(address && (uintptr_t)address % page == 0 && cj_code_arena_contains_allocation(address, sizes[i]));
            unsigned char *rw = cj_mono_writable(address, sizes[i]); assert(rw != address);
            assert(address[0] == 0 && address[sizes[i] - 1] == 0);
            rw[0] = 0x3a; rw[sizes[i] - 1] = 0xa3; cj_mono_flush(address, sizes[i]);
            assert(address[0] == (sizes[i] == 1 ? 0xa3 : 0x3a) && address[sizes[i] - 1] == 0xa3);
#endif
        }
        printf("PASS_REPLAYED_HOST_TRACE repetition=%d allocations=%zu reserved=%zu capacity=%zu\n",
               repetition+1,cj_code_arena_allocations(),cj_code_arena_used(),2*length);fflush(stdout);
    }
#ifdef CJ_TEST_PHYSICAL_FAILURE
    assert(0 && "Did not reproduce the exact physical failure");
#else
    pid_t child = fork(); assert(child >= 0);
    if (!child) { cj_mono_code_alloc(length + page); _exit(99); }
    int status; assert(waitpid(child, &status, 0) == child);
    assert(WIFSIGNALED(status) && WTERMSIG(status) == SIGABRT);
    puts("PASS_EXHAUSTION_STOPS_BEFORE_MONO_USES_NULL");
#endif
}
