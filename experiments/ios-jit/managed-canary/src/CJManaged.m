#import "CJManaged.h"
#import "CJCodeArena.h"
#import "CJNativeResolver.h"
#import "CJMonoThread.h"
#include <mono/jit/jit.h>
#include <mono/jit/mono-private-unstable.h>
#include <mono/metadata/assembly.h>
#include <mono/metadata/appdomain.h>
#include <mono/metadata/class.h>
#include <mono/metadata/loader.h>
#include <mono/metadata/mono-config.h>
#include <mono/metadata/debug-helpers.h>
#include <mono/metadata/object.h>
#include <mono/metadata/threads.h>
#include <mono/metadata/mono-gc.h>
#include <mono/metadata/profiler.h>
#include <mono/utils/mono-logger.h>
#include <stdatomic.h>

static CJManagedLog gLog;
static _Atomic(unsigned) gJITCount, gUnownedJIT, gDynamicCount, gDynamicSwitchCount, gFailedJIT, gArithmeticCount;
static MonoMethod *gArithmetic;

// This canary deliberately uses invariant globalization. Full ICU/Apple culture
// support belongs in the later game host; unexpected calls remain unresolved.
const void *GlobalizationResolveDllImport(const char *entry) {
    if (gLog) gLog(@"invariant_globalization_entry_unavailable", @{@"entry": [NSString stringWithUTF8String:entry] ?: @"unknown"});
    return NULL;
}

