#import <Foundation/Foundation.h>

NSDictionary *CJPlatformOptions(NSUserDefaults *defaults, NSOperatingSystemVersion os, BOOL container, NSInteger screenFPS);
NSURL *CJPlatformJITURL(NSString *provider, int pid, NSString *bundleID, NSString *scriptName, NSString *script);
BOOL CJIntegratedJITShouldRefresh(NSDictionary *platform, BOOL foreground, BOOL active,
                                 BOOL requestConsumed, BOOL hasRefreshed, NSTimeInterval elapsed);
