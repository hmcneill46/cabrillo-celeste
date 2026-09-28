#import "CJShortcutSession.h"
#import "CJShortcutPlatform.h"
#import "CJPlatformOptions.h"
#include <sys/socket.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
static NSUInteger checks;
static void check(BOOL pass,NSString *name){if(!pass){fprintf(stderr,"FAIL %s\n",name.UTF8String);exit(1);}checks++;}
static NSData *rpFrame(id value) {
    NSData *body=[NSJSONSerialization dataWithJSONObject:value options:NSJSONWritingFragmentsAllowed error:NULL];
    NSMutableData *frame=[NSMutableData dataWithBytes:"RPPairing" length:9];
    uint16_t length=htons((uint16_t)body.length);[frame appendBytes:&length length:2];[frame appendData:body];return frame;
}
static BOOL readBytes(int fd,void *bytes,size_t count) {
    size_t offset=0;
    while(offset<count){ssize_t n=recv(fd,(char *)bytes+offset,count-offset,0);if(n<=0)return NO;offset+=(size_t)n;}
    return YES;
}
static void probeControl(NSData *response,BOOL fragmented,NSString *expectedFailure,NSString *name) {
    int pair[2];if(socketpair(AF_UNIX,SOCK_STREAM,0,pair))exit(2);
    fcntl(pair[0],F_SETFL,fcntl(pair[0],F_GETFL)|O_NONBLOCK);
    for(int i=0;i<2;i++){int yes=1;setsockopt(pair[i],SOL_SOCKET,SO_NOSIGPIPE,&yes,sizeof(yes));}
    struct timeval timeout={1,0};setsockopt(pair[1],SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
    int server=pair[1];__block BOOL validHello=NO;dispatch_group_t group=dispatch_group_create();
    dispatch_group_async(group,dispatch_get_global_queue(QOS_CLASS_UTILITY,0),^{@autoreleasepool{
        char header[9];uint16_t length=0;
        if(readBytes(server,header,9) && !memcmp(header,"RPPairing",9) && readBytes(server,&length,2)) {
            NSMutableData *data=[NSMutableData dataWithLength:ntohs(length)];
            if(readBytes(server,data.mutableBytes,data.length)) {
                NSDictionary *request=[NSJSONSerialization JSONObjectWithData:data options:0 error:NULL];
                NSDictionary *hello=request[@"message"][@"plain"][@"_0"][@"request"][@"_0"][@"handshake"][@"_0"];
                validHello=[request[@"originatedBy"] isEqual:@"host"] && [request[@"sequenceNumber"] isEqual:@0] &&
                    [hello isEqual:@{@"hostOptions":@{@"attemptPairVerify":@YES},@"wireProtocolVersion":@19}];
            }
        }
        if(!response)usleep(200000);
        else for(NSUInteger offset=0;offset<response.length;) {
            NSUInteger count=fragmented?MIN((NSUInteger)3,response.length-offset):response.length-offset;
            ssize_t n=send(server,(const char *)response.bytes+offset,count,0);if(n<=0)break;offset+=(NSUInteger)n;
            if(fragmented)usleep(1000);
        }
        close(server);
    }});
    NSTimeInterval start=NSProcessInfo.processInfo.systemUptime;NSString *failure=nil;
    BOOL ready=CJShortcutProbeConnectedSocket(pair[0],start+(response?1.5:0.08),&failure);close(pair[0]);
    if(dispatch_group_wait(group,dispatch_time(DISPATCH_TIME_NOW,2*NSEC_PER_SEC)))exit(2);
    check(validHello,@"probe sends only the documented unauthenticated hello");
    check(ready==(expectedFailure==nil) && (expectedFailure?[failure isEqual:expectedFailure]:failure==nil),name);
    if(!response)check(NSProcessInfo.processInfo.systemUptime-start<1.0,@"silent peer is bounded by deadline");
}
static void tunnelControls(void) {
    NSDictionary *hello=@{@"wireProtocolVersion":@24,@"minimumSupportedWireProtocolVersion":@8,
        @"deviceOptions":@{@"allowsIncomingTunnelConnections":@YES}};
    NSDictionary *(^envelope)(id)=^NSDictionary *(id value){return @{@"originatedBy":@"device",@"sequenceNumber":@0,
        @"message":@{@"plain":@{@"_0":@{@"response":@{@"_1":@{@"handshake":@{@"_0":value}}}}}}};};
    probeControl(rpFrame(envelope(hello)),NO,nil,@"actual phone protocol24 accepts requested19");
    probeControl(rpFrame(envelope(hello)),YES,nil,@"fragmented Remote Pairing reply accepted");
    NSMutableDictionary *h=[hello mutableCopy];h[@"deviceOptions"]=@{@"allowsIncomingTunnelConnections":@NO};
    probeControl(rpFrame(envelope(h)),NO,@"hello_service_not_ready",@"control-only service cannot grant tunnel readiness");
    h=[hello mutableCopy];h[@"minimumSupportedWireProtocolVersion"]=@20;
    probeControl(rpFrame(envelope(h)),NO,@"hello_service_not_ready",@"unsupported protocol range rejected");
    probeControl(rpFrame(envelope(@[])),NO,@"hello_service_not_ready",@"wrong handshake type is rejected without exception");
    probeControl(rpFrame(@[]),NO,@"hello_service_not_ready",@"non-object JSON is rejected without exception");
    NSMutableDictionary *e=[envelope(hello) mutableCopy];e[@"originatedBy"]=@"host";
    probeControl(rpFrame(e),NO,@"hello_service_not_ready",@"reflected request cannot pass");
    e=[envelope(hello) mutableCopy];e[@"sequenceNumber"]=@1;
    probeControl(rpFrame(e),NO,@"hello_service_not_ready",@"unrelated reply sequence rejected");
    NSMutableData *frame=[rpFrame(envelope(hello)) mutableCopy];((char *)frame.mutableBytes)[0]='X';
    probeControl(frame,NO,@"unexpected_service",@"wrong framing rejected");
    frame=[NSMutableData dataWithBytes:"RPPairing\x40\x01" length:11];
    probeControl(frame,NO,@"hello_reply_size_invalid",@"oversized response rejected before allocation");
    probeControl([NSData dataWithBytes:"RPPairing\0\0" length:11],NO,@"hello_reply_size_invalid",@"empty response rejected");
    probeControl([NSData dataWithBytes:"RPPairing\0\x04{}" length:13],NO,@"hello_body_unavailable",@"truncated body fails closed");
    probeControl([NSData data],NO,@"hello_reply_unavailable",@"closed endpoint fails closed");
    probeControl(nil,NO,@"hello_reply_unavailable",@"silent endpoint cannot hang launch");
}
static NSURL *root;
static NSURL *guestFixture(NSURL *apps,NSString *name,NSDictionary *info,NSDictionary *metadata) {
    NSURL *folder=[apps URLByAppendingPathComponent:name isDirectory:YES];
    [NSFileManager.defaultManager createDirectoryAtURL:folder withIntermediateDirectories:YES attributes:nil error:NULL];
    [info writeToURL:[folder URLByAppendingPathComponent:@"Info.plist"] atomically:YES];
    [metadata writeToURL:[folder URLByAppendingPathComponent:@"LCAppInfo.plist"] atomically:YES];
    return folder;
}
static void guestControls(void) {
    NSString *failure=nil;
    check(!CJShortcutStikGuest(&failure) && failure.length,@"unavailable LC runtime cannot guess a helper");
    NSURL *apps=[root URLByAppendingPathComponent:@"helper-fixtures" isDirectory:YES];
    check(!CJShortcutFindStikGuest(apps,&failure) && failure.length,@"unreadable shared directory gives setup error");
    [NSFileManager.defaultManager createDirectoryAtURL:apps withIntermediateDirectories:YES attributes:nil error:NULL];
    check(!CJShortcutFindStikGuest(apps,&failure) && [failure containsString:@"No shared"],@"empty shared directory cannot dispatch");
    NSDictionary *info=@{@"CFBundleIdentifier":@"com.stik.stikdebug",@"CFBundleURLTypes":@[@{@"CFBundleURLSchemes":@[@"stikdebug"]}]};
    NSURL *folder=guestFixture(apps,@"installed-helper.app",info,@{@"LCDataUUID":@"actual-data-folder"});
    NSDictionary *guest=CJShortcutFindStikGuest(apps,&failure);
    check(!failure && [guest[@"bundleFolder"] isEqual:@"installed-helper.app"] && [guest[@"containerFolder"] isEqual:@"actual-data-folder"],@"discover actual helper bundle folder and data selection");
    NSURL *inner=CJPlatformJITURL(@"stikdebug",7654,@"actual.host",@"fresh.js",@"fresh script + / =");
    NSURL *route=CJShortcutStikGuestURL(guest,inner);
    NSMutableDictionary *q=[NSMutableDictionary dictionary];
    for(NSURLQueryItem *item in [NSURLComponents componentsWithURL:route resolvingAgainstBaseURL:NO].queryItems)q[item.name]=item.value;
    check([route.scheme isEqual:@"livecontainer2"] && [route.host isEqual:@"livecontainer-launch"] && [q[@"bundle-name"] isEqual:guest[@"bundleFolder"]],@"cold URL explicitly selects shared helper");
    check([q[@"container-folder-name"] isEqual:guest[@"containerFolder"]] && !q[@"jit"],@"preserve helper settings and exact data container");
    NSString *decoded=[[NSString alloc] initWithData:[[NSData alloc] initWithBase64EncodedString:q[@"open-url"] options:0] encoding:NSUTF8StringEncoding];
    check([decoded isEqual:inner.absoluteString],@"wrapper preserves fresh PID script and actual host return byte for byte");
    check(!CJPlatformJITURL(@"livecontainer2",7654,@"actual.host",nil,nil),@"old generic guest URL cannot be used accidentally");
    check(!CJShortcutStikGuestURL(@{},inner) && !CJShortcutStikGuestURL(guest,[NSURL URLWithString:@"https://example.invalid"]),@"missing guest and unrelated inner routes rejected");
    check(!CJShortcutStikGuestURL(@{@"bundleFolder":@"../unrelated.app"},inner),@"guest path traversal rejected");
    [@{} writeToURL:[folder URLByAppendingPathComponent:@"LCAppInfo.plist"] atomically:YES];
    guest=CJShortcutFindStikGuest(apps,&failure);
    route=CJShortcutStikGuestURL(guest,inner);
    check(guest && !guest[@"containerFolder"] && ![route.absoluteString containsString:@"container-folder-name"],@"helper without default data defers selection to LiveContainer");
    NSMutableDictionary *hostInfo=[info mutableCopy];hostInfo[@"CFBundleIdentifier"]=@"lc.host";
    guestFixture(apps,@"installed-helper.app",hostInfo,@{@"doUseLCBundleId":@YES,@"LCOrignalBundleIdentifier":@"com.stik.stikdebug",@"LCDataUUID":@"actual"});
    check(CJShortcutFindStikGuest(apps,&failure)!=nil,@"LC host bundle rewrite retains original helper identity");
    NSURL *duplicate=guestFixture(apps,@"second-helper.app",info,@{});
    check(!CJShortcutFindStikGuest(apps,&failure) && [failure containsString:@"More than one"],@"ambiguous shared helper requires a choice before request");
    [NSFileManager.defaultManager removeItemAtURL:duplicate error:NULL];
    guestFixture(apps,@"installed-helper.app",info,@{@"LCDataUUID":@"../unrelated"});
    check(!CJShortcutFindStikGuest(apps,&failure) && [failure containsString:@"invalid"],@"invalid helper data folder fails closed");
    guestFixture(apps,@"installed-helper.app",@{@"CFBundleIdentifier":@"com.stik.stikdebug",@"CFBundleURLTypes":@[@"malformed"]},@{});
    check(!CJShortcutFindStikGuest(apps,&failure),@"identifier alone cannot select a helper without its URL scheme");
    guestFixture(apps,@"installed-helper.app",@{@"CFBundleIdentifier":@"unrelated.app",@"CFBundleURLTypes":info[@"CFBundleURLTypes"]},@{});
    check(!CJShortcutFindStikGuest(apps,&failure),@"scheme alone cannot redirect the fresh script to an unrelated app");
    [NSFileManager.defaultManager removeItemAtURL:folder error:NULL];
    NSURL *external=guestFixture(root,@"external-helper.app",info,@{});
    [NSFileManager.defaultManager createSymbolicLinkAtURL:folder withDestinationURL:external error:NULL];
    check(!CJShortcutFindStikGuest(apps,&failure),@"shared discovery ignores links outside its application directory");
    [NSFileManager.defaultManager removeItemAtURL:folder error:NULL];
    guestFixture(apps,@"installed-helper.app",info,@{});
    NSURL *lcFile=[folder URLByAppendingPathComponent:@"Info.plist"];
    [[NSMutableData dataWithLength:1024*1024+1] writeToURL:lcFile atomically:YES];
    check(!CJShortcutFindStikGuest(apps,&failure),@"metadata read is bounded");
}
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
    tunnelControls();
    guestControls();
    printf("PASS %lu shortcut launch controls\n",(unsigned long)checks);
}return 0;}
