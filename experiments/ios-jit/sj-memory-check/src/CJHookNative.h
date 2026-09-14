#pragma once
#include <stddef.h>
#include <stdint.h>

typedef void (*CJHookLog)(const char *event, uintptr_t rx, uintptr_t rw, size_t length,
                          const char *detail, int actual, int expected);
void CJHookSetLog(CJHookLog log);
void *CJResolveHookNative(const char *library, const char *entry);
size_t CJHookPatchCount(void);
size_t CJHookRejectedCount(void);
void CJHookMark(const char *stage, int state, int actual, int expected);
