#import "CJShortcutSession.h"
#import "CJShortcutPlatform.h"
#import "CJPlatformOptions.h"
static NSUInteger checks;
static void check(BOOL pass,NSString *name){if(!pass){fprintf(stderr,"FAIL %s\n",name.UTF8String);exit(1);}checks++;}
static NSURL *root;
static CJShortcutSession *session(NSString *name){return [[CJShortcutSession alloc] initWithJournal:[root URLByAppendingPathComponent:[name stringByAppendingString:@"/recovery.json"]] process:NSUUID.UUID.UUIDString];}
static NSURL *callback(CJShortcutSession *s,NSString *stage,NSString *outcome){return CJShortcutGuestURL(@"shortcut-callback",@{@"stage":stage,@"token":s.token,@"outcome":outcome,@"ack":[NSString stringWithFormat:@"cabrillo-39:%@:%@",stage,s.token]});}
static void ack(CJShortcutSession *s){check([s callback:callback(s,s.phase,@"success") now:3],@"expected callback accepted");}
static void travelToJIT(CJShortcutSession *s){[s startTravel:YES restoreWiFi:NO restoreCellular:YES now:0];ack(s);[s tunnelReadyAt:2];ack(s);[s tunnelReadyAt:4];}
int main(int argc,char **argv){@autoreleasepool{
    if(argc!=2)return 2;root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
    CJShortcutSession *s=session(@"wifi");NSMutableArray *commands=[NSMutableArray array];
    s.command=^(NSString *name,NSDictionary *fields){(void)fields;[commands addObject:name];};
    [s startTravel:NO restoreWiFi:NO restoreCellular:NO now:0];
    check([s.phase isEqual:@"connect"] && !s.recoveryRequired,@"wifi path makes no network recovery writes");
    [s startTravel:YES restoreWiFi:YES restoreCellular:YES now:1];check(commands.count==1,@"duplicate start coalesces");
    [s tickAt:1 jitPassed:YES jitFailed:NO detached:YES];check([s.phase isEqual:@"connect"],@"jit cannot bypass tunnel");
    [s tunnelReadyAt:2];check([s.phase isEqual:@"jit"],@"verified tunnel precedes request");
    [s tickAt:3 jitPassed:YES jitFailed:NO detached:YES];check([s.phase isEqual:@"jit"],@"wait for shortcut return before next shortcut");
    NSURL *old=callback(s,@"jit",@"success");ack(s);
    [s tickAt:4 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"jit"],@"shortcut success cannot grant jit");
    [s tickAt:5 jitPassed:YES jitFailed:NO detached:NO];check([s.phase isEqual:@"jit"],@"native pass cannot bypass detach");
    [s tickAt:6 jitPassed:YES jitFailed:NO detached:YES];check([s.phase isEqual:@"ready"],@"real native pass after detach grants readiness");
    check(![s callback:old now:7],@"completed callback replay rejected");
    check([commands isEqual:@[@"connect-vpn",@"jit"]],@"wifi has no radio actions");

    s=session(@"travel");travelToJIT(s);check(s.recoveryRequired,@"travel persists recovery before radios");ack(s);
    [s tickAt:5 jitPassed:YES jitFailed:NO detached:YES];check([s.phase isEqual:@"restore"] && s.recoveryRequired,@"restore follows actual jit verification");
    old=callback(s,@"restore",@"success");ack(s);check([s.phase isEqual:@"ready"] && !s.recoveryRequired,@"restore receipt clears journal");
    check(!session(@"travel").recoveryRequired,@"completed journal absent on new process");

    s=session(@"interrupted");[s startTravel:YES restoreWiFi:NO restoreCellular:YES now:0];old=callback(s,@"prepare",@"success");
    CJShortcutSession *fresh=session(@"interrupted");check(fresh.recoveryRequired && !fresh.active,@"new process sees recovery");
    check(![fresh callback:old now:2],@"old process callback cannot grant anything");
    [fresh startTravel:NO restoreWiFi:YES restoreCellular:NO now:3];
    check([fresh.phase isEqual:@"restore"] && ![fresh.snapshot[@"restoreWiFi"] boolValue] && [fresh.snapshot[@"restoreCellular"] boolValue],@"recover old preset before honoring new launch choices");
    ack(fresh);check([fresh.phase isEqual:@"failed"] && !fresh.recoveryRequired && ![fresh.snapshot[@"jitVerified"] boolValue],@"recovery never grants old process jit");

    s=session(@"forged");[s startTravel:YES restoreWiFi:YES restoreCellular:YES now:0];
    check(![s callback:CJShortcutGuestURL(@"shortcut-callback",@{@"stage":@"prepare",@"token":@"wrong",@"outcome":@"success"}) now:1],@"wrong nonce rejected");
    check(![s callback:callback(s,@"restore",@"success") now:1],@"out-of-order restore rejected");
    check(![s callback:[NSURL URLWithString:[callback(s,@"prepare",@"success").absoluteString stringByAppendingString:@"&token=other"]] now:1],@"duplicate fields rejected");
    [s tickAt:40 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"recovery"] && s.recoveryRequired,@"stalled radio shortcut needs recovery without concurrent radio writes");

    s=session(@"offline-failure");[s startTravel:YES restoreWiFi:YES restoreCellular:NO now:0];ack(s);[s tunnelReadyAt:2];ack(s);
    check([s.phase isEqual:@"verify-offline"],@"must verify vpn after airplane mode too");
    [s tickAt:40 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"restore"],@"lost offline tunnel restores before any jit request");
    [s callback:callback(s,@"restore",@"error") now:41];check([s.phase isEqual:@"recovery"] && s.recoveryRequired,@"restore action error retains recovery");
    [s recoverAt:42 detached:YES];[s fail:@"URL failed" now:43];check([s.phase isEqual:@"recovery"],@"restore open failure cannot recurse");

    s=session(@"cancel");travelToJIT(s);old=callback(s,@"jit",@"success");
    [s cancelAt:5 detached:YES];check([s.phase isEqual:@"waiting-detach"],@"cancel cannot cut tunnel before delayed helper attach");
    check([s callback:old now:6],@"handoff can finish after cancellation");
    [s tickAt:7 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"waiting-detach"],@"early detach is insufficient while helper pending");
    [s tickAt:8 jitPassed:NO jitFailed:YES detached:NO];check([s.phase isEqual:@"waiting-detach"],@"failed jit still must detach");
    [s tickAt:9 jitPassed:NO jitFailed:YES detached:YES];check([s.phase isEqual:@"restore"],@"terminal detached helper permits cancellation cleanup");

    s=session(@"late");travelToJIT(s);[s tickAt:200 jitPassed:NO jitFailed:NO detached:NO];
    check([s.phase isEqual:@"waiting-detach"],@"timeout cannot bypass attached debugger");
    [s tickAt:201 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"restore"],@"timeout with detach recovers");

    NSURL *journal=[root URLByAppendingPathComponent:@"bad/recovery.json"];
    [NSFileManager.defaultManager createDirectoryAtURL:journal.URLByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:NULL];
    [@"broken" writeToURL:journal atomically:YES encoding:NSUTF8StringEncoding error:NULL];
    check(session(@"bad").recoveryRequired,@"corrupt recovery cannot be ignored");
    NSURL *blocked=[root URLByAppendingPathComponent:@"not-a-directory"];
    [@"file" writeToURL:blocked atomically:YES encoding:NSUTF8StringEncoding error:NULL];
    s=[[CJShortcutSession alloc] initWithJournal:[blocked URLByAppendingPathComponent:@"recovery.json"] process:@"test"];
    __block BOOL emitted=NO;s.command=^(NSString *name,NSDictionary *fields){(void)name;(void)fields;emitted=YES;};
    [s startTravel:YES restoreWiFi:YES restoreCellular:YES now:0];check(!emitted && [s.phase isEqual:@"failed"],@"no radio changes without durable recovery");

    NSURL *guest=CJShortcutGuestURL(@"launch",@{}),*route=CJShortcutRoute(guest,@"livecontainer");
    NSString *b64=[NSURLComponents componentsWithURL:route resolvingAgainstBaseURL:NO].queryItems[0].value;
    check([[[NSString alloc] initWithData:[[NSData alloc] initWithBase64EncodedString:b64 options:0] encoding:NSUTF8StringEncoding] isEqual:guest.absoluteString],@"LC URL roundtrip");
    check(!CJShortcutRoute(guest,@"https"),@"unrecognized host scheme rejected");
    NSURL *run=CJShortcutRunURL(@"restore",@"nonce",@{@"wifi":@"off",@"cellular":@"on"},@"livecontainer");
    NSMutableDictionary *params=[NSMutableDictionary dictionary];for(NSURLQueryItem *i in [NSURLComponents componentsWithURL:run resolvingAgainstBaseURL:NO].queryItems)params[i.name]=i.value;
    check(params[@"x-success"] && params[@"x-error"] && params[@"x-cancel"],@"all shortcut exits return to app");
    NSURL *success=[NSURL URLWithString:params[@"x-success"]];b64=[NSURLComponents componentsWithURL:success resolvingAgainstBaseURL:NO].queryItems[0].value;
    NSString *inner=[[NSString alloc] initWithData:[[NSData alloc] initWithBase64EncodedString:b64 options:0] encoding:NSUTF8StringEncoding];
    check([inner containsString:@"ack=cabrillo-39"],@"ack embedded inside LC callback");
    NSString *script=@"fresh pid-bound script + / =";
    NSURL *jit=CJPlatformJITURL(@"stikdebug",1234,@"host.example",@"fresh.js",script);
    params=[NSMutableDictionary dictionary];for(NSURLQueryItem *i in [NSURLComponents componentsWithURL:jit resolvingAgainstBaseURL:NO].queryItems)params[i.name]=i.value;
    check([params[@"pid"] isEqual:@"1234"] && [params[@"bundle-id"] isEqual:@"host.example"],@"helper targets existing PID and returns actual host");
    check(params[@"script-data"] && ![params[@"script-data"] containsString:@"="],@"fresh inline script preserves URL-safe encoding");
    check(!CJShortcutHostContext(YES),@"LC automation fails closed without host introspection");
    NSDictionary *host=@{@"bundleID":@"host.example",@"scheme":@"livecontainer",@"resumeScheme":@"livecontainer"};
    __block NSUInteger queries=0;
    BOOL (^denied)(NSURL *)=^(NSURL *url){(void)url;queries++;return NO;};
    check(!CJShortcutSetupProblem(YES,@"livecontainer2",host,denied) && queries==0,@"LC denied host queries cannot reject installed helpers");
    check(!CJShortcutSetupProblem(YES,@"stikdebug",host,denied) && queries==0,@"standalone helper inside LC also uses actual opening");
    check(CJShortcutSetupProblem(YES,@"manual",host,denied)!=nil && queries==0,@"query bypass cannot enable unsupported providers");
    check(CJShortcutSetupProblem(YES,@"livecontainer2",nil,denied)!=nil && queries==0,@"query bypass still requires real host identity");
    check([CJShortcutSetupProblem(NO,@"stikdebug",host,denied) containsString:@"Shortcuts"] && queries==1,@"direct install reports missing Shortcuts");
    check([CJShortcutSetupProblem(NO,@"stikdebug",host,^BOOL(NSURL *url){return ![url.scheme isEqual:@"localdevvpn"];}) containsString:@"LocalDevVPN"],@"direct install reports missing VPN app");
    check([CJShortcutSetupProblem(NO,@"stikdebug",host,^BOOL(NSURL *url){return ![url.scheme isEqual:@"stikdebug"];}) containsString:@"StikDebug"],@"direct install reports missing selected helper");
    check(!CJShortcutSetupProblem(NO,@"stikdebug",host,^(NSURL *url){(void)url;return YES;}),@"direct installed helpers pass setup");
    printf("PASS %lu shortcut launch controls\n",(unsigned long)checks);
}return 0;}
