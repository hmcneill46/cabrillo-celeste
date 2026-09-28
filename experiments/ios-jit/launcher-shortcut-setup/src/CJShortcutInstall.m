#import "CJShortcutInstall.h"
#import "CJShortcutPlatform.h"
#import <CommonCrypto/CommonDigest.h>

static BOOL CJInstallComponent(id value) {
    return [value isKindOfClass:NSString.class] && [value length]>0 && [value length]<=255 &&
        ![value isEqual:@"."] && ![value isEqual:@".."] &&
        [value rangeOfCharacterFromSet:[NSCharacterSet characterSetWithCharactersInString:@"/\\"]].location==NSNotFound &&
        [value rangeOfCharacterFromSet:NSCharacterSet.controlCharacterSet].location==NSNotFound;
}
NSDictionary *CJShortcutInstallPlan(NSDictionary *host, NSString *bundleFolder, NSString *dataFolder) {
    if(!host)return @{@"error":@"Reopen Cabrillo from its installed app to identify its launch route."};
    NSString *scheme=host[@"scheme"];
    if([scheme isEqual:@""])return @{@"variant":@"Standalone",@"location":@"Standalone Cabrillo",@"launchURL":@"cabrillo://launch",@"needsLaunchLink":@NO};
    if(![@[@"livecontainer",@"livecontainer2",@"liveprocess"] containsObject:scheme] ||
       !CJInstallComponent(bundleFolder) || ![bundleFolder.pathExtension.lowercaseString isEqual:@"app"] || !CJInstallComponent(dataFolder))
        return @{@"error":@"This LiveContainer installation could not be identified. Open Cabrillo normally and try again."};
    NSURLComponents *url=[NSURLComponents new];url.scheme=scheme;url.host=@"livecontainer-launch";
    url.queryItems=@[[NSURLQueryItem queryItemWithName:@"bundle-name" value:bundleFolder],
        [NSURLQueryItem queryItemWithName:@"container-folder-name" value:dataFolder],
        [NSURLQueryItem queryItemWithName:@"open-url" value:[[@"cabrillo://launch" dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0]]];
    NSString *location=[scheme isEqual:@"livecontainer2"]?@"LiveContainer 2":[scheme isEqual:@"liveprocess"]?@"LiveProcess":@"LiveContainer";
    return @{@"variant":@"LiveContainer",@"location":location,@"launchURL":url.URL.absoluteString,@"needsLaunchLink":@YES};
}
NSDictionary *CJShortcutHelperFromLaunchLink(NSString *link, NSString **failure) {
    if(failure)*failure=@"In LiveContainer, hold StikDebug → Add to Home Screen → Copy Launch URL. Paste that link here.";
    if(![link isKindOfClass:NSString.class] || link.length>4096)return nil;
    NSURLComponents *url=[NSURLComponents componentsWithString:[link stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet]];
    if(![@[@"livecontainer",@"livecontainer2"] containsObject:url.scheme.lowercaseString] ||
       ![url.host isEqual:@"livecontainer-launch"] || url.user || url.password || url.port || url.fragment || url.path.length)return nil;
    NSMutableDictionary *values=[NSMutableDictionary dictionary];
    for(NSURLQueryItem *item in url.queryItems) {
        if(![@[@"bundle-name",@"container-folder-name"] containsObject:item.name] || values[item.name] || !CJInstallComponent(item.value))return nil;
        values[item.name]=item.value;
    }
    NSString *bundle=values[@"bundle-name"];
    if(![bundle.pathExtension.lowercaseString isEqual:@"app"])return nil;
    NSMutableDictionary *guest=[@{@"bundleFolder":bundle} mutableCopy];
    if(values[@"container-folder-name"])guest[@"containerFolder"]=values[@"container-folder-name"];
    if(failure)*failure=nil;
    return guest;
}
NSDictionary *CJShortcutConfiguredHelper(BOOL container, NSUserDefaults *defaults, NSString **failure) {
    // Guests can identify the shared helper. Standalone apps cannot read another
    // app's files; use the owner's explicit LC launch link instead of guessing.
    if(container)return CJShortcutStikGuest(failure);
    return CJShortcutHelperFromLaunchLink([defaults stringForKey:@"shortcut.stikGuestLink"],failure);
}
static NSData *RegularData(NSURL *file, NSUInteger limit) {
    NSDictionary *attributes=[NSFileManager.defaultManager attributesOfItemAtPath:file.path error:NULL];
    if(![attributes[NSFileType] isEqual:NSFileTypeRegular] || [attributes[NSFileSize] unsignedLongLongValue]>limit)return nil;
    return [NSData dataWithContentsOfURL:file options:NSDataReadingUncached error:NULL];
}
NSData *CJShortcutImportData(NSURL *resources, NSString *variant, NSString **failure) {
    if(failure)*failure=@"The bundled shortcut could not be verified. Reinstall this Cabrillo build before creating the shortcut.";
    if(!resources.isFileURL || ![@[@"LiveContainer",@"Standalone"] containsObject:variant])return nil;
    NSData *manifestData=RegularData([resources URLByAppendingPathComponent:@"manifest.json"],65536);
    NSDictionary *manifest=manifestData?[NSJSONSerialization JSONObjectWithData:manifestData options:0 error:NULL]:nil;
    if(![manifest isKindOfClass:NSDictionary.class] || ![manifest[@"build"] isEqual:@48] ||
       ![manifest[@"callback_protocol"] isEqual:@"cabrillo-39"] || ![manifest[@"signed"] isEqual:@YES])return nil;
    id files=manifest[@"files"], variants=[files isKindOfClass:NSDictionary.class]?files[variant]:nil;
    id entry=[variants isKindOfClass:NSDictionary.class]?variants[@"Cabrillo.shortcut"]:nil;
    if(![entry isKindOfClass:NSDictionary.class] || ![entry[@"sha256"] isKindOfClass:NSString.class] || ![entry[@"bytes"] isKindOfClass:NSNumber.class])return nil;
    NSURL *directory=[resources URLByAppendingPathComponent:variant isDirectory:YES];
    if(![[NSFileManager.defaultManager attributesOfItemAtPath:directory.path error:NULL][NSFileType] isEqual:NSFileTypeDirectory])return nil;
    NSData *data=RegularData([directory URLByAppendingPathComponent:@"Cabrillo.shortcut"],2*1024*1024);
    if(!data.length || data.length!=[entry[@"bytes"] unsignedIntegerValue])return nil;
    unsigned char bytes[CC_SHA256_DIGEST_LENGTH];CC_SHA256(data.bytes,(CC_LONG)data.length,bytes);
    NSMutableString *digest=[NSMutableString string];for(NSUInteger i=0;i<sizeof(bytes);i++)[digest appendFormat:@"%02x",bytes[i]];
    if(![digest isEqual:entry[@"sha256"]])return nil;
    if(failure)*failure=nil;
    return data;
}
