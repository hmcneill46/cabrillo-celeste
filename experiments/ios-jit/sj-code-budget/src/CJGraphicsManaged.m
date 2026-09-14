// Embedding initialization/GC transitions follow the physically accepted G2 host.
// This stage adds a retained main-thread attachment and bounded per-frame calls.
#import "CJGraphicsManaged.h"
#import "CJHookNative.h"
#import "CJHookMemory.h"
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

static CJGraphicsLog gLog;
static MonoDomain *gDomain;
static MonoClass *gClass;
static BOOL gPrepared, gMainAttached, gAttempted;
static _Atomic(unsigned) gJIT, gUnowned, gFailed, gManagedErrors;
static const char *gNames[] = {"Start", "Frame", "Suspend", "Resume", "Stop"};
static MonoMethod *gMethods[5];
static NSString *S(const char *v) { return v ? ([NSString stringWithUTF8String:v] ?: @"invalid UTF8") : @"null"; }
static NSString *MethodName(MonoMethod *method) { char *n=mono_method_full_name(method,1); NSString *s=S(n); mono_free(n); return s; }
NSDictionary *CJGraphicsRuntimeStats(void) {
    return @{@"jit_done_count": @(atomic_load(&gJIT)), @"jit_unowned": @(atomic_load(&gUnowned)),
             @"jit_failed": @(atomic_load(&gFailed)), @"managed_errors": @(atomic_load(&gManagedErrors)),
             @"code_reserved_bytes": @(cj_code_arena_used()), @"code_budget_bytes": @(CJ_HOOK_CODE_BUDGET),
             @"code_allocations": @(cj_code_arena_allocations()), @"patches": @(CJHookPatchCount()),
             @"patch_rejections": @(CJHookRejectedCount())};
}
static void HookEvent(const char *event, uintptr_t rx, uintptr_t rw, size_t bytes, const char *stage, int actual, int expected) {
    gLog(S(event), @{@"stage": S(stage), @"rx": [NSString stringWithFormat:@"0x%llx", (unsigned long long)rx],
        @"rw": [NSString stringWithFormat:@"0x%llx", (unsigned long long)rw], @"bytes": @(bytes),
        @"actual": @(actual), @"expected": @(expected), @"runtime": CJGraphicsRuntimeStats()});
}
const void *GlobalizationResolveDllImport(const char *entry) {
    if (gLog) gLog(@"invariant_globalization_entry_unavailable", @{@"entry": S(entry)});
    return NULL;
}
static void Trace(const char *domain, const char *level, const char *message, mono_bool fatal, void *user) {
    (void)user; gLog(@"mono_log", @{@"domain":S(domain),@"level":S(level),@"message":S(message),@"fatal":@(fatal)});
    if (fatal) abort();
}
static void Print(const char *message, mono_bool newline) { (void)newline; gLog(@"mono_output", @{@"message":S(message)}); }
static void Chunk(MonoProfiler *p, const mono_byte *chunk, uintptr_t bytes) {
    (void)p; gLog(@"mono_code_chunk_created",@{@"address":[NSString stringWithFormat:@"%p",chunk],@"bytes":@(bytes)});
}
static void Begin(MonoProfiler *p, MonoMethod *m) { (void)p; gLog(@"mono_jit_begin", @{@"method":MethodName(m)}); }
static void Failed(MonoProfiler *p, MonoMethod *m) { (void)p; atomic_fetch_add(&gFailed,1); gLog(@"mono_jit_failed", @{@"method":MethodName(m)}); }
static void Done(MonoProfiler *p, MonoMethod *m, MonoJitInfo *info) {
    (void)p; void *code=mono_jit_info_get_code_start(info); int bytes=mono_jit_info_get_code_size(info);
    #if defined(CJ_GRAPHICS_HOST_TEST)
    // Host Mono owns ordinary executable pages; never report device alias proof.
    BOOL owned=bytes>0;
#else
    BOOL owned=bytes>0 && cj_code_arena_contains_allocation(code,(size_t)bytes);
#endif
    atomic_fetch_add(&gJIT,1); if (!owned) atomic_fetch_add(&gUnowned,1);
    gLog(@"mono_jit_done", @{@"method":MethodName(m),@"code_bytes":@(bytes),
        @"rx":[NSString stringWithFormat:@"%p",code],@"in_prepared_allocation":@(owned)});
}
static void *Import(const char *library, const char *entry) {
    void *v=CJResolveGraphicsNative(library,entry);
    if (!v) v=CJResolveHookNative(library,entry);
    if (!v) v=CJResolveNativeLibrary(library,entry);
    gLog(@"pinvoke_resolution", @{@"library":S(library),@"entry":S(entry),@"resolved_in_static_table":@(v!=NULL)});
    return v;
}
static void Exception(MonoObject *exception, const char *stage) {
    atomic_fetch_add(&gManagedErrors,1);
    gLog(@"managed_exception", @{@"stage":S(stage),@"type":S(mono_class_get_name(mono_object_get_class(exception)))});
    uint32_t pin=mono_gchandle_new(exception,0); MonoObject *error=NULL;
    MonoString *message=mono_object_to_string(mono_gchandle_get_target(pin),&error);
    if (message && !error) { char *text=mono_string_to_utf8(message); gLog(@"managed_exception_detail",@{@"message":S(text)}); mono_free(text); }
    mono_gchandle_free(pin);
}

