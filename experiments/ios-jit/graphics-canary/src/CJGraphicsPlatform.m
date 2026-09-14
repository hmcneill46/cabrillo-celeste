#import "CJGraphicsPlatform.h"
#import <QuartzCore/CAMetalLayer.h>
#import <mach/mach.h>
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
static CJGraphicsLog gLog;
static UIWindow *gWindow;
static SDL_Window *gSDLWindow;
static NSDictionary *gSample;
static BOOL gReadback;
static unsigned gChecksFailed;

static CAMetalLayer *FindMetal(CALayer *layer) {
    if ([layer isKindOfClass:CAMetalLayer.class]) return (CAMetalLayer *)layer;
    for (CALayer *child in layer.sublayers) { CAMetalLayer *found=FindMetal(child); if (found) return found; }
    return nil;
}
void CJGraphicsPlatformPrepare(CJGraphicsLog log) {
    NSCAssert(NSThread.isMainThread,@"SDL configuration belongs on the main thread");
    gLog=[log copy];
    SDL_SetMainReady(); SDL_iPhoneSetEventPump(SDL_FALSE);
    SDL_setenv("FNA3D_FORCE_DRIVER","Metal",1);
    SDL_setenv("FNA_GRAPHICS_ENABLE_HIGHDPI","1",1);
    SDL_setenv("FNA_AUDIO_DISABLE_SOUND","1",1);
    SDL_SetHint(SDL_HINT_ORIENTATIONS,"LandscapeLeft LandscapeRight");
    SDL_SetHint(SDL_HINT_IOS_HIDE_HOME_INDICATOR,"2");
    SDL_SetHint(SDL_HINT_TOUCH_MOUSE_EVENTS,"0");
    SDL_SetHint(SDL_HINT_MOUSE_TOUCH_EVENTS,"0");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,"0");
    gLog(@"graphics_native_configured",@{@"renderer":@"Metal",@"audio":@"disabled_for_graphics_probe",@"nested_ui_application":@NO,@"sdl_recursive_event_pump":@NO});
}
void CJGraphicsPlatformEvent(int state) {
    if (!SDL_WasInit(SDL_INIT_VIDEO)) return;
    switch (state) {
        case 1: SDL_OnApplicationWillResignActive(); break;
        case 2: SDL_OnApplicationDidEnterBackground(); break;
        case 3: SDL_OnApplicationWillEnterForeground(); break;
        case 4: SDL_OnApplicationDidBecomeActive(); break;
        default: return;
    }
    gLog(@"graphics_sdl_lifecycle",@{@"state":@(state)});
}
void CJGraphicsMark(const char *name, const char *message) {
    NSString *event=name?[NSString stringWithUTF8String:name]:nil;
    if ([event isEqualToString:@"graphics_check_fail"]) gChecksFailed++;
    if ([event isEqualToString:@"graphics_check_pass"] && message && !strcmp(message,"metal_render_target_clear_and_gpu_readback")) gReadback=YES;
    // This is a test-fixture event bridge, not a general native command channel.
    gLog([event hasPrefix:@"graphics_"]?event:@"graphics_fixture_message",
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
void CJGraphicsPlatformForgetWindow(void) { gSDLWindow=NULL; gWindow=nil; }
NSDictionary *CJGraphicsPlatformSnapshot(void) {
    CAMetalLayer *metal=FindMetal(gWindow.layer);
    int w=0,h=0;
    if (gSDLWindow && gWindow) SDL_GetWindowSize(gSDLWindow,&w,&h);
    struct task_vm_info memory={0}; mach_msg_type_number_t count=TASK_VM_INFO_COUNT;
    kern_return_t status=task_info(mach_task_self(),TASK_VM_INFO,(task_info_t)&memory,&count);
    return @{@"metal_layer":@(metal!=nil),@"drawable_width":@(metal.drawableSize.width),@"drawable_height":@(metal.drawableSize.height),
        @"window_width":@(w),@"window_height":@(h),@"screen_scale":@(gWindow.screen.scale),
        @"resident_memory_bytes":@(status==KERN_SUCCESS?memory.resident_size:0),@"physical_footprint_bytes":@(status==KERN_SUCCESS?memory.phys_footprint:0),
        @"memory_query_result":@(status),@"gpu_readback_passed":@(gReadback),@"failed_checks":@(gChecksFailed),@"sample":gSample?:@{}};
}
void *CJResolveGraphicsNative(const char *library, const char *entry) {
    if (!library || !entry) return NULL;
    if (!strcmp(library,"__Internal")) return CJResolveFNAStatic(entry);
    if (strcmp(library,"CJGraphicsNative")) return NULL;
    if (!strcmp(entry,"CJGraphicsMark")) return (void *)&CJGraphicsMark;
    if (!strcmp(entry,"CJGraphicsSetWindow")) return (void *)&CJGraphicsSetWindow;
    if (!strcmp(entry,"CJGraphicsSample")) return (void *)&CJGraphicsSample;
    return NULL;
}
