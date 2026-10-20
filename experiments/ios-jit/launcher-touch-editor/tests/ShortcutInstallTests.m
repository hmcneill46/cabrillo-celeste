#import <Foundation/Foundation.h>
#import "CJShortcutInstall.h"
#import "CJShortcutPlatform.h"
static NSUInteger checks;
static void Check(BOOL result,NSString *name){checks++;if(!result){fprintf(stderr,"FAIL %s\n",name.UTF8String);exit(1);}}
static NSDictionary *Query(NSString *text){NSMutableDictionary *result=[NSMutableDictionary dictionary];for(NSURLQueryItem *q in [NSURLComponents componentsWithString:text].queryItems)result[q.name]=q.value;return result;}
int main(int argc,char **argv){@autoreleasepool{
    if(argc!=3)return 2;
    NSDictionary *standalone=CJShortcutInstallPlan(@{@"scheme":@""},nil,nil);
    Check([standalone[@"launchURL"] isEqual:@"cabrillo://launch"] && [standalone[@"variant"] isEqual:@"Standalone"] && ![standalone[@"needsLaunchLink"] boolValue],@"standalone route");
    for(NSString *scheme in @[@"livecontainer",@"livecontainer2",@"liveprocess"]){
        NSDictionary *plan=CJShortcutInstallPlan(@{@"scheme":scheme},@"Cabrillo + 测试.app",@"my data+&=?#");
        NSDictionary *q=Query(plan[@"launchURL"]);
        Check([[NSURL URLWithString:plan[@"launchURL"]] scheme] && [[NSURL URLWithString:plan[@"launchURL"]].scheme isEqual:scheme],@"actual host selected");
        Check([q[@"bundle-name"] isEqual:@"Cabrillo + 测试.app"] && [q[@"container-folder-name"] isEqual:@"my data+&=?#"],@"guest and data roundtrip");
        NSString *inner=[[NSString alloc] initWithData:[[NSData alloc] initWithBase64EncodedString:q[@"open-url"] options:0] encoding:NSUTF8StringEncoding];
        Check([inner isEqual:@"cabrillo://launch"] && [plan[@"needsLaunchLink"] boolValue],@"explicit home launch");
    }
    Check(CJShortcutInstallPlan(nil,@"Cabrillo.app",@"data")[@"error"]!=nil,@"unknown host blocked");
    Check(CJShortcutInstallPlan(@{@"scheme":@"https"},@"Cabrillo.app",@"data")[@"error"]!=nil,@"unsupported host blocked");
    for(NSString *part in @[@"",@"..",@"a/b",@"a\\b",@"a\nb",[@"a" stringByPaddingToLength:256 withString:@"a" startingAtIndex:0]]){
        Check(CJShortcutInstallPlan(@{@"scheme":@"livecontainer"},part,@"data")[@"error"]!=nil,@"bad app folder");
        Check(CJShortcutInstallPlan(@{@"scheme":@"livecontainer"},@"Cabrillo.app",part)[@"error"]!=nil,@"bad data folder");
    }
    NSString *failure=nil;
    for(NSString *link in @[@"livecontainer://livecontainer-launch?bundle-name=Stik.app",@" livecontainer2://livecontainer-launch?bundle-name=Stik%20Debug.app&container-folder-name=helper%2Bdata\n"]){
        NSDictionary *helper=CJShortcutHelperFromLaunchLink(link,&failure);
        Check(helper!=nil && !failure,@"copied helper link accepted");
        NSURL *route=CJShortcutStikGuestURL(helper,[NSURL URLWithString:@"stikdebug://enable-jit?pid=1234&script-data=fresh"]);
        Check([route.scheme isEqual:@"livecontainer2"] && [Query(route.absoluteString)[@"bundle-name"] isEqual:helper[@"bundleFolder"]],@"helper explicitly goes to LC2");
    }
    for(id link in @[@"",NSNull.null,@"https://example.com",@"livecontainer://open-url?url=anything",@"livecontainer://livecontainer-launch?bundle-name=../Stik.app",@"livecontainer://livecontainer-launch?bundle-name=Stik.app&bundle-name=Other.app",@"livecontainer://livecontainer-launch?bundle-name=Stik.app&open-url=ZXZpbA==",@"livecontainer://livecontainer-launch?bundle-name=Stik.app&container-folder-name=",@"livecontainer://livecontainer-launch?bundle-name=Stik.app#fragment",@"livecontainer://user@livecontainer-launch?bundle-name=Stik.app",@"livecontainer://livecontainer-launch/path?bundle-name=Stik.app"])
        Check(CJShortcutHelperFromLaunchLink(link,&failure)==nil && failure.length,@"invalid helper link rejected");
    NSUserDefaults *defaults=[[NSUserDefaults alloc] initWithSuiteName:[@"shortcut49.test." stringByAppendingString:NSUUID.UUID.UUIDString]];
    [defaults setObject:@"livecontainer://livecontainer-launch?bundle-name=UserSelectedStik.app" forKey:@"shortcut.stikGuestLink"];
    Check([CJShortcutConfiguredHelper(NO,defaults,&failure)[@"bundleFolder"] isEqual:@"UserSelectedStik.app"],@"standalone uses explicit saved helper");
    Check(CJShortcutSetupProblem(YES,@"livecontainer2",@{@"scheme":@"livecontainer2"},nil)!=nil,@"same host conflict before any radios");
    Check(CJShortcutSetupProblem(YES,@"stikdebug",@{@"scheme":@"livecontainer2"},nil)==nil,@"LC2 Cabrillo can use standalone helper");
    NSURL *assets=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
    for(NSString *variant in @[@"Standalone",@"LiveContainer"])
        Check(CJShortcutImportData(assets,variant,&failure).length>0 && !failure,@"signed bundled bytes verified");
    Check(!CJShortcutImportData(assets,@"../LiveContainer",&failure),@"variant path rejected");
    NSURL *copy=[NSURL fileURLWithPath:@(argv[2]) isDirectory:YES];
    Check([NSFileManager.defaultManager copyItemAtURL:assets toURL:copy error:NULL],@"isolated export fixture copied");
    NSURL *file=[copy URLByAppendingPathComponent:@"LiveContainer/Cabrillo.shortcut"];
    NSMutableData *data=[[NSData dataWithContentsOfURL:file] mutableCopy];((unsigned char *)data.mutableBytes)[data.length/2]^=1;[data writeToURL:file atomically:YES];
    Check(!CJShortcutImportData(copy,@"LiveContainer",&failure),@"modified shortcut rejected");
    [NSFileManager.defaultManager removeItemAtURL:file error:NULL];
    [NSFileManager.defaultManager createSymbolicLinkAtPath:file.path withDestinationPath:[assets URLByAppendingPathComponent:@"LiveContainer/Cabrillo.shortcut"].path error:NULL];
    Check(!CJShortcutImportData(copy,@"LiveContainer",&failure),@"symlink rejected");
    NSURL *manifest=[copy URLByAppendingPathComponent:@"manifest.json"];
    [@"[]" writeToURL:manifest atomically:YES encoding:NSUTF8StringEncoding error:NULL];
    Check(!CJShortcutImportData(copy,@"Standalone",&failure),@"wrong manifest shape rejected");
    [@"{\"build\":49,\"signed\":true,\"callback_protocol\":\"cabrillo-39\",\"files\":[]}" writeToURL:manifest atomically:YES encoding:NSUTF8StringEncoding error:NULL];
    Check(!CJShortcutImportData(copy,@"Standalone",&failure),@"wrong manifest files shape rejected");
    printf("PASS %lu shortcut installation controls\n",(unsigned long)checks);return 0;
}}
