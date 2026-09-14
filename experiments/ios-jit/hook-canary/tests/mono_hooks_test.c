#include "CJMonoThread.h"
#include "CJNativeResolver.h"
#include "CJHookNative.h"
#include <mono/jit/jit.h>
#include <mono/jit/mono-private-unstable.h>
#include <mono/metadata/assembly.h>
#include <mono/metadata/appdomain.h>
#include <mono/metadata/class.h>
#include <mono/metadata/object.h>
#include <mono/metadata/threads.h>
#include <mono/metadata/mono-gc.h>
#include <mono/metadata/profiler.h>
#include <mono/utils/mono-publib.h>
#include <assert.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>

static void *system_native;
static MonoDomain *domain;
static MonoClass *baseline, *hooks;
static _Atomic int stages, stage_failures, jit_count, jit_failed;
static _Atomic size_t jit_bytes;
void *CJResolveSystemNative(const char *entry) { return dlsym(system_native, entry); }
const void *GlobalizationResolveDllImport(const char *entry) { (void)entry; return NULL; }
static void *resolve(const char *library, const char *entry) {
    void *result=CJResolveHookNative(library,entry);
    if (!result) result=CJResolveNativeLibrary(library,entry);
    fprintf(stderr,"PINVOKE %s %s %s\n",library,entry,result?"RESOLVED":"UNRESOLVED");
    return result;
}
static void hook_log(const char *event, uintptr_t rx, uintptr_t rw, size_t bytes, const char *detail, int actual, int expected) {
    fprintf(stdout,"HOOK_EVENT %s %s actual=%d expected=%d bytes=%zu rx=0x%lx rw=0x%lx\n",event,detail,actual,expected,bytes,(unsigned long)rx,(unsigned long)rw);
    if (!strcmp(event,"hook_stage_pass")) atomic_fetch_add(&stages,1);
    if (!strcmp(event,"hook_stage_fail")) atomic_fetch_add(&stage_failures,1);
}
static void done(MonoProfiler *p,MonoMethod *method,MonoJitInfo *info) {
    (void)p;
    atomic_fetch_add(&jit_count,1);atomic_fetch_add(&jit_bytes,(size_t)mono_jit_info_get_code_size(info));
    if (strstr(mono_method_get_name(method),"CJIT_Hook")) fprintf(stdout,"DYNAMIC_JIT %s\n",mono_method_get_name(method));
}
static void failed(MonoProfiler *p,MonoMethod *method) {(void)p;fprintf(stderr,"JIT_FAILED %s\n",mono_method_get_name(method));atomic_fetch_add(&jit_failed,1);}
static void chunk_created(MonoProfiler *p, const mono_byte *chunk, uintptr_t size) {
    (void)p; (void)chunk;
    // Record actual full-fixture host code-manager demand for capacity planning.
    // Host chunk sizes do not substitute for the device's 16 KiB page policy.
    fprintf(stdout, "HOST_CODE_CHUNK bytes=%lu\n", (unsigned long)size);
}
static void invoke(MonoClass *klass,const char *name,int x,int expected) {
    fprintf(stdout,"INVOKE_START %s\n",name);
    void *anchor=NULL,*cookie=mono_threads_enter_gc_unsafe_region(&anchor);
    MonoMethod *method=mono_class_get_method_from_name(klass,name,1);assert(method);
    MonoObject *exception=NULL;void *args[]={&x};MonoObject *boxed=mono_runtime_invoke(method,NULL,args,&exception);
    if(exception) {
        fprintf(stderr,"MANAGED_EXCEPTION %s %s\n",name,mono_class_get_name(mono_object_get_class(exception)));
        uint32_t pin=mono_gchandle_new(exception,0);MonoObject *format_error=NULL;
        MonoString *message=mono_object_to_string(mono_gchandle_get_target(pin),&format_error);
        if(message&&!format_error){char *utf8=mono_string_to_utf8(message);fprintf(stderr,"%s\n",utf8);mono_free(utf8);}
        mono_gchandle_free(pin);exit(2);
    }
    assert(boxed&&mono_object_get_class(boxed)==mono_get_int32_class());
    int actual=*(int*)mono_object_unbox(boxed);assert(actual==expected);
    mono_threads_exit_gc_unsafe_region(cookie,&anchor);
    fprintf(stdout,"INVOKE_PASS %s\n",name);
}
static void *resume_worker(void *argument) {
    (void)argument;assert(mono_thread_attach(domain));
    invoke(hooks,"HookResume",348,550);
    assert(CJDetachManagedWorker());puts("HOST_RESUME_WORKER_DETACHED");return NULL;
}
int main(int argc,char **argv) {
    assert(argc==4);struct rlimit limit={0,0};setrlimit(RLIMIT_CORE,&limit);
    setvbuf(stdout,NULL,_IONBF,0);setvbuf(stderr,NULL,_IONBF,0);
    system_native=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);assert(system_native);
    CJHookSetLog(hook_log);
    setenv("DOTNET_SYSTEM_GLOBALIZATION_INVARIANT","1",1);
    setenv("CELESTE_JIT_CANARY_NATIVE_CHECK","build-5-native-imports",1);
    char resolver[64];snprintf(resolver,sizeof(resolver),"%p",(void*)&resolve);
    const char *keys[]={"RUNTIME_IDENTIFIER","APP_CONTEXT_BASE_DIRECTORY","APP_PATHS","TRUSTED_PLATFORM_ASSEMBLIES","PINVOKE_OVERRIDE","System.Globalization.Invariant","System.Diagnostics.Tracing.EventSource.IsSupported"};
    const char *values[]={"osx-x64",argv[2],argv[2],getenv("CJIT_TEST_TPA"),resolver,"true","false"};assert(values[3]);
    mono_set_assemblies_path(argv[2]);mono_jit_set_aot_mode(MONO_AOT_MODE_NONE);assert(monovm_initialize(7,keys,values)==0);
    MonoProfilerHandle profiler=mono_profiler_create(NULL);mono_profiler_set_jit_done_callback(profiler,done);mono_profiler_set_jit_failed_callback(profiler,failed);
    mono_profiler_set_jit_chunk_created_callback(profiler, chunk_created);
    domain=mono_jit_init_version("cjit-real-hooks-regression","mobile");assert(domain);mono_gc_init_finalizer_thread();
    MonoAssembly *assembly=mono_domain_assembly_open(domain,argv[3]);assert(assembly);
    MonoImage *image=mono_assembly_get_image(assembly);
    baseline=mono_class_from_name(image,"CelesteJIT.Canary","Entry");hooks=mono_class_from_name(image,"CelesteJIT.Hooks","Entry");assert(baseline&&hooks);
    int x=348;
    const char *names[]={"NativeImports","Arithmetic","SwitchTable","Dynamic","DynamicSwitch","GenericAbi","ExceptionsAndGC","ThreadAndCallback"};
    int expected[]={x+5,(x*31)^0x13579bdf,x+761,x*3+37,x+168,x*14+13,x+19,x+24};
    for(int i=0;i<8;i++)invoke(baseline,names[i],x,expected[i]);
    invoke(hooks,"HookSetup",x,x+101);assert(CJDetachManagedWorker());puts("HOST_INITIAL_WORKER_DETACHED");
    pthread_t worker;assert(!pthread_create(&worker,NULL,resume_worker,NULL));assert(!pthread_join(worker,NULL));
    assert(CJHookPatchCount()>0&&CJHookRejectedCount()==0&&atomic_load(&stage_failures)==0&&atomic_load(&jit_failed)==0);
    printf("PASS_REAL_MONOMOD_HOOKS checks=%d patches=%zu jit_events=%d jit_bytes=%zu\n",atomic_load(&stages),CJHookPatchCount(),atomic_load(&jit_count),atomic_load(&jit_bytes));
    return 0;
}
