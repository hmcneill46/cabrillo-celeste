#define main unused_full_game_main
#include "host_graphics.m"
#undef main
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
        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{ @autoreleasepool {
            prepared=CJGraphicsPrepare(fixture,frameworks,^(NSString *n,NSDictionary *f){Log(n,f);});
            dispatch_semaphore_signal(done);
        }});
        assert(dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,60*NSEC_PER_SEC))==0 && prepared);
        int result=0;assert(Callback("Start",&result) && result==1);
        for(int i=0;i<30;i++){assert(Callback("Frame",&result));if(result==2)break;assert(result==1);}
        assert(result==2);assert(Callback("Stop",&result)&&result==1);assert(CJGraphicsDetachMain());
        NSDictionary *stats=CJGraphicsRuntimeStats();assert([stats[@"managed_errors"] intValue]==0 && [stats[@"jit_failed"] intValue]==0 && [stats[@"jit_unowned"] intValue]==0);
        puts("PASS_BACKBUFFER_NATIVE_CALLBACK_AND_MONO_DETACH");
    }
    return 0;
}
