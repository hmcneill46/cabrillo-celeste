#include "CJMonoThread.h"
#include "CJNativeResolver.h"
#include <mono/jit/jit.h>
#include <mono/jit/mono-private-unstable.h>
#include <mono/metadata/assembly.h>
#include <mono/metadata/appdomain.h>
#include <mono/metadata/class.h>
#include <mono/metadata/object.h>
#include <mono/metadata/threads.h>
#include <mono/metadata/mono-gc.h>
#include <assert.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>

// Additional exact signatures from the pinned runtime's mono-threads-api.h.
extern void *mono_threads_enter_gc_unsafe_region(void **stack_pointer);
extern void mono_threads_exit_gc_unsafe_region(void *cookie, void **stack_pointer);
extern void *mono_threads_enter_gc_safe_region_unbalanced(void **stack_pointer);
static void *system_native;
static MonoDomain *domain;
static MonoClass *entry_class;
void *CJResolveSystemNative(const char *entry) { return dlsym(system_native, entry); }
const void *GlobalizationResolveDllImport(const char *entry) { (void)entry; return NULL; }

static void invoke(const char *stage, int challenge, int expected) {
    void *stack_anchor = NULL;
    void *cookie = mono_threads_enter_gc_unsafe_region(&stack_anchor);
    MonoMethod *method = mono_class_get_method_from_name(entry_class, stage, 1); assert(method);
    void *args[] = {&challenge}; MonoObject *exception = NULL;
    MonoObject *boxed = mono_runtime_invoke(method, NULL, args, &exception);
    if (exception) fprintf(stderr, "Managed exception in %s: %s\n", stage, mono_class_get_name(mono_object_get_class(exception)));
    assert(!exception && boxed && mono_object_get_class(boxed) == mono_get_int32_class());
    assert(*(int *)mono_object_unbox(boxed) == expected);
    mono_threads_exit_gc_unsafe_region(cookie, &stack_anchor);
}

int main(int argc, char **argv) {
    assert(argc == 5);
    struct rlimit limit = {0, 0}; setrlimit(RLIMIT_CORE, &limit);
    setvbuf(stdout, NULL, _IONBF, 0); setvbuf(stderr, NULL, _IONBF, 0);
    system_native = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL); assert(system_native);
    setenv("DOTNET_SYSTEM_GLOBALIZATION_INVARIANT", "1", 1);
    setenv("CELESTE_JIT_CANARY_NATIVE_CHECK", "build-5-native-imports", 1);
    char resolver[64]; snprintf(resolver, sizeof(resolver), "%p", (void *)&CJResolveNativeLibrary);
    const char *keys[] = {"RUNTIME_IDENTIFIER", "APP_CONTEXT_BASE_DIRECTORY", "APP_PATHS", "TRUSTED_PLATFORM_ASSEMBLIES", "PINVOKE_OVERRIDE", "System.Globalization.Invariant", "System.Diagnostics.Tracing.EventSource.IsSupported"};
    const char *values[] = {"osx-x64", argv[2], argv[2], getenv("CJIT_TEST_TPA"), resolver, "true", "false"};
    assert(values[3]);
    mono_set_assemblies_path(argv[2]); mono_jit_set_aot_mode(MONO_AOT_MODE_NONE);
    assert(monovm_initialize(7, keys, values) == 0);
    domain = mono_jit_init_version("cjit-lifecycle-regression", "mobile"); assert(domain);
    mono_gc_init_finalizer_thread();
    MonoAssembly *assembly = mono_domain_assembly_open(domain, argv[3]); assert(assembly);
    entry_class = mono_class_from_name(mono_assembly_get_image(assembly), "CelesteJIT.Canary", "Entry"); assert(entry_class);
    invoke("Arithmetic", atoi(argv[4]), 15);
    assert(CJDetachManagedWorker());
    puts("PASS_NATIVE_VISIBILITY_FIXTURE");
    return 0;
}