static NSString *CJString(const char *s) { return s ? ([NSString stringWithUTF8String:s] ?: @"<invalid UTF-8>") : @"<null>"; }
static NSString *CJPointer(const void *p) { return [NSString stringWithFormat:@"0x%llx", (unsigned long long)(uintptr_t)p]; }
static NSString *CJMethodName(MonoMethod *method) {
    char *name = mono_method_full_name(method, 1);
    NSString *result = CJString(name); mono_free(name); return result;
}
static void CJTrace(const char *domain, const char *level, const char *message, mono_bool fatal, void *user) {
    (void)user;
    gLog(@"mono_log", @{@"domain": CJString(domain), @"level": CJString(level), @"message": CJString(message), @"fatal": @(fatal)});
    if (fatal) abort();
}
static void CJPrint(const char *message, mono_bool newline) {
    (void)newline; gLog(@"mono_output", @{@"message": CJString(message)});
}
static void CJBegin(MonoProfiler *profiler, MonoMethod *method) {
    (void)profiler; gLog(@"mono_jit_begin", @{@"method": CJMethodName(method)});
}
static void CJFailed(MonoProfiler *profiler, MonoMethod *method) {
    (void)profiler; atomic_fetch_add(&gFailedJIT, 1);
    gLog(@"mono_jit_failed", @{@"method": CJMethodName(method)});
}
static void CJDone(MonoProfiler *profiler, MonoMethod *method, MonoJitInfo *info) {
    (void)profiler;
    void *code = mono_jit_info_get_code_start(info);
    int size = mono_jit_info_get_code_size(info);
    BOOL owned = size > 0 && cj_code_arena_contains_allocation(code, (size_t)size);
    atomic_fetch_add(&gJITCount, 1);
    if (!owned) atomic_fetch_add(&gUnownedJIT, 1);
    if (owned && method == gArithmetic) atomic_fetch_add(&gArithmeticCount, 1);
    if (owned && strncmp(mono_method_get_name(method), "CJIT_Dynamic_", 13) == 0) atomic_fetch_add(&gDynamicCount, 1);
    if (owned && strncmp(mono_method_get_name(method), "CJIT_DynamicSwitch_", 19) == 0) atomic_fetch_add(&gDynamicSwitchCount, 1);
    gLog(@"mono_jit_done", @{@"method": CJMethodName(method), @"rx": CJPointer(code), @"code_bytes": @(size), @"in_prepared_allocation": @(owned)});
}
static void *CJPInvoke(const char *library, const char *entry) {
    void *result = CJResolveNativeLibrary(library, entry);
    gLog(@"pinvoke_resolution", @{@"library": CJString(library), @"entry": CJString(entry), @"resolved_in_static_table": @(result != NULL)});
    return result;
}
static BOOL CJInvokeUnsafe(MonoClass *klass, const char *name, int challenge, int expected) {
    MonoMethod *method = mono_class_get_method_from_name(klass, name, 1);
    gLog(@"managed_stage_start", @{@"stage": CJString(name), @"challenge": @(challenge), @"expected": @(expected), @"method_found": @(method != NULL)});
    if (!method) return NO;
    if (!strcmp(name, "Arithmetic")) gArithmetic = method;
    void *entry = mono_compile_method(method);
    MonoJitInfo *info = entry ? mono_jit_info_table_find(mono_domain_get(), entry) : NULL;
    BOOL compiled = info && mono_jit_info_get_method(info) == method &&
        cj_code_arena_contains_allocation(mono_jit_info_get_code_start(info), (size_t)mono_jit_info_get_code_size(info));
    gLog(@"managed_method_compiled", @{@"stage": CJString(name), @"entry": CJPointer(entry), @"verified_jit_info_in_prepared_arena": @(compiled)});
    if (!compiled) return NO;
    void *args[] = {&challenge}; MonoObject *exception = NULL;
    MonoObject *boxed = mono_runtime_invoke(method, NULL, args, &exception);
    if (exception) {
        MonoClass *type = mono_object_get_class(exception);
        gLog(@"managed_exception", @{@"stage": CJString(name), @"type": CJString(mono_class_get_name(type))});
        // Pin while requesting a managed stack/message; preserve the first event if formatting fails.
        uint32_t handle = mono_gchandle_new(exception, 0);
        MonoObject *formatError = NULL;
        MonoString *message = mono_object_to_string(mono_gchandle_get_target(handle), &formatError);
        if (message && !formatError) {
            char *utf8 = mono_string_to_utf8(message);
            gLog(@"managed_exception_detail", @{@"message": CJString(utf8)}); mono_free(utf8);
        }
        mono_gchandle_free(handle); return NO;
    }
    BOOL integer = boxed && mono_object_get_class(boxed) == mono_get_int32_class();
    int actual = integer ? *(int *)mono_object_unbox(boxed) : 0;
    BOOL pass = integer && actual == expected;
    gLog(pass ? @"managed_stage_pass" : @"managed_stage_fail", @{@"stage": CJString(name), @"actual": @(actual), @"expected": @(expected)});
    return pass;
}
static BOOL CJInvoke(MonoClass *klass, const char *name, int challenge, int expected) {
    // Protect managed references while compiling, invoking, inspecting a
    // returned box or formatting an exception. Restore the caller's mode on
    // every result path, including failure, before returning to native code.
    void *stack_anchor = NULL;
    void *cookie = mono_threads_enter_gc_unsafe_region(&stack_anchor);
    BOOL passed = CJInvokeUnsafe(klass, name, challenge, expected);
    mono_threads_exit_gc_unsafe_region(cookie, &stack_anchor);
    return passed;
}
BOOL CJManagedRun(NSURL *importedDLL, NSURL *frameworkDirectory, CJManagedLog log) {
    gLog = [log copy];
    gLog(@"mono_configuration_start", @{@"runtime": @"8.0.28", @"runtime_commit": @"46295af5828b062bbbf93a9cef50fd8cb9fbcb09",
          @"aot_disabled": @YES, @"interpreter_disabled": @YES, @"code_budget_bytes": @(2 * 4194304), @"imported_filename": importedDLL.lastPathComponent});
    // Use the same supported embedding property as the upstream AppleAppBuilder,
    // with explicit static symbols so LiveContainer's global dlsym scope is irrelevant.
    setenv("DOTNET_SYSTEM_GLOBALIZATION_INVARIANT", "1", 1);
    setenv("CELESTE_JIT_CANARY_NATIVE_CHECK", "build-5-native-imports", 1);
    const char *required[] = {"SystemNative_GetEnv", "SystemNative_SchedGetCpu", "SystemNative_LChflagsCanSetHiddenFlag"};
    for (size_t i = 0; i < sizeof(required) / sizeof(required[0]); i++) {
        BOOL found = CJResolveNativeLibrary("libSystem.Native", required[i]) != NULL;
        gLog(@"native_import_preflight", @{@"library": @"libSystem.Native", @"entry": CJString(required[i]), @"resolved": @(found)});
        if (!found) return NO;
    }
    unsetenv("MONO_ENV_OPTIONS"); unsetenv("MONO_AOT_MODE");
    mono_trace_set_log_handler(CJTrace, NULL);
    mono_trace_set_print_handler(CJPrint); mono_trace_set_printerr_handler(CJPrint);
    mono_trace_set_level_string("info");
    mono_set_signal_chaining(1); mono_set_crash_chaining(1);
    mono_set_assemblies_path(frameworkDirectory.fileSystemRepresentation);
    mono_jit_set_aot_mode(MONO_AOT_MODE_NONE);
    NSMutableArray<NSString *> *assemblies = [NSMutableArray array];
    NSArray<NSURL *> *files = [NSFileManager.defaultManager contentsOfDirectoryAtURL:frameworkDirectory includingPropertiesForKeys:nil options:0 error:NULL];
    for (NSURL *file in files) if ([file.pathExtension isEqualToString:@"dll"]) [assemblies addObject:file.path];
    [assemblies sortUsingSelector:@selector(compare:)];
    NSString *tpa = [assemblies componentsJoinedByString:@":"];
    char override[64]; snprintf(override, sizeof(override), "%p", (void *)&CJPInvoke);
    // Match the compiled-out EventPipe backend with the supported EventSource
    // feature switch. Native/JIT diagnostic callbacks remain enabled.
    const char *keys[] = {"RUNTIME_IDENTIFIER", "APP_CONTEXT_BASE_DIRECTORY", "APP_PATHS", "TRUSTED_PLATFORM_ASSEMBLIES", "PINVOKE_OVERRIDE", "System.Globalization.Invariant", "System.Diagnostics.Tracing.EventSource.IsSupported"};
    const char *values[] = {"ios-arm64", frameworkDirectory.fileSystemRepresentation, frameworkDirectory.fileSystemRepresentation, tpa.UTF8String, override, "true", "false"};
    gLog(@"runtime_feature_configuration", @{@"eventsource_supported": @NO, @"invariant_globalization": @YES});
    int initialized = monovm_initialize(7, keys, values);
    gLog(@"monovm_properties_ready", @{@"result": @(initialized), @"framework_assembly_count": @(assemblies.count)});
    if (initialized != 0 || assemblies.count < 10) return NO;
    MonoProfilerHandle profiler = mono_profiler_create(NULL);
    mono_profiler_set_jit_begin_callback(profiler, CJBegin);
    mono_profiler_set_jit_done_callback(profiler, CJDone);
    mono_profiler_set_jit_failed_callback(profiler, CJFailed);
    gLog(@"mono_runtime_init_start", @{});
    MonoDomain *domain = mono_jit_init_version("celeste-jit-canary", "mobile");
    if (!domain) { gLog(@"mono_runtime_init_failed", @{}); return NO; }
    gLog(@"mono_runtime_init_pass", @{@"runtime_build": CJString(mono_get_runtime_build_info())});
    gLog(@"mono_finalizer_init_start", @{});
    mono_gc_init_finalizer_thread();
    gLog(@"mono_finalizer_init_pass", @{});
    gLog(@"imported_assembly_load_start", @{});
    MonoAssembly *assembly = mono_domain_assembly_open(domain, importedDLL.fileSystemRepresentation);
    MonoImage *image = assembly ? mono_assembly_get_image(assembly) : NULL;
    MonoClass *klass = image ? mono_class_from_name(image, "CelesteJIT.Canary", "Entry") : NULL;
    BOOL passed = klass != NULL;
    gLog(@"imported_assembly_loaded", @{@"assembly_found": @(assembly != NULL), @"entry_class_found": @(klass != NULL), @"image_name": image ? CJString(mono_image_get_name(image)) : @"none"});
    int challenge = 100 + (int)arc4random_uniform(900);
    const char *stages[] = {"NativeImports", "Arithmetic", "SwitchTable", "Dynamic", "DynamicSwitch", "GenericAbi", "ExceptionsAndGC", "ThreadAndCallback"};
    int expected[] = {challenge + 5, (challenge * 31) ^ 0x13579bdf, challenge + 761, challenge * 3 + 37, challenge + 168, challenge * 14 + 13, challenge + 19, challenge + 24};
    for (size_t i = 0; i < sizeof(stages) / sizeof(stages[0]) && passed; i++) passed = CJInvoke(klass, stages[i], challenge, expected[i]);
    BOOL proof = atomic_load(&gArithmeticCount) > 0 && atomic_load(&gDynamicCount) > 0 &&
        atomic_load(&gDynamicSwitchCount) > 0 && atomic_load(&gUnownedJIT) == 0 && atomic_load(&gFailedJIT) == 0;
    gLog(@"managed_jit_evidence", @{@"stages_passed": @(passed), @"jit_done_count": @(atomic_load(&gJITCount)),
          @"arithmetic_jit_count": @(atomic_load(&gArithmeticCount)), @"dynamic_method_jit_count": @(atomic_load(&gDynamicCount)),
          @"dynamic_switch_jit_count": @(atomic_load(&gDynamicSwitchCount)),
          @"jit_outside_prepared_arena": @(atomic_load(&gUnownedJIT)), @"jit_failures": @(atomic_load(&gFailedJIT)),
          @"code_reserved_bytes": @(cj_code_arena_used()), @"code_allocations": @(cj_code_arena_allocations())});
    // One-shot process. No runtime cleanup/unload/reinitialization is attempted.
    // This worker leaves Mono before returning to the native launcher.
    gLog(@"managed_worker_detach_start", @{});
    BOOL detached = CJDetachManagedWorker();
    gLog(detached ? @"managed_worker_detached" : @"managed_worker_detach_failed", @{@"managed_thread_cleared": @(detached)});
    return passed && proof && detached && atomic_load(&gUnownedJIT) == 0 && atomic_load(&gFailedJIT) == 0;
}
