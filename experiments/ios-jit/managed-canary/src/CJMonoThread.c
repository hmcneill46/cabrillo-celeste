#include "CJMonoThread.h"
#include <mono/metadata/threads.h>

int CJDetachManagedWorker(void) {
    MonoThread *thread = mono_thread_current();
    if (!thread) return 0;
    // mono_jit_init_version leaves the embedding thread GC-safe. Detach itself
    // ends by entering GC-safe mode, which is not nestable. Enter GC-unsafe
    // explicitly first, as the pinned runtime's detach-if-exiting path does.
    // This transition is deliberately unbalanced: detach consumes it. Exiting
    // the region again afterward would repeat the same double-blocking error.
    void *stack_anchor = NULL;
    (void)mono_threads_enter_gc_unsafe_region_unbalanced(&stack_anchor);
    mono_threads_assert_gc_unsafe_region();
    mono_thread_detach(thread);
    mono_threads_assert_gc_safe_region();
    return mono_thread_current() == NULL;
}
