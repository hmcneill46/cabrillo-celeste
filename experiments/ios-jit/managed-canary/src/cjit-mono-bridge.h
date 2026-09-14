#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void *cj_mono_code_alloc(size_t size);
int cj_mono_owns_code(const void *address);
void *cj_mono_writable(void *address, size_t length);
void cj_mono_flush(void *address, size_t length);
#ifdef __cplusplus
}
#endif
#ifdef CJ_MONO_IOS_JIT
#define CJ_CODE_WRITE(p, n) cj_mono_writable((void *)(p), (size_t)(n))
#else
#define CJ_CODE_WRITE(p, n) (p)
#endif
