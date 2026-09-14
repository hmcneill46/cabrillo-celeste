#pragma once
#include "cjit-mono-bridge.h"
typedef struct { uintptr_t rx, rw; size_t length; } CJCodeRegion;
typedef void (*CJCodeEvent)(const char *name, uintptr_t address, size_t length, size_t used);
// Initialize once, only after the caller has validated mappings and detach.
int cj_code_arena_initialize(const CJCodeRegion regions[2], size_t page_size, CJCodeEvent event);
size_t cj_code_arena_used(void);
size_t cj_code_arena_allocations(void);
int cj_code_arena_contains_allocation(const void *address, size_t length);
