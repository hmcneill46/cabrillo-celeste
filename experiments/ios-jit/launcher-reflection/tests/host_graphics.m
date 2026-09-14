#import "CJContentImport.h"
// Host-only real Celeste integration; device execution remains a separate gate.
#import <AppKit/AppKit.h>
#import "CJGraphicsManaged.h"
#include "SDL.h"
#include <assert.h>
#include <dlfcn.h>
#include <unistd.h>
#include <stdatomic.h>
#include <sys/resource.h>
extern void *objc_autoreleasePoolPush(void);
extern void objc_autoreleasePoolPop(void *pool);
static void *systemNative, *sdl, *fna, *fmodLibrary, *studio, *lua, *compression, *crypto;
static SDL_Window *gameWindow;
static int touchPresses,touchReleases;
static SDL_Finger testFingers[2];
static BOOL fingerActive[2];
static int TestTouchDeviceCount(void){return 1;}
static SDL_TouchID TestTouchDevice(int index){return index==0?77:0;}
static int TestTouchCount(SDL_TouchID device){(void)device;return fingerActive[0]+fingerActive[1];}
static SDL_Finger *TestTouchFinger(SDL_TouchID device,int index){(void)device;for(int i=0;i<2;i++)if(fingerActive[i] && index--==0)return &testFingers[i];return NULL;}
static BOOL readback, title, level, hookCalled, resumed, saved, complete, everestBoot, luaCallback, modContext, modExecution, modResume, modSave;
static BOOL helperComplete;
static int failures, command, levelSamples, hostJit;
static size_t chunkBytes, chunkCount;
size_t cj_code_arena_used(void) { return 0; }
size_t cj_code_arena_allocations(void) { return 0; }
void *CJResolveSystemNative(const char *entry) { return dlsym(systemNative,entry); }
void CJGraphicsMark(const char *name,const char *message) {
    printf("GAME %s %s\n",name,message);
    if (!strcmp(name,"everest_boot_pass")) everestBoot=YES;
    if (!strcmp(name,"everest_lua_callback_pass")) luaCallback=YES;
    if (!strcmp(name,"everest_mod_context_pass")) modContext=YES;
    if (!strcmp(name,"everest_mod_execution_pass")) modExecution=YES;
    if (!strcmp(name,"everest_mod_resume_pass")) modResume=YES;
    if (!strcmp(name,"everest_mod_save_pass")) modSave=YES;
    if (!strcmp(name,"sj_play_checks_pass")) helperComplete=YES;
    if (!strcmp(name,"graphics_check_fail") || !strcmp(name,"game_worker_failed")) failures++;
    if (!strcmp(name,"graphics_check_pass") && !strcmp(message,"metal_render_target_clear_and_gpu_readback")) readback=YES;
    if (!strcmp(name,"game_menu") && !strcmp(message,"OuiTitleScreen")) title=YES;
    if (!strcmp(name,"game_scene") && !strcmp(message,"Celeste.Level")) level=YES;
    if (!strcmp(name,"game_jump_hook")) hookCalled=YES;
    if (!strcmp(name,"game_resumed")) resumed=YES;
    if (!strcmp(name,"game_save_pass") && strstr(message,"SaveData")) saved=YES;
    if (!strcmp(name,"game_checks_pass")) complete=YES;
}
void CJGraphicsSetWindow(void *window) { assert(window);gameWindow=window;puts("HOST_SDL_WINDOW_RECEIVED"); }
void CJGraphicsSample(int frames,int contacts,int jumps,int moves,int controllers,int resumes) {
    (void)contacts;(void)controllers;touchPresses=jumps;touchReleases=moves;
    printf("HOST_SAMPLE frames=%d jumps=%d moves=%d resumes=%d\n",frames,jumps,moves,resumes);
}
static int CJGamePresentation(double *values) {
    if(!gameWindow)return 0;int w,h;((void (*)(SDL_Window *,int *,int *))dlsym(sdl,"SDL_GetWindowSize"))(gameWindow,&w,&h);
    values[0]=w;values[1]=h;for(int i=2;i<7;i++)values[i]=0;return 1;
}
static void CJGameHaptic(int action){printf("HOST_HAPTIC action=%d (no hardware claim)\n",action);}
static int CJGameTakeCommand(void) { int result=command;command=0;return result; }
void *CJResolveGraphicsNative(const char *library,const char *entry) {
    if (!strcmp(library,"libSystem.IO.Compression.Native")) return dlsym(compression,entry);
    if (!strcmp(library,"libSystem.Security.Cryptography.Native.Apple")) return dlsym(crypto,entry);
    if (!strcmp(library,"lua54")) return dlsym(lua,entry);
    if (!strcmp(library,"__Internal")) {
        // Deterministic host finger snapshots exercise the exact FNA touch-slot
        // policy and game controls. Physical SDL touch was accepted separately.
        if (!strcmp(entry,"SDL_GetNumTouchDevices")) return (void *)&TestTouchDeviceCount;
        if (!strcmp(entry,"SDL_GetTouchDevice")) return (void *)&TestTouchDevice;
        if (!strcmp(entry,"SDL_GetNumTouchFingers")) return (void *)&TestTouchCount;
        if (!strcmp(entry,"SDL_GetTouchFinger")) return (void *)&TestTouchFinger;
        void *p=dlsym(sdl,entry); if(!p)p=dlsym(fna,entry);if(!p)p=dlsym(fmodLibrary,entry);if(!p)p=dlsym(studio,entry);return p;
    }
    if (strcmp(library,"CJGraphicsNative")) return NULL;
    if (!strcmp(entry,"CJContentShouldCancel")) return (void *)&CJContentShouldCancel;
    if (!strcmp(entry,"CJContentProgress")) return (void *)&CJContentProgress;
    if (!strcmp(entry,"CJContentFreeBytes")) return (void *)&CJContentFreeBytes;
    if (!strcmp(entry,"CJGraphicsMark")) return (void *)&CJGraphicsMark;
    if (!strcmp(entry,"CJGraphicsSetWindow")) return (void *)&CJGraphicsSetWindow;
    if (!strcmp(entry,"CJGraphicsSample")) return (void *)&CJGraphicsSample;
    if (!strcmp(entry,"CJGameWorkerPoolPush")) return (void *)&objc_autoreleasePoolPush;
    if (!strcmp(entry,"CJGameWorkerPoolPop")) return (void *)&objc_autoreleasePoolPop;
    if (!strcmp(entry,"CJGameTakeCommand")) return (void *)&CJGameTakeCommand;
    if (!strcmp(entry,"CJGamePresentation")) return (void *)&CJGamePresentation;
    if (!strcmp(entry,"CJGameHaptic")) return (void *)&CJGameHaptic;
    return NULL;
}
static BOOL Callback(const char *method,int *result) { @autoreleasepool { return CJGraphicsCall(method,result); } }
static void Log(NSString *name,NSDictionary *fields) {
    if ([name isEqualToString:@"mono_jit_begin"]) return;
    if ([name isEqualToString:@"mono_jit_done"]) { hostJit++;return; }
    if ([name isEqualToString:@"mono_code_chunk_created"]) { chunkBytes += [fields[@"bytes"] unsignedLongLongValue];chunkCount++;printf("HOST_CODE_CHUNK_BYTES %llu\n",[fields[@"bytes"] unsignedLongLongValue]); }
    fprintf(stdout,"%s %s\n",name.UTF8String,fields.description.UTF8String);
}
static void __attribute__((unused)) Key(SDL_Keycode key,BOOL down) {
    SDL_Event e={0};e.type=down?SDL_KEYDOWN:SDL_KEYUP;e.key.type=e.type;e.key.state=down?SDL_PRESSED:SDL_RELEASED;
    e.key.keysym.sym=key;
    e.key.keysym.scancode=((SDL_Scancode (*)(SDL_Keycode))dlsym(sdl,"SDL_GetScancodeFromKey"))(key);
    assert(((int (*)(SDL_Event *))dlsym(sdl,"SDL_PushEvent"))(&e)==1);
}
static void Touch(int finger,float x,float y,BOOL down) {
    int slot=finger-101;assert(slot>=0 && slot<2);fingerActive[slot]=down;
    testFingers[slot]=(SDL_Finger){finger,x,y,down?1:0};
    SDL_Event e={0};e.type=down?SDL_FINGERDOWN:SDL_FINGERUP;e.tfinger.type=e.type;
    e.tfinger.touchId=1;e.tfinger.fingerId=finger;e.tfinger.x=x;e.tfinger.y=y;e.tfinger.pressure=down?1:0;
    assert(((int (*)(SDL_Event *))dlsym(sdl,"SDL_PushEvent"))(&e)==1);
}
int main(int argc,char **argv) {
    @autoreleasepool {
        assert(argc==9);struct rlimit limit={0,0};setrlimit(RLIMIT_CORE,&limit);
        setvbuf(stdout,NULL,_IONBF,0);setvbuf(stderr,NULL,_IONBF,0);
        systemNative=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);assert(systemNative);
        NSString *nativePath=[@(argv[1]) stringByDeletingLastPathComponent];
        compression=dlopen([nativePath stringByAppendingPathComponent:@"libSystem.IO.Compression.Native.dylib"].UTF8String,RTLD_NOW|RTLD_LOCAL);assert(compression);
        crypto=dlopen([nativePath stringByAppendingPathComponent:@"libSystem.Security.Cryptography.Native.Apple.dylib"].UTF8String,RTLD_NOW|RTLD_LOCAL);assert(crypto);
        sdl=dlopen(argv[4],RTLD_NOW|RTLD_LOCAL);if(!sdl){puts(dlerror());return 2;}
        fna=dlopen(argv[5],RTLD_NOW|RTLD_LOCAL);if(!fna){puts(dlerror());return 2;}
        fmodLibrary=dlopen(argv[6],RTLD_NOW|RTLD_LOCAL);if(!fmodLibrary){puts(dlerror());return 2;}
        studio=dlopen(argv[7],RTLD_NOW|RTLD_LOCAL);if(!studio){puts(dlerror());return 2;}
        lua=dlopen(argv[8],RTLD_NOW|RTLD_LOCAL);if(!lua){puts(dlerror());return 2;}
        setenv("FNA3D_FORCE_DRIVER","Metal",1);setenv("FNA_GRAPHICS_ENABLE_HIGHDPI","0",1);setenv("FNA_AUDIO_DISABLE_SOUND","1",1);
        [NSApplication sharedApplication];[NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
        ((void (*)(void))dlsym(sdl,"SDL_SetMainReady"))();
        NSURL *fixture=[NSURL fileURLWithPath:@(argv[3])],*frameworks=[NSURL fileURLWithPath:@(argv[2])];
        __block BOOL prepared=NO;dispatch_semaphore_t done=dispatch_semaphore_create(0);
        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
            @autoreleasepool {
                prepared=CJGraphicsPrepare(fixture,frameworks,^(NSString *n,NSDictionary *f){Log(n,f);});
                if (prepared && getenv("CJIT_TEST_CONTENT_RETRY")) {
                    int stopped=0; CJContentSetCancelled(YES);
                    assert(CJGraphicsPrepareContent(&stopped) && stopped==3);
                    CJContentSetCancelled(NO);
                    NSString *original=@(getenv("CJIT_CONTENT_ARCHIVE"));
                    NSString *invalid=[@(getenv("CJIT_CONTENT_LIBRARY_ROOT")) stringByAppendingPathComponent:@"invalid-test.zip"];
                    [[NSData dataWithBytes:"invalid archive" length:15] writeToFile:invalid atomically:YES];
                    setenv("CJIT_CONTENT_ARCHIVE",invalid.fileSystemRepresentation,1);
                    stopped=0; assert(CJGraphicsPrepareContent(&stopped) && stopped==2);
                    setenv("CJIT_CONTENT_ARCHIVE",original.UTF8String,1);
                    [NSFileManager.defaultManager removeItemAtPath:invalid error:NULL];
                    Log(@"content_expected_error_retry_pass",@{@"cancel_result":@3,@"invalid_result":@2});
                }
                int content=0; prepared=prepared && CJGraphicsPrepareContent(&content) && content==1;
            }
            dispatch_semaphore_signal(done);
        });
        assert(dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,120*NSEC_PER_SEC))==0 && prepared);
        int result=0;if(!Callback("Start",&result) || result!=1 || !readback){puts("HOST_START_FAILED");return 3;}
        int paintControlFrame=0;BOOL requested=NO;BOOL paint=getenv("CJIT_HOST_PAINT")!=NULL;BOOL normal=getenv("CJIT_HOST_NORMAL")!=NULL || paint;
        for(int i=0;i<5400;i++) {
            BOOL callback=Callback("Frame",&result);
            if(!callback && getenv("CJIT_EXPECT_LITERAL_FAILURE")) {
                NSDictionary *failure=CJGraphicsLastFailure();
                assert([CJGraphicsRuntimeStats()[@"jit_failed"] unsignedIntValue]>0 && [failure[@"stage"] isEqualToString:@"jit_compile"] && [failure[@"summary"] containsString:@"Celeste.Decal:Root"]);
                printf("NATIVE_CAUGHT_JIT_FAILURE %s\n",failure.description.UTF8String);
                puts("PASS_ORIGINAL_PAINT_LITERAL_FAILURE_AND_NATIVE_SUMMARY");return 0;
            }
            assert(callback && result==1 && !failures);
            if (title && !requested) { command=paint?4:normal?3:1;requested=YES; }
            if (level) {
                levelSamples++;
                if(paint) {
                    // Paint's original Lua intro has several dialogue pages.
                    // Use ordinary jump/confirm touch input until control returns.
                    if(levelSamples%30==10)Touch(102,888.0/960,471.0/540,YES);
                    if(levelSamples%30==22)Touch(102,888.0/960,471.0/540,NO);
                    if(hookCalled && !paintControlFrame)paintControlFrame=levelSamples;
                    if(paintControlFrame) {
                        int elapsed=levelSamples-paintControlFrame;
                        if(elapsed==30)Touch(101,166.0/960,436.0/540,YES);
                        if(elapsed==40)Touch(101,166.0/960,436.0/540,NO);
                        if(elapsed==120){assert(Callback("Suspend",&result) && result==1);assert(Callback("Resume",&result) && result==1);}
                        if(elapsed>=260)break;
                    }
                    continue;
                }
                if (levelSamples==480) Touch(101,166.0/960,436.0/540,YES);
                if (levelSamples==250) Touch(102,888.0/960,471.0/540,YES);
                if (levelSamples==262) Touch(102,888.0/960,471.0/540,NO);
                if (levelSamples==310) Touch(102,888.0/960,471.0/540,YES);
                if (levelSamples==322) Touch(102,888.0/960,471.0/540,NO);
                if (levelSamples==520) Touch(101,166.0/960,436.0/540,NO);
                if (levelSamples==540 && !normal) command=2;
                if (levelSamples==640) { assert(Callback("Suspend",&result) && result==1);assert(Callback("Resume",&result) && result==1); }
                if (levelSamples==750) Touch(102,888.0/960,471.0/540,YES);
                if (levelSamples==762) Touch(102,888.0/960,471.0/540,NO);
                if (levelSamples>=950) break;
            }
        }
        assert(everestBoot && luaCallback && title && level && hookCalled && resumed && touchPresses>=3 && touchReleases>=3);
        BOOL stopped=NO;
        for(int i=0;i<600;i++) {
            assert(Callback("Stop",&result));
            if(result!=3){stopped=YES;break;}
            assert(Callback("Frame",&result) && result==1);
        }
        assert(stopped && result==1 && saved && complete && modContext && modExecution && modResume && modSave && (normal || helperComplete));
        assert(CJGraphicsDetachMain());assert([CJGraphicsRuntimeStats()[@"managed_errors"] intValue]==0);
        printf("HOST_CODE_CAPACITY chunks=%zu total_bytes=%zu jit_methods=%d\n",chunkCount,chunkBytes,hostJit);
        puts(paint?"PASS_HOST_PAINT_INTRO_SAVES_AND_RESUME":normal?"PASS_HOST_NORMAL_SELECTION_SAVES_AND_RESUME":"PASS_HOST_REAL_SJ_LOBBY_BING_SAVES_AND_RESUME");
    }
    return 0;
}
