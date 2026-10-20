#import "CJPlatformOptions.h"
#include <math.h>

BOOL CJIntegratedJITShouldRefresh(NSDictionary *platform, BOOL foreground, BOOL active,
                                 BOOL requestConsumed, BOOL hasRefreshed, NSTimeInterval elapsed) {
    if (![platform[@"provider"] isEqual:@"integrated"] || ![platform[@"providerAvailable"] boolValue] ||
        !foreground || active || requestConsumed) return NO;
    return !hasRefreshed || (isfinite(elapsed) && elapsed >= 5);
}

NSDictionary *CJPlatformOptions(NSUserDefaults *defaults, NSOperatingSystemVersion os, BOOL container, NSInteger screenFPS) {
    BOOL stik = os.majorVersion > 17 || (os.majorVersion == 17 && os.minorVersion >= 4);
    NSString *provider = [defaults stringForKey:@"platform.jitProvider"];
    NSArray *providers = stik ? @[@"livecontainer2", @"stikdebug", @"manual"] : @[@"manual"];
    if (!container && os.majorVersion < 17) providers = [providers arrayByAddingObject:@"trollstore"];
    if (stik && !container) providers = [@[@"integrated"] arrayByAddingObjectsFromArray:providers];
    // Only an unset preference adopts the new standalone default. A saved method
    // remains visible when this environment cannot use it; never select a
    // different acquisition method on the owner's behalf.
    if ([defaults objectForKey:@"platform.jitProvider"] == nil)
        provider = container && stik ? @"livecontainer2" : stik ? @"integrated" : @"manual";
    if (!provider) provider = @"invalid";
    BOOL available = [providers containsObject:provider];
    NSString *problem = nil;
    if (!available) {
        if ([provider isEqual:@"integrated"])
            problem = container ? @"Built-in StikJIT cannot run inside LiveContainer. Choose another JIT method in Settings."
                                : @"Built-in StikJIT requires iOS 17.4 or later. Choose another JIT method in Settings.";
        else problem = @"The saved JIT method is unavailable in this installation. Choose another method in Settings.";
        providers = [providers arrayByAddingObject:provider];
    }
    // The accepted iOS26 phone needs debugger-prepared executable pages. Older
    // systems can allocate locally after enabling JIT.
    BOOL script = os.majorVersion >= 26;
    NSDictionary *labels = @{@"integrated":@"Built-in StikJIT", @"livecontainer2":@"StikDebug in LiveContainer 2", @"stikdebug":@"Standalone StikDebug",
                              @"trollstore":@"TrollStore", @"manual":@"Already enabled / another tool"};
    NSDictionary *buttons = @{@"integrated":@"Enable with Built-in StikJIT", @"livecontainer2":@"Enable via LiveContainer 2", @"stikdebug":@"Enable via StikDebug",
                               @"trollstore":@"Enable via TrollStore", @"manual":@"Check JIT for this launch"};
    NSInteger fps = [defaults boolForKey:@"platform.highRefresh"] ? MIN(120, MAX(60, screenFPS)) : 60;
    return @{@"provider":provider, @"providers":providers, @"labels":labels, @"button":buttons[provider]?:@"Choose a JIT method",
             @"providerAvailable":@(available), @"providerError":problem?:@"",
             @"scriptRequired":@(script), @"screenFPS":@(screenFPS), @"targetFPS":@(fps), @"container":@(container),
             @"help":problem ?: [provider isEqual:@"integrated"] ? @"Import your pairing file in Settings, connect LocalDevVPN, then use Run. Cabrillo enables JIT and verifies this process before starting the game."
                            : script ? @"Enable JIT for this process and prepare its memory with the fresh session script. Return here after the debugger detaches."
                              : @"Enable JIT for this running app, then return here. This iOS version can prepare its JIT memory without a debugger script."};
}

NSURL *CJPlatformJITURL(NSString *provider, int pid, NSString *bundleID, NSString *scriptName, NSString *script) {
    if (pid <= 0) return nil;
    NSURLComponents *url = [NSURLComponents new];
    if ([provider isEqualToString:@"trollstore"]) {
        if (!bundleID.length) return nil;
        url.scheme=@"apple-magnifier";url.host=@"enable-jit";
        url.queryItems=@[[NSURLQueryItem queryItemWithName:@"bundle-id" value:bundleID]];
        return url.URL;
    }
    // LiveContainer requires a discovered guest and CJShortcutStikGuestURL;
    // its generic open-url route cannot select a helper on a cold launch.
    if (![provider isEqual:@"stikdebug"]) return nil;
    url.scheme=@"stikdebug";url.host=@"enable-jit";
    NSMutableArray *items=[NSMutableArray arrayWithObject:[NSURLQueryItem queryItemWithName:@"pid" value:[NSString stringWithFormat:@"%d",pid]]];
    // PID always selects the existing process. The actual host bundle ID lets
    // StikDebug foreground it with kill_existing=false before running the script.
    if (bundleID.length) [items addObject:[NSURLQueryItem queryItemWithName:@"bundle-id" value:bundleID]];
    if (scriptName.length) [items addObject:[NSURLQueryItem queryItemWithName:@"script-name" value:scriptName]];
    if (script.length) {
        NSString *encoded=[[script dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0];
        encoded=[[[encoded stringByReplacingOccurrencesOfString:@"+" withString:@"-"] stringByReplacingOccurrencesOfString:@"/" withString:@"_"] stringByReplacingOccurrencesOfString:@"=" withString:@""];
        [items addObject:[NSURLQueryItem queryItemWithName:@"script-data" value:encoded]];
    }
    url.queryItems=items;
    return url.URL;
}
