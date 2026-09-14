#include "CJNativeResolver.h"
#include <assert.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static void *system_native;
void *CJResolveSystemNative(const char *entry) { return dlsym(system_native, entry); }
int main(int argc, char **argv) {
    assert(argc == 2);
    system_native = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL); assert(system_native);
    const char *libraries[] = {"libSystem.Native", "System.Native", "libSystem.Native.dylib"};
    const char *entries[] = {"SystemNative_SchedGetCpu", "SystemNative_LChflagsCanSetHiddenFlag", "SystemNative_GetEnv"};
    for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) {
        void *result = CJResolveNativeLibrary(libraries[i], entries[j]);
        assert(result && result == dlsym(system_native, entries[j]));
    }
    setenv("CELESTE_JIT_RESOLVER_HOST_CHECK", "native-import-ok", 1);
    char *(*get_env)(const char *) = CJResolveNativeLibrary("libSystem.Native", "SystemNative_GetEnv");
    assert(!strcmp(get_env("CELESTE_JIT_RESOLVER_HOST_CHECK"), "native-import-ok"));
    assert(CJResolveNativeLibrary("CJCanaryNative", "CJCanaryInvokeCallback"));
    assert(!CJResolveNativeLibrary(NULL, "SystemNative_GetEnv"));
    assert(!CJResolveNativeLibrary("libSystem.Native", NULL));
    assert(!CJResolveNativeLibrary("libSystem.Native", "DefinitelyMissing"));
    assert(!CJResolveNativeLibrary("UnrelatedLibrary", "SystemNative_GetEnv"));
    assert(!CJResolveNativeLibrary("CJCanaryNative", "DefinitelyMissing"));
    puts("PASS: exact BCL library name and aliases resolve the three observed failed imports; actual SystemNative_GetEnv round trip and unknown-library rejection.");
    dlclose(system_native);
}
