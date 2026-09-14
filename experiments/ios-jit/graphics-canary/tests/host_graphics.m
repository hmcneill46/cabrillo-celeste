// Desktop-only runtime/main-thread/FNA regression. No device alias acceptance.
#import <AppKit/AppKit.h>
#import "CJGraphicsManaged.h"
#include <assert.h>
#include <dlfcn.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>
#include <sys/resource.h>

static void *systemNative, *sdl, *fna;
static BOOL readback, hookInstalled, hookResumed, hookRemoved, startupClosed, resetReadback, skipClosed, skipRecovered;
static int lastFrames, resumed, nativeErrors;
size_t cj_code_arena_used(void) { return 0; }
size_t cj_code_arena_allocations(void) { return 0; }
void *CJResolveSystemNative(const char *entry) { return dlsym(systemNative,entry); }
void CJGraphicsMark(const char *name,const char *message) {
    printf("GRAPHICS %s %s\n",name,message);
    if (!strcmp(name,"graphics_check_fail")) nativeErrors++;
    if (!strcmp(name,"graphics_check_pass")) {
        if (!strcmp(message,"metal_render_target_clear_and_gpu_readback")) readback=YES;
        if (!strcmp(message,"render_hook_installed")) hookInstalled=YES;
        if (!strcmp(message,"render_hook_survives_resume_gc")) hookResumed=YES;
        if (!strcmp(message,"render_hook_removed_on_stop")) hookRemoved=YES;
        if (!strcmp(message,"startup_metal_frame_closed_before_callback_return")) startupClosed=YES;
        if (!strcmp(message,"pending_clear_reset_preserves_render_target")) resetReadback=YES;
        if (!strcmp(message,"skipped_draw_metal_frame_closed_before_callback_return")) skipClosed=YES;
        if (!strcmp(message,"gpu_work_after_suppressed_draw")) skipRecovered=YES;
    }
}
void CJGraphicsSetWindow(void *window) { assert(window); puts("HOST_SDL_WINDOW_RECEIVED"); }
void CJGraphicsSample(int frames,int contacts,int presses,int releases,int controllers,int resumes) {
    (void)contacts;(void)presses;(void)releases;(void)controllers;
    lastFrames=frames; resumed=resumes;
    printf("HOST_SAMPLE frames=%d resumes=%d\n",frames,resumes);
}
void *CJResolveGraphicsNative(const char *library,const char *entry) {
    if (!strcmp(library,"__Internal")) { void *p=dlsym(sdl,entry); return p ? p : dlsym(fna,entry); }
    if (strcmp(library,"CJGraphicsNative")) return NULL;
    if (!strcmp(entry,"CJGraphicsMark")) return (void *)&CJGraphicsMark;
    if (!strcmp(entry,"CJGraphicsSetWindow")) return (void *)&CJGraphicsSetWindow;
    if (!strcmp(entry,"CJGraphicsSample")) return (void *)&CJGraphicsSample;
    return NULL;
}
static BOOL Callback(const char *method, int *result) {
    @autoreleasepool { return CJGraphicsCall(method, result); }
}

static void Log(NSString *name,NSDictionary *fields) {
    if ([name isEqualToString:@"mono_jit_begin"] || [name isEqualToString:@"mono_jit_done"]) return;
    fprintf(stdout,"%s %s\n",name.UTF8String,fields.description.UTF8String);
}
int main(int argc,char **argv) {
    @autoreleasepool {
        assert(argc==6);
        struct rlimit limit={0,0};setrlimit(RLIMIT_CORE,&limit);
        setvbuf(stdout,NULL,_IONBF,0);setvbuf(stderr,NULL,_IONBF,0);
        systemNative=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);assert(systemNative);
        sdl=dlopen(argv[4],RTLD_NOW|RTLD_LOCAL);if(!sdl){puts(dlerror());return 2;}
        fna=dlopen(argv[5],RTLD_NOW|RTLD_LOCAL);if(!fna){puts(dlerror());return 2;}
        setenv("FNA3D_FORCE_DRIVER","Metal",1);setenv("FNA_GRAPHICS_ENABLE_HIGHDPI","0",1);
        [NSApplication sharedApplication];[NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
        ((void (*)(void))dlsym(sdl,"SDL_SetMainReady"))();
        NSURL *fixture=[NSURL fileURLWithPath:@(argv[3])], *frameworks=[NSURL fileURLWithPath:@(argv[2])];
        __block BOOL prepared=NO;
        dispatch_semaphore_t done=dispatch_semaphore_create(0);
        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
            @autoreleasepool { prepared=CJGraphicsPrepare(fixture,frameworks,^(NSString *n,NSDictionary *f){Log(n,f);}); }
            dispatch_semaphore_signal(done);
        });
        assert(dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,30*NSEC_PER_SEC))==0 && prepared);
        int result=0;
        assert(Callback("Start",&result) && result==1 && readback && hookInstalled);
        for (int i=0;i<360;i++) { assert(Callback("Frame",&result) && result==1); }
        assert(Callback("Suspend",&result) && result==1);
        assert(Callback("Resume",&result) && result==1 && hookResumed);
        for (int i=0;i<180;i++) { assert(Callback("Frame",&result) && result==1); }
        // No synthetic physical touch: Stop must report incomplete in this host run.
        assert(Callback("Stop",&result) && result==2 && hookRemoved);
        assert(CJGraphicsDetachMain());
        assert(lastFrames==539 && resumed==1 && nativeErrors==0);
        assert(startupClosed && resetReadback && skipClosed && skipRecovered);
        assert([CJGraphicsRuntimeStats()[@"managed_errors"] intValue]==0);
        puts("PASS_HOST_FNA_METAL_539_FRAMES_CALLBACK_POOLS_RESET_SKIP_RESUME_HOOK_AND_MAIN_THREAD_DETACH");
    }
    return 0;
}
