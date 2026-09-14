/* Compile-only ABI probe. This file is not linked into any product.
 * Protocol reference: StikDebug/StikJIT Resources/universal.js at
 * 3623e725876f76aecb0520582ad6194bacb15d39.
 * Never execute either function without the matching debugger script attached.
 */
#include <stddef.h>

#if !defined(__aarch64__)
#error This probe requires an Apple arm64 device target.
#endif

__attribute__((naked, noinline, optnone, used))
void *CelesteJit26PrepareRegion(void *address __attribute__((unused)),
                              size_t length __attribute__((unused))) {
    __asm__("mov x16, #1\n"
            "brk #0xf00d\n"
            "ret\n");
}

__attribute__((naked, noinline, optnone, used))
void CelesteJit26Detach(void) {
    __asm__("mov x16, #0\n"
            "brk #0xf00d\n"
            "ret\n");
}
