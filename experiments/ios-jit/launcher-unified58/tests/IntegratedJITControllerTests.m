#import "CJPlatformOptions.h"
#import "CJIntegratedJITLaunch.h"
#include <math.h>

// Compare real retained routing implementations, including URL escaping, rather
// than reproducing either URL builder in this fixture.
#define CJPlatformOptions CJBuild56PlatformOptions
#define CJPlatformJITURL CJBuild56PlatformJITURL
#include "../../launcher-shortcut-cellular/src/CJPlatformOptions.m"
#undef CJPlatformOptions
#undef CJPlatformJITURL

static NSUInteger checks;
static void Check(BOOL pass, NSString *name) {
    if(!pass){fprintf(stderr,"FAIL %s\n",name.UTF8String);exit(1);} checks++;
}
static NSDictionary *Options(NSUserDefaults *d, NSInteger major, NSInteger minor, BOOL container) {
    return CJPlatformOptions(d,(NSOperatingSystemVersion){major,minor,0},container,120);
}
static CJIntegratedJITReadiness Ready(void) {
    return (CJIntegratedJITReadiness){.nativePassed=YES,.traceKnown=YES,.traced=NO,.debugged=YES,.foreground=YES,
        .profileReady=YES,.profileRestartRequired=NO,.libraryReady=YES,.contentReady=YES,.busy=NO,.used=NO,.selected=YES};
}
static CJIntegratedJITLaunch *Begin(BOOL run) {
    CJIntegratedJITLaunch *s=[CJIntegratedJITLaunch new];
    Check([s beginRequest:@"fresh-process-request" run:run],@"first request accepted");
    return s;
}
int main(int argc, const char *argv[]) { @autoreleasepool {
    NSString *suite=[@"CabrilloIntegratedPolicy-" stringByAppendingString:NSUUID.UUID.UUIDString];
    NSUserDefaults *d=[[NSUserDefaults alloc] initWithSuiteName:suite];
    NSDictionary *fresh=Options(d,17,4,NO);
    Check([fresh[@"provider"] isEqual:@"integrated"] && [fresh[@"providerAvailable"] boolValue],@"eligible fresh standalone defaults internal");
    Check([Options(d,27,0,NO)[@"provider"] isEqual:@"integrated"],@"future standalone default internal");
    Check([Options(d,17,4,YES)[@"provider"] isEqual:@"livecontainer2"],@"fresh container retains external default");
    Check(![Options(d,27,0,YES)[@"providers"] containsObject:@"integrated"],@"unset container never offers helper");
    Check([Options(d,17,3,NO)[@"provider"] isEqual:@"manual"],@"older standalone keeps manual default");
    Check([Options(d,15,8,NO)[@"providers"] containsObject:@"trollstore"],@"iOS15 retains TrollStore");
    Check(![Options(d,15,8,YES)[@"providers"] containsObject:@"trollstore"],@"container never offers TrollStore");
    Check(![Options(d,17,4,NO)[@"scriptRequired"] boolValue] && [Options(d,26,0,NO)[@"scriptRequired"] boolValue],@"memory strategy boundary retained");
    Check([Options(d,27,0,NO)[@"targetFPS"] integerValue]==60,@"default refresh unchanged");
    [d setBool:YES forKey:@"platform.highRefresh"];
    Check([Options(d,27,0,NO)[@"targetFPS"] integerValue]==120,@"explicit high refresh retained");
    for(NSString *provider in @[@"manual",@"stikdebug",@"livecontainer2",@"integrated"]) {
        [d setObject:provider forKey:@"platform.jitProvider"];
        Check([Options(d,27,0,NO)[@"provider"] isEqual:provider],@"existing standalone choice retained");
        if(![provider isEqual:@"integrated"]) {
            NSDictionary *baseline=CJBuild56PlatformOptions(d,(NSOperatingSystemVersion){27,0,0},NO,120);
            NSDictionary *current=Options(d,27,0,NO);
            for(NSString *key in @[@"provider",@"button",@"scriptRequired",@"targetFPS",@"container",@"help"])
                Check([baseline[key] isEqual:current[key]],[@"legacy explicit method retains " stringByAppendingString:key]);
        }
    }
    [d setObject:@"integrated" forKey:@"platform.jitProvider"];
    for(NSDictionary *o in @[Options(d,27,0,YES),Options(d,17,3,NO),Options(d,15,8,NO)]) {
        Check([o[@"provider"] isEqual:@"integrated"],@"unsupported selected internal remains selected");
        Check([o[@"providers"] containsObject:@"integrated"],@"unsupported selected method stays visible");
        Check(![o[@"providerAvailable"] boolValue] && [o[@"providerError"] length]>0,@"unsupported internal exposes actionable failure");
    }
    [d setObject:@"stikdebug" forKey:@"platform.jitProvider"];
    Check([Options(d,17,3,NO)[@"provider"] isEqual:@"stikdebug"] && ![Options(d,17,3,NO)[@"providerAvailable"] boolValue],@"unsupported old external selection never changes silently");
    [d setObject:@"trollstore" forKey:@"platform.jitProvider"];
    Check([Options(d,27,0,NO)[@"provider"] isEqual:@"trollstore"] && ![Options(d,27,0,NO)[@"providerAvailable"] boolValue],@"unsupported TrollStore remains explicit error");
    [d setObject:@"unrecognized-method" forKey:@"platform.jitProvider"];
    Check([Options(d,27,0,NO)[@"provider"] isEqual:@"unrecognized-method"] && ![Options(d,27,0,NO)[@"providerAvailable"] boolValue],@"unknown preference is not a provider fallback");
    [d setObject:@"" forKey:@"platform.jitProvider"];
    Check([Options(d,27,0,NO)[@"provider"] isEqual:@""] && ![Options(d,27,0,NO)[@"providerAvailable"] boolValue],@"only absent preference receives new default");
    for(NSString *provider in @[@"manual",@"stikdebug",@"livecontainer2",@"trollstore",@"integrated"]) {
        for(NSString *bundle in @[@"actual.host.bundle",@""]) {
            for(NSString *script in @[@"const value='new+/=';\n",@""]) {
                NSURL *old=CJBuild56PlatformJITURL(provider,42,bundle,@"fresh-request.js",script);
                NSURL *now=CJPlatformJITURL(provider,42,bundle,@"fresh-request.js",script);
                Check((old==nil && now==nil) || [old.absoluteString isEqual:now.absoluteString],@"legacy URL routing remains byte-identical");
            }
        }
    }
    Check(!CJPlatformJITURL(@"integrated",42,@"actual.host",nil,nil),@"internal method cannot leak into URL routing");
    Check(!CJPlatformJITURL(@"stikdebug",0,@"actual.host",nil,nil),@"invalid PID remains rejected");
    [d removeObjectForKey:@"platform.jitProvider"];
    NSDictionary *refresh=Options(d,27,0,NO);
    Check(CJIntegratedJITShouldRefresh(refresh,YES,NO,NO,NO,0),@"initial foreground refresh allowed");
    Check(!CJIntegratedJITShouldRefresh(refresh,YES,NO,NO,YES,4.999),@"resume refresh debounced for five seconds");
    Check(CJIntegratedJITShouldRefresh(refresh,YES,NO,NO,YES,5),@"resume refresh allowed after debounce boundary");
    Check(!CJIntegratedJITShouldRefresh(refresh,NO,NO,NO,NO,10),@"background cannot start automatic refresh");
    Check(!CJIntegratedJITShouldRefresh(refresh,YES,YES,NO,NO,10),@"active helper cannot overlap automatic refresh");
    Check(!CJIntegratedJITShouldRefresh(refresh,YES,NO,YES,NO,10),@"consumed process request cannot refresh acquisition status");
    Check(!CJIntegratedJITShouldRefresh(refresh,YES,NO,NO,YES,-1),@"invalid elapsed time fails closed");
    Check(!CJIntegratedJITShouldRefresh(refresh,YES,NO,NO,YES,NAN),@"unknown elapsed time fails closed");
    Check(!CJIntegratedJITShouldRefresh(refresh,YES,NO,NO,YES,INFINITY),@"nonfinite elapsed time fails closed");
    Check(!CJIntegratedJITShouldRefresh(Options(d,27,0,YES),YES,NO,NO,NO,10),@"container never starts internal readiness probe");
    [d setObject:@"stikdebug" forKey:@"platform.jitProvider"];
    Check(!CJIntegratedJITShouldRefresh(Options(d,27,0,NO),YES,NO,NO,NO,10),@"explicit external method never starts internal probe");
    [d setObject:@"integrated" forKey:@"platform.jitProvider"];
    Check(!CJIntegratedJITShouldRefresh(Options(d,17,3,NO),YES,NO,NO,NO,10),@"unsupported selected method cannot probe");
    CJIntegratedJITReadiness ready=Ready();
    CJIntegratedJITLaunch *empty=[CJIntegratedJITLaunch new];
    Check(![empty beginRequest:@"" run:YES] && !empty.requestID,@"empty request rejected without consumption");
    Check(![empty requestRun] && ![empty consumeRunWithReadiness:ready],@"Run cannot precede request");
    CJIntegratedJITLaunch *nativeOnly=Begin(YES);
    Check(![nativeOnly consumeRunWithReadiness:ready],@"native success alone cannot launch");
    Check(![nativeOnly beginRequest:@"second" run:YES] && [nativeOnly.requestID isEqual:@"fresh-process-request"],@"in-flight request cannot be replaced");
    Check(![nativeOnly completeRequest:@"stale-process-request" success:YES error:nil] && nativeOnly.active,@"stale helper success cannot finish current request");
    Check(![nativeOnly consumeRunWithReadiness:ready],@"stale success plus native pass still cannot launch");
    Check([nativeOnly completeRequest:@"fresh-process-request" success:YES error:nil],@"matching helper result accepted");
    CJIntegratedJITReadiness noNative=ready;noNative.nativePassed=NO;
    Check(![nativeOnly consumeRunWithReadiness:noNative],@"helper success alone cannot launch");
#define BLOCK(field,value) do { CJIntegratedJITReadiness blocked=ready;blocked.field=value;Check(![nativeOnly consumeRunWithReadiness:blocked],@"blocked " #field);Check(!nativeOnly.launchConsumed && nativeOnly.pendingRun,@"blocked readiness keeps pending Run"); } while(0)
    BLOCK(traceKnown,NO);BLOCK(traced,YES);BLOCK(debugged,NO);BLOCK(foreground,NO);
    BLOCK(profileReady,NO);BLOCK(profileRestartRequired,YES);BLOCK(libraryReady,NO);
    BLOCK(contentReady,NO);BLOCK(busy,YES);BLOCK(used,YES);BLOCK(selected,NO);
#undef BLOCK
    Check([nativeOnly consumeRunWithReadiness:ready],@"both independent passes and all current gates consume Run");
    Check(nativeOnly.launchConsumed && !nativeOnly.pendingRun,@"Run consumed atomically");
    Check(!CJIntegratedJITCanEnterRuntime(NO,YES,NO),@"background drift after consumption blocks runtime entry");
    Check(!CJIntegratedJITCanEnterRuntime(YES,NO,NO),@"profile readiness drift after consumption blocks runtime entry");
    Check(!CJIntegratedJITCanEnterRuntime(YES,YES,YES),@"new profile restart requirement blocks runtime entry");
    Check(CJIntegratedJITCanEnterRuntime(YES,YES,NO),@"foreground valid profile permits later explicit retry");
    Check(![nativeOnly consumeRunWithReadiness:ready] && ![nativeOnly requestRun],@"duplicate polling cannot launch twice");
    Check(![nativeOnly completeRequest:@"fresh-process-request" success:NO error:@"late error"],@"duplicate helper completion cannot change accepted result");
    [nativeOnly fail:@"late unrelated failure"];
    Check(!nativeOnly.failed && nativeOnly.launchConsumed,@"late callback cannot restart consumed launch");
    CJIntegratedJITLaunch *failure=Begin(YES);
    Check([failure completeRequest:@"fresh-process-request" success:NO error:@"mount failed"],@"matching helper failure accepted");
    Check(failure.failed && !failure.active && !failure.pendingRun && [failure.error isEqual:@"mount failed"],@"helper error retained and auto-run cancelled");
    Check(![failure consumeRunWithReadiness:ready],@"native pass cannot override helper failure");
    Check(![failure requestRun] && ![failure beginRequest:@"new" run:YES],@"failed process requires restart");
    Check(![failure completeRequest:@"fresh-process-request" success:YES error:nil],@"late helper success cannot revive failed request");
    CJIntegratedJITLaunch *nativeFailure=Begin(YES);
    [nativeFailure fail:@"native check failed"];
    Check(![nativeFailure completeRequest:@"fresh-process-request" success:YES error:nil] && ![nativeFailure consumeRunWithReadiness:ready],@"native failure remains terminal after helper success");
    CJIntegratedJITLaunch *manualEnable=Begin(NO);
    Check([manualEnable completeRequest:@"fresh-process-request" success:YES error:nil],@"manual enable helper completes");
    Check(![manualEnable consumeRunWithReadiness:ready],@"Enable does not imply Run");
    Check([manualEnable requestRun] && [manualEnable consumeRunWithReadiness:ready],@"later explicit Run reuses verified same-process activation once");
    [d removePersistentDomainForName:suite];
    NSDictionary *report=@{@"status":@"PASS_INTEGRATED_JIT_CONTROLLER_POLICY",@"checks":@(checks),@"game_executed":@NO,@"device_jit_executed":@NO,@"helper_launched":@NO};
    if(argc>1){NSData *data=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted error:NULL];if(![data writeToFile:[NSString stringWithUTF8String:argv[1]] atomically:YES]){fputs("FAIL write control report\n",stderr);return 1;}}
    printf("PASS %lu integrated controller and provider controls\n",(unsigned long)checks);
} return 0; }