BOOL CJGraphicsPrepare(NSURL *dll, NSURL *frameworks, CJGraphicsLog log) {
    if (gAttempted || NSThread.isMainThread) return NO;
    gAttempted=YES; gLog=[log copy]; CJHookSetLog(HookEvent);
    gLog(@"mono_configuration_start",@{@"runtime":@"8.0.28",@"aot_disabled":@YES,@"interpreter_disabled":@YES,@"code_budget_bytes":@(CJ_HOOK_CODE_BUDGET)});
    setenv("DOTNET_SYSTEM_GLOBALIZATION_INVARIANT","1",1);
    unsetenv("MONO_ENV_OPTIONS"); unsetenv("MONO_AOT_MODE");
    mono_trace_set_log_handler(Trace,NULL); mono_trace_set_print_handler(Print); mono_trace_set_printerr_handler(Print);
    mono_trace_set_level_string("info"); mono_set_signal_chaining(1); mono_set_crash_chaining(1);
    mono_set_assemblies_path(frameworks.fileSystemRepresentation); mono_jit_set_aot_mode(MONO_AOT_MODE_NONE);
    NSMutableArray<NSString *> *assemblies=[NSMutableArray array];
    for (NSURL *file in [NSFileManager.defaultManager contentsOfDirectoryAtURL:frameworks includingPropertiesForKeys:nil options:0 error:NULL])
        if ([file.pathExtension isEqualToString:@"dll"]) [assemblies addObject:file.path];
    [assemblies sortUsingSelector:@selector(compare:)];
    NSString *tpa=[assemblies componentsJoinedByString:@":"];
    char override[64]; snprintf(override,sizeof(override),"%p",(void *)&Import);
    const char *keys[]={"RUNTIME_IDENTIFIER","APP_CONTEXT_BASE_DIRECTORY","APP_PATHS","TRUSTED_PLATFORM_ASSEMBLIES","PINVOKE_OVERRIDE","System.Globalization.Invariant","System.Diagnostics.Tracing.EventSource.IsSupported"};
#if defined(CJ_GRAPHICS_HOST_TEST)
    const char *rid="osx-x64";
#else
    const char *rid="ios-arm64";
#endif
    const char *values[]={rid,frameworks.fileSystemRepresentation,frameworks.fileSystemRepresentation,tpa.UTF8String,override,"true","false"};
    int init=monovm_initialize(7,keys,values);
    gLog(@"monovm_properties_ready",@{@"result":@(init),@"assemblies":@(assemblies.count)});
    if (init || assemblies.count<100) return NO;
    MonoProfilerHandle profiler=mono_profiler_create(NULL);
    mono_profiler_set_jit_chunk_created_callback(profiler,Chunk); mono_profiler_set_jit_begin_callback(profiler,Begin); mono_profiler_set_jit_done_callback(profiler,Done); mono_profiler_set_jit_failed_callback(profiler,Failed);
    gLog(@"mono_runtime_init_start",@{});
    gDomain=mono_jit_init_version("celeste-jit-graphics","mobile");
    if (!gDomain) return NO;
    mono_gc_init_finalizer_thread();
    gLog(@"mono_runtime_init_pass",@{@"runtime_build":S(mono_get_runtime_build_info())});
    void *anchor=NULL; void *cookie=mono_threads_enter_gc_unsafe_region(&anchor);
    MonoAssembly *assembly=mono_domain_assembly_open(gDomain,dll.fileSystemRepresentation);
    MonoImage *image=assembly ? mono_assembly_get_image(assembly) : NULL;
    gClass=image ? mono_class_from_name(image,"CelesteJIT.Game","Entry") : NULL;
    BOOL found=gClass!=NULL;
    for (unsigned i=0;i<5 && found;i++) {
        gMethods[i]=mono_class_get_method_from_name(gClass,gNames[i],1);
        found=gMethods[i]!=NULL;
    }
    gLog(@"graphics_assembly_loaded",@{@"entry_and_methods_found":@(found),@"image":image?S(mono_image_get_name(image)):@"missing"});
    mono_threads_exit_gc_unsafe_region(cookie,&anchor);
    BOOL detached=CJDetachManagedWorker();
    gLog(detached?@"graphics_prepare_worker_detached":@"graphics_prepare_worker_detach_failed",@{@"managed_thread_cleared":@(detached)});
    gPrepared=found && detached && !atomic_load(&gUnowned) && !atomic_load(&gFailed);
    return gPrepared;
}

