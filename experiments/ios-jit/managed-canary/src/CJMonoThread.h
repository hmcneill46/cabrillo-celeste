#pragma once

// Exact MONO_API signatures from the pinned Mono utils/mono-threads-api.h.
// The official iOS embedding header subset omits these cooperative-GC APIs.
void *mono_threads_enter_gc_unsafe_region(void **stack_pointer);
void mono_threads_exit_gc_unsafe_region(void *cookie, void **stack_pointer);
void *mono_threads_enter_gc_unsafe_region_unbalanced(void **stack_pointer);
void mono_threads_assert_gc_unsafe_region(void);
void mono_threads_assert_gc_safe_region(void);

// Detach a native worker from managed Mono, consuming the GC-unsafe transition.
// Returns true only after the managed thread object has been cleared.
int CJDetachManagedWorker(void);
