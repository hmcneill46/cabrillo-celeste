#include "CJCodeArena.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>

// Only the surrounding Mono object model is mocked. The two switch cases below
// are extracted verbatim from the pinned runtime by check_switch_tables.py.
typedef void *gpointer;
typedef struct { int native_offset; } MonoBasicBlock;
typedef struct { int tag; } MonoMemoryManager;
typedef struct { int dynamic; } MonoMethod;
typedef struct { void *code_mp; } DynamicInfo;
typedef struct { MonoBasicBlock **table; int table_size; } SwitchTable;
typedef struct { struct { SwitchTable *table; } data; } MonoJumpInfo;
typedef struct { MonoMethod *method; DynamicInfo *dynamic_info; MonoMemoryManager *mem_manager; } MonoCompile;
#define MONO_PATCH_INFO_SWITCH 1
#define GINT_TO_POINTER(i) ((gpointer)(intptr_t)(i))
#define GPOINTER_TO_INT(p) ((int)(intptr_t)(p))
#define g_assert assert
static int mono_aot_only = 0;
static MonoMemoryManager manager = {1};
static DynamicInfo dynamic = {&manager};
static int static_reserves, dynamic_reserves;
static void *mono_mem_manager_code_reserve(MonoMemoryManager *m, size_t n) {
    assert(m == &manager); static_reserves++; return cj_mono_code_alloc(n);
}
static void *mono_code_manager_reserve(void *m, size_t n) {
    assert(m == &manager); dynamic_reserves++; return cj_mono_code_alloc(n);
}
static void *mono_mem_manager_alloc(MonoMemoryManager *m, size_t n) {
    (void)m; (void)n; abort(); // This canary must never enter the AOT branch.
}
static MonoMemoryManager *m_method_get_mem_manager(MonoMethod *m) { assert(m); return &manager; }
static DynamicInfo *mono_dynamic_code_hash_lookup(MonoMethod *m) { assert(m->dynamic); return &dynamic; }
static void mono_codeman_enable_write(void) {}
static void mono_codeman_disable_write(void) {}

static void postprocess(MonoCompile *cfg, MonoJumpInfo *patch_info) {
    int i;
    switch (MONO_PATCH_INFO_SWITCH) {
        /* POSTPROCESS_CASE */
    }
}
static gpointer resolve(MonoMethod *method, MonoJumpInfo *patch_info, unsigned char *code) {
    MonoMemoryManager *mem_manager = &manager;
    gpointer target = NULL;
    switch (MONO_PATCH_INFO_SWITCH) {
        /* RESOLVE_CASE */
    }
    return target;
}
static CJCodeRegion create_region(size_t bytes) {
    char name[] = "/tmp/cjit-switch-test-XXXXXX";
    int fd = mkstemp(name); assert(fd >= 0); unlink(name); assert(ftruncate(fd, bytes) == 0);
    void *rx = mmap(NULL, bytes, PROT_READ, MAP_SHARED, fd, 0);
    void *rw = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0); close(fd);
    assert(rx != MAP_FAILED && rw != MAP_FAILED && rx != rw);
    return (CJCodeRegion){(uintptr_t)rx, (uintptr_t)rw, bytes};
}
int main(int argc, char **argv) {
    struct rlimit limit = {0, 0}; setrlimit(RLIMIT_CORE, &limit);
    size_t page = getpagesize();
    CJCodeRegion regions[2] = {create_region(16 * page), create_region(16 * page)};
    assert(cj_code_arena_initialize(regions, page, NULL));
    unsigned char *code = cj_mono_code_alloc(256); assert(code);
    MonoBasicBlock blocks[] = {{4}, {28}, {128}};
    for (int kind = 0; kind < 2; kind++) {
        MonoMethod method = {kind}; MonoCompile cfg = {&method, &dynamic, &manager};
        MonoBasicBlock *input[] = {&blocks[0], NULL, &blocks[1], &blocks[2]};
        SwitchTable table = {input, 4}; MonoJumpInfo patch = {{&table}};
        if (argc > 1 && strstr(argv[1], "dynamic") && !kind) continue;
        if (argc > 1 && !strncmp(argv[1], "resolve", 7)) {
            // Exercise the second old write independently of the first one.
            gpointer offsets[] = {GINT_TO_POINTER(4), NULL, GINT_TO_POINTER(28), GINT_TO_POINTER(128)};
            table.table = (MonoBasicBlock **)offsets;
            resolve(&method, &patch, code);
            abort(); // Unpatched source must have faulted on its RX store.
        }
        postprocess(&cfg, &patch);
        if (argc > 1) abort();
        gpointer *offsets = (gpointer *)table.table;
        assert(cj_code_arena_contains_allocation(offsets, sizeof(input)));
        assert(GPOINTER_TO_INT(offsets[0]) == 4 && offsets[1] == NULL);
        assert(GPOINTER_TO_INT(offsets[2]) == 28 && GPOINTER_TO_INT(offsets[3]) == 128);
        gpointer *targets = resolve(&method, &patch, code);
        assert(cj_code_arena_contains_allocation(targets, sizeof(input)));
        assert(targets[0] == code + 4 && targets[1] == code);
        assert(targets[2] == code + 28 && targets[3] == code + 128);
        assert(targets != cj_mono_writable(targets, sizeof(input)));
    }
    assert(static_reserves == 2 && dynamic_reserves == 2);
    puts("PASS: actual Mono static and dynamic switch-table cases write through RW; offsets and final targets retain RX identity, including eliminated entries.");
}