BOOL CJGraphicsPrepareContent(int *result) {
    if (!gPrepared || gMainAttached || NSThread.isMainThread || !result) return NO;
    if (!mono_thread_attach(gDomain)) return NO;
    void *anchor=NULL; void *cookie=mono_threads_enter_gc_unsafe_region(&anchor);
    MonoClass *content=mono_class_from_name(mono_class_get_image(gClass),"CelesteJIT.Game","ContentLibrary");
    MonoMethod *method=content ? mono_class_get_method_from_name(content,"Prepare",1) : NULL;
    int unused=0; void *args[]={&unused}; MonoObject *exception=NULL;
    MonoObject *boxed=method ? mono_runtime_invoke(method,NULL,args,&exception) : NULL;
    BOOL ok=NO;
    if(exception)Exception(exception,"ContentLibrary.Prepare");
    else if(boxed && mono_object_get_class(boxed)==mono_get_int32_class()){*result=*(int *)mono_object_unbox(boxed);ok=YES;}
    mono_threads_exit_gc_unsafe_region(cookie,&anchor);
    BOOL detached=CJDetachManagedWorker();
    gLog(@"content_worker_detached",@{@"managed_thread_cleared":@(detached),@"result":@(*result)});
    return ok && detached && !atomic_load(&gUnowned) && !atomic_load(&gFailed) && !atomic_load(&gManagedErrors);
}

BOOL CJGraphicsCall(const char *name, int *result) {
    if (!gPrepared || !NSThread.isMainThread || !result) return NO;
    MonoMethod *method=NULL;
    for (unsigned i=0;i<5;i++) if (!strcmp(name,gNames[i])) method=gMethods[i];
    if (!method) return NO;
    if (!gMainAttached) {
        gMainAttached=mono_thread_attach(gDomain)!=NULL;
        gLog(@"graphics_main_thread_attached",@{@"success":@(gMainAttached)});
        if (!gMainAttached) return NO;
    }
    void *anchor=NULL; void *cookie=mono_threads_enter_gc_unsafe_region(&anchor);
    int unused=0; void *args[]={&unused}; MonoObject *exception=NULL;
    MonoObject *boxed=mono_runtime_invoke(method,NULL,args,&exception);
    BOOL ok=NO;
    if (exception) Exception(exception,name);
    else if (boxed && mono_object_get_class(boxed)==mono_get_int32_class()) { *result=*(int *)mono_object_unbox(boxed); ok=YES; }
    mono_threads_exit_gc_unsafe_region(cookie,&anchor);
    return ok && !atomic_load(&gUnowned) && !atomic_load(&gFailed) && CJHookRejectedCount()==0;
}
BOOL CJGraphicsDetachMain(void) {
    if (!gMainAttached || !NSThread.isMainThread) return NO;
    BOOL ok=CJDetachManagedWorker();
    gMainAttached=NO; gPrepared=NO;
    gLog(ok?@"graphics_main_thread_detached":@"graphics_main_thread_detach_failed",@{@"managed_thread_cleared":@(ok)});
    return ok;
}
