#import "CJContentImport.h"
#import "CJGraphicsPlatform.h"
#import <QuartzCore/CAMetalLayer.h>
#import <mach/mach.h>
#import <AVFoundation/AVFoundation.h>
#include <stdatomic.h>
#include "SDL.h"
#include "SDL_syswm.h"

// SDL's UIKit entrypoint would start a second UIApplicationMain. The native
// launcher owns the application; SDL only supplies its window and event queue.
extern void SDL_iPhoneSetEventPump(SDL_bool enabled);
extern void SDL_OnApplicationWillResignActive(void);
extern void SDL_OnApplicationDidEnterBackground(void);
extern void SDL_OnApplicationWillEnterForeground(void);
extern void SDL_OnApplicationDidBecomeActive(void);
extern void *CJResolveFNAStatic(const char *entry);
extern void *CJResolveSystemNative(const char *entry);
static CJGraphicsLog gLog;
static UIWindow *gWindow;
static SDL_Window *gSDLWindow;
static NSDictionary *gSample;
static BOOL gReadback;
static _Atomic(unsigned) gChecksFailed;
static NSString *gGameScene;
static BOOL gAudioActive;
static int gCommand;
static UIImpactFeedbackGenerator *gHaptic;
extern void *objc_autoreleasePoolPush(void);
extern void objc_autoreleasePoolPop(void *pool);
static BOOL ActivateAudio(void) {
    NSError *error=nil;AVAudioSession *session=AVAudioSession.sharedInstance;
    BOOL ok=[session setCategory:AVAudioSessionCategoryPlayback withOptions:AVAudioSessionCategoryOptionDuckOthers error:&error];
    if(ok)ok=[session setActive:YES error:&error];gAudioActive=ok;
    gLog(@"game_audio_session",@{@"active":@(ok),@"error":error.localizedDescription?:@"",@"outputs":[session.currentRoute.outputs valueForKey:@"portType"]?:@[]});
    return ok;
}
void CJGameQueueTestMap(void) { gCommand=1; }
static int CJGameTakeCommand(void) { int value=gCommand;gCommand=0;return value; }
static int CJGamePresentation(double *values) {
    if(!gWindow || !NSThread.isMainThread)return 0;
    CGRect bounds=gWindow.bounds;UIEdgeInsets safe=gWindow.safeAreaInsets;
    values[0]=bounds.size.width;values[1]=bounds.size.height;values[2]=safe.top;values[3]=safe.left;values[4]=safe.bottom;values[5]=safe.right;
    values[6]=UIDevice.currentDevice.userInterfaceIdiom==UIUserInterfaceIdiomPad;
    return 1;
}
static void CJGameHaptic(int action) {
    if(!NSThread.isMainThread || UIApplication.sharedApplication.applicationState!=UIApplicationStateActive)return;
    (void)action;[gHaptic impactOccurred];[gHaptic prepare];
}

