// Reuse the accepted alias allocator without changing its source or archives.
// Mono may initialize a thunk area before checking an allocation for NULL.
// Exhaustion must therefore stop here, after recording a native diagnostic.
#define cj_code_arena_initialize cj_base_code_arena_initialize
#include "../../managed-canary/src/CJCodeArena.c"
#undef cj_code_arena_initialize

static CJCodeEvent hook_arena_event;
static void CJHookArenaEvent(const char *name, uintptr_t address, size_t length, size_t used_bytes) {
    if (hook_arena_event) hook_arena_event(name, address, length, used_bytes);
    if (!strcmp(name, "code_allocation_failed")) {
        if (hook_arena_event) hook_arena_event("jit_code_budget_exhausted", address, length, used_bytes);
        // Returning NULL continues into Mono's thunk memset and a misleading
        // SIGSEGV. Aborting is terminal, not an in-process recovery mechanism.
        abort();
    }
}

int cj_code_arena_initialize(const CJCodeRegion input[2], size_t page, CJCodeEvent event) {
    if (!cj_base_code_arena_initialize(input, page, CJHookArenaEvent)) return 0;
    hook_arena_event = event;
    return 1;
}
