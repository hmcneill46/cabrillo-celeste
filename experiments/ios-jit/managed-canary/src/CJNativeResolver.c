#include "CJNativeResolver.h"
#include <stdint.h>
#include <string.h>
extern void *CJResolveSystemNative(const char *entry);
extern int32_t CJCanaryInvokeCallback(int32_t (*callback)(int32_t), int32_t challenge);

void *CJResolveNativeLibrary(const char *library, const char *entry) {
    if (!library || !entry) return NULL;
    // The pinned Unix/iOS BCL names libSystem.Native. Accept the equivalent
    // explicit names used by other .NET hosts; never match unrelated libraries.
    if (!strcmp(library, "libSystem.Native") || !strcmp(library, "System.Native") ||
        !strcmp(library, "libSystem.Native.dylib")) return CJResolveSystemNative(entry);
    if (!strcmp(library, "CJCanaryNative") && !strcmp(entry, "CJCanaryInvokeCallback"))
        return (void *)&CJCanaryInvokeCallback;
    return NULL;
}
