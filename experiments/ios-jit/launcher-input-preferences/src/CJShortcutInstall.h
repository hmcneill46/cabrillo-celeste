#import <Foundation/Foundation.h>

// Pure installation planning. No network/radio changes or shortcut-library writes.
NSDictionary *CJShortcutInstallPlan(NSDictionary *host, NSString *bundleFolder, NSString *dataFolder);
NSDictionary *CJShortcutHelperFromLaunchLink(NSString *link, NSString **failure);
NSDictionary *CJShortcutConfiguredHelper(BOOL container, NSUserDefaults *defaults, NSString **failure);
NSData *CJShortcutImportData(NSURL *resources, NSString *variant, NSString **failure);
