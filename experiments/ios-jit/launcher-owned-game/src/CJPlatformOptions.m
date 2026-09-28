#import "CJPlatformOptions.h"

NSDictionary *CJPlatformOptions(NSUserDefaults *defaults, NSOperatingSystemVersion os, BOOL container, NSInteger screenFPS) {
    BOOL stik = os.majorVersion > 17 || (os.majorVersion == 17 && os.minorVersion >= 4);
    NSString *provider = [defaults stringForKey:@"platform.jitProvider"];
    NSArray *providers = stik ? @[@"livecontainer2", @"stikdebug", @"manual"] : @[@"manual"];
    if (!container && os.majorVersion < 17) providers = [providers arrayByAddingObject:@"trollstore"];
    if (![providers containsObject:provider]) provider = container && stik ? @"livecontainer2" : stik ? @"stikdebug" : @"manual";
    // The accepted iOS26 phone needs debugger-prepared executable pages. Older
    // systems can allocate locally after enabling JIT.
    BOOL script = os.majorVersion >= 26;
    NSDictionary *labels = @{@"livecontainer2":@"StikDebug in LiveContainer 2", @"stikdebug":@"Standalone StikDebug",
                              @"trollstore":@"TrollStore", @"manual":@"Already enabled / another tool"};
    NSDictionary *buttons = @{@"livecontainer2":@"Enable via LiveContainer 2", @"stikdebug":@"Enable via StikDebug",
                               @"trollstore":@"Enable via TrollStore", @"manual":@"Check JIT for this launch"};
    NSInteger fps = [defaults boolForKey:@"platform.highRefresh"] ? MIN(120, MAX(60, screenFPS)) : 60;
    return @{@"provider":provider, @"providers":providers, @"labels":labels, @"button":buttons[provider],
             @"scriptRequired":@(script), @"screenFPS":@(screenFPS), @"targetFPS":@(fps), @"container":@(container),
             @"help":script ? @"Enable JIT for this process and prepare its memory with the fresh session script. Return here after the debugger detaches."
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
    if (![@[@"stikdebug",@"livecontainer2"] containsObject:provider]) return nil;
    url.scheme=@"stikdebug";url.host=@"enable-jit";
    NSMutableArray *items=[NSMutableArray arrayWithObject:[NSURLQueryItem queryItemWithName:@"pid" value:[NSString stringWithFormat:@"%d",pid]]];
    // Only a standalone app supplies its bundle ID. A guest supplies the real
    // process ID, preserving the tested LC route without relaunching its host.
    if (bundleID.length) [items addObject:[NSURLQueryItem queryItemWithName:@"bundle-id" value:bundleID]];
    if (scriptName.length) [items addObject:[NSURLQueryItem queryItemWithName:@"script-name" value:scriptName]];
    if (script.length) {
        NSString *encoded=[[script dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0];
        encoded=[[[encoded stringByReplacingOccurrencesOfString:@"+" withString:@"-"] stringByReplacingOccurrencesOfString:@"/" withString:@"_"] stringByReplacingOccurrencesOfString:@"=" withString:@""];
        [items addObject:[NSURLQueryItem queryItemWithName:@"script-data" value:encoded]];
    }
    url.queryItems=items;
    if ([provider isEqualToString:@"stikdebug"]) return url.URL;
    NSURLComponents *route=[NSURLComponents new];route.scheme=@"livecontainer2";route.host=@"open-url";
    route.queryItems=@[[NSURLQueryItem queryItemWithName:@"url" value:[[url.URL.absoluteString dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0]]];
    return route.URL;
}