static CAMetalLayer *FindMetal(CALayer *layer) {
    if ([layer isKindOfClass:CAMetalLayer.class]) return (CAMetalLayer *)layer;
    for (CALayer *child in layer.sublayers) { CAMetalLayer *found=FindMetal(child); if (found) return found; }
    return nil;
}
void CJGraphicsPlatformPrepare(CJGraphicsLog log) {
    NSCAssert(NSThread.isMainThread,@"SDL configuration belongs on the main thread");
    gLog=[log copy];
    NSURL *documents=[NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
    NSURL *profile=[documents URLByAppendingPathComponent:@"Profiles/everest-jit-canary" isDirectory:YES];
    NSError *error=nil;BOOL made=[NSFileManager.defaultManager createDirectoryAtURL:profile withIntermediateDirectories:YES attributes:@{NSFileProtectionKey:NSFileProtectionCompleteUntilFirstUserAuthentication} error:&error];
    NSURL *library=[documents URLByAppendingPathComponent:@"GameLibrary/v1" isDirectory:YES];
    NSURL *content=[library URLByAppendingPathComponent:@"pending/Content" isDirectory:YES];
    setenv("CJIT_CONTENT_LIBRARY_ROOT",library.fileSystemRepresentation,1);
    setenv("CJIT_CONTENT_MANIFEST",[NSBundle.mainBundle URLForResource:@"GameContentManifest" withExtension:@"json"].fileSystemRepresentation,1);
    setenv("CJIT_CONTENT_ARCHIVE",[documents URLByAppendingPathComponent:@"ContentImport/game-input.zip"].fileSystemRepresentation,1);
    setenv("CJIT_GAME_CONTENT_ROOT",content.fileSystemRepresentation,1);
    setenv("CJIT_GAME_SAVE_ROOT",profile.fileSystemRepresentation,1);
    gLog(@"game_native_paths",@{@"profile_created":@(made),@"error":error.localizedDescription?:@"",@"profile":profile.path,@"content":content.path});
    ActivateAudio();
    gHaptic=[[UIImpactFeedbackGenerator alloc] initWithStyle:UIImpactFeedbackStyleLight];[gHaptic prepare];
    SDL_SetMainReady(); SDL_iPhoneSetEventPump(SDL_FALSE);
    SDL_setenv("FNA3D_FORCE_DRIVER","Metal",1);
    SDL_setenv("FNA_GRAPHICS_ENABLE_HIGHDPI","1",1);
    SDL_setenv("FNA_AUDIO_DISABLE_SOUND","1",1);
    SDL_SetHint(SDL_HINT_ORIENTATIONS,"LandscapeLeft LandscapeRight");
    SDL_SetHint(SDL_HINT_IOS_HIDE_HOME_INDICATOR,"2");
    SDL_SetHint(SDL_HINT_TOUCH_MOUSE_EVENTS,"0");
    SDL_SetHint(SDL_HINT_MOUSE_TOUCH_EVENTS,"0");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,"0");
    gLog(@"graphics_native_configured",@{@"renderer":@"Metal",@"audio":@"FMOD native CoreAudio; FAudio disabled",@"nested_ui_application":@NO,@"sdl_recursive_event_pump":@NO});
}
void CJGraphicsPlatformEvent(int state) {
    if (!SDL_WasInit(SDL_INIT_VIDEO)) return;
    switch (state) {
        case 1: SDL_OnApplicationWillResignActive(); break;
        case 2: SDL_OnApplicationDidEnterBackground(); {
            NSError *error=nil;BOOL ok=[AVAudioSession.sharedInstance setActive:NO withOptions:AVAudioSessionSetActiveOptionNotifyOthersOnDeactivation error:&error];gAudioActive=NO;
            gLog(@"game_audio_session_deactivated",@{@"success":@(ok),@"error":error.localizedDescription?:@""});
        } break;
        case 3: SDL_OnApplicationWillEnterForeground(); break;
        case 4: ActivateAudio(); SDL_OnApplicationDidBecomeActive(); break;
        default: return;
    }
    gLog(@"graphics_sdl_lifecycle",@{@"state":@(state)});
}
void CJGraphicsMark(const char *name, const char *message) {
    NSString *event=name?[NSString stringWithUTF8String:name]:nil;
    if ([event isEqualToString:@"graphics_check_fail"]) atomic_fetch_add(&gChecksFailed,1);
    if ([event isEqualToString:@"graphics_check_pass"] && message && !strcmp(message,"metal_render_target_clear_and_gpu_readback")) gReadback=YES;
    if ([event isEqualToString:@"game_scene"] && message) gGameScene=[NSString stringWithUTF8String:message];
    // Diagnostic names carry no native command authority.
    gLog(([event hasPrefix:@"graphics_"] || [event hasPrefix:@"game_"] || [event hasPrefix:@"everest_"] || [event hasPrefix:@"content_"] || [event hasPrefix:@"sj_"] || [event hasPrefix:@"mono_"])?event:@"graphics_fixture_message",
        @{@"message":message?([NSString stringWithUTF8String:message]?:@"invalid UTF8"):@"",@"main_thread":@(NSThread.isMainThread)});
}
void CJGraphicsSetWindow(void *window) {
    NSCAssert(NSThread.isMainThread,@"SDL window must be obtained on the main thread");
    gSDLWindow=(SDL_Window *)window;
    SDL_SysWMinfo info; SDL_zero(info); SDL_VERSION(&info.version);
    BOOL ok=window && SDL_GetWindowWMInfo(gSDLWindow,&info) && info.subsystem==SDL_SYSWM_UIKIT;
    if (ok) gWindow=info.info.uikit.window;
    gLog(@"graphics_native_window",@{@"found":@(gWindow!=nil),@"has_scene":@(gWindow.windowScene!=nil),
        @"connected_scenes":@(UIApplication.sharedApplication.connectedScenes.count),@"metrics":CJGraphicsPlatformSnapshot()});
}
void CJGraphicsSample(int frames, int contacts, int presses, int releases, int controllers, int resumes) {
    gSample=@{@"frames":@(frames),@"contacts":@(contacts),@"touch_presses":@(presses),@"touch_releases":@(releases),@"controllers":@(controllers),@"resumes":@(resumes)};
    gLog(@"graphics_sample",@{@"game":gSample,@"native":CJGraphicsPlatformSnapshot(),@"runtime":CJGraphicsRuntimeStats()});
}
UIWindow *CJGraphicsPlatformWindow(void) { return gWindow; }
void CJGraphicsPlatformForgetWindow(void) { gSDLWindow=NULL; gWindow=nil;gHaptic=nil; }
NSDictionary *CJGraphicsPlatformSnapshot(void) {
    CAMetalLayer *metal=FindMetal(gWindow.layer);
    int w=0,h=0;
    if (gSDLWindow && gWindow) SDL_GetWindowSize(gSDLWindow,&w,&h);
    struct task_vm_info memory={0}; mach_msg_type_number_t count=TASK_VM_INFO_COUNT;
    kern_return_t status=task_info(mach_task_self(),TASK_VM_INFO,(task_info_t)&memory,&count);
    return @{@"metal_layer":@(metal!=nil),@"drawable_width":@(metal.drawableSize.width),@"drawable_height":@(metal.drawableSize.height),
        @"window_width":@(w),@"window_height":@(h),@"screen_scale":@(gWindow.screen.scale),
        @"resident_memory_bytes":@(status==KERN_SUCCESS?memory.resident_size:0),@"physical_footprint_bytes":@(status==KERN_SUCCESS?memory.phys_footprint:0),
        @"memory_query_result":@(status),@"gpu_readback_passed":@(gReadback),@"failed_checks":@(atomic_load(&gChecksFailed)),@"audio_session_active":@(gAudioActive),@"scene":gGameScene?:@"Starting",@"sample":gSample?:@{}};
}
void *CJResolveGraphicsNative(const char *library, const char *entry) {
    if (!library || !entry) return NULL;
    if (!strcmp(library,"lua54")) return CJResolveFNAStatic(entry);
    if (!strcmp(library,"libSystem.IO.Compression.Native") || !strcmp(library,"libSystem.Security.Cryptography.Native.Apple")) return CJResolveSystemNative(entry);
    if (!strcmp(library,"__Internal")) return CJResolveFNAStatic(entry);
    if (strcmp(library,"CJGraphicsNative")) return NULL;
    if (!strcmp(entry,"CJContentShouldCancel")) return (void *)&CJContentShouldCancel;
    if (!strcmp(entry,"CJContentProgress")) return (void *)&CJContentProgress;
    if (!strcmp(entry,"CJContentFreeBytes")) return (void *)&CJContentFreeBytes;
    if (!strcmp(entry,"CJGraphicsMark")) return (void *)&CJGraphicsMark;
    if (!strcmp(entry,"CJGraphicsSetWindow")) return (void *)&CJGraphicsSetWindow;
    if (!strcmp(entry,"CJGraphicsSample")) return (void *)&CJGraphicsSample;
    if (!strcmp(entry,"CJGameWorkerPoolPush")) return (void *)&objc_autoreleasePoolPush;
    if (!strcmp(entry,"CJGameWorkerPoolPop")) return (void *)&objc_autoreleasePoolPop;
    if (!strcmp(entry,"CJGamePresentation")) return (void *)&CJGamePresentation;
    if (!strcmp(entry,"CJGameHaptic")) return (void *)&CJGameHaptic;
    if (!strcmp(entry,"CJGameTakeCommand")) return (void *)&CJGameTakeCommand;
    return NULL;
}
