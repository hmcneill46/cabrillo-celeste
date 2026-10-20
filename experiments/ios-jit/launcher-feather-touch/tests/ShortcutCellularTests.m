#import "CJShortcutSession.h"
#import "CJShortcutRouteProbe.h"
#include <arpa/inet.h>
#include <net/if.h>

static NSUInteger checks;
static NSURL *root;
static void check(BOOL pass,NSString *name) {
    if(!pass){fprintf(stderr,"FAIL %s\n",name.UTF8String);exit(1);}checks++;
}
static CJShortcutSession *session(NSString *name) {
    return [[CJShortcutSession alloc] initWithJournal:[root URLByAppendingPathComponent:[name stringByAppendingString:@"/recovery.json"]] process:NSUUID.UUID.UUIDString];
}
static NSURL *callback(CJShortcutSession *s,NSString *outcome) {
    return CJShortcutGuestURL(@"shortcut-callback",@{@"stage":s.phase,@"token":s.token,@"outcome":outcome,
        @"ack":[NSString stringWithFormat:@"cabrillo-39:%@:%@",s.phase,s.token]});
}
static void ack(CJShortcutSession *s,NSTimeInterval now) {
    check([s callback:callback(s,@"success") now:now],@"matching network-stage receipt accepted");
}
static void routeReady(CJShortcutSession *s,NSTimeInterval now) {
    // The exact49 reducer has no route-only entry point and remains blocked at
    // connect when the service is unavailable until isolation. Compile this
    // same scenario against it as the original failure control.
    if([s respondsToSelector:@selector(localRouteReadyAt:)])[s localRouteReadyAt:now];
}
static void travelConnect(CJShortcutSession *s) {
    [s startTravel:YES restoreWiFi:NO restoreCellular:YES now:0];ack(s,1);
}
static struct in_addr address(const char *text) {struct in_addr a={0};inet_pton(AF_INET,text,&a);return a;}
static void routeControls(void) {
    struct sockaddr_in source={0};source.sin_family=AF_INET;source.sin_addr=address("10.7.1.1");
    struct ifaddrs iface={0};iface.ifa_name="utun6";iface.ifa_flags=IFF_UP|IFF_RUNNING|IFF_POINTOPOINT;iface.ifa_addr=(struct sockaddr *)&source;
    check(CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"current LocalDevVPN source route accepted");
    source.sin_addr=address("10.7.0.2");check(CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"older local VPN interface address supported");
    source.sin_addr=address("10.7.1.1");
    check(!CJShortcutRouteUsesTunnel(address("192.0.2.4"),&iface),@"unrelated active tunnel cannot satisfy selected source route");
    check(!CJShortcutRouteUsesTunnel(source.sin_addr,NULL),@"removed interface rejected");
    for(NSNumber *flag in @[@(IFF_UP),@(IFF_RUNNING),@(IFF_POINTOPOINT)]) {
        iface.ifa_flags=(IFF_UP|IFF_RUNNING|IFF_POINTOPOINT)&~flag.unsignedIntValue;
        check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"inactive or non-point-to-point route rejected");
    }
    iface.ifa_flags=IFF_UP|IFF_RUNNING|IFF_POINTOPOINT|IFF_LOOPBACK;
    check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"loopback interface cannot satisfy VPN route");
    iface.ifa_flags=IFF_UP|IFF_RUNNING|IFF_POINTOPOINT;
    for(NSString *name in @[@"en0",@"pdp_ip0",@"lo0",@"utun"]) {
        iface.ifa_name=(char *)name.UTF8String;
        check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"Wi-Fi cellular loopback and incomplete interface names rejected");
    }
    iface.ifa_name="utun6";
    for(NSString *ip in @[@"0.0.0.0",@"127.0.0.1",@"169.254.1.1"]) {
        source.sin_addr=address(ip.UTF8String);
        check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"unspecified loopback and link-local sources rejected");
    }
    source.sin_addr=address("10.7.1.1");source.sin_family=AF_INET6;
    check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"IPv6 interface cannot match IPv4 route by overlapping memory");
    source.sin_family=AF_INET;
    struct ifaddrs wifi=iface;wifi.ifa_name="en0";wifi.ifa_next=&iface;
    check(CJShortcutRouteUsesTunnel(source.sin_addr,&wifi),@"nonmatching interface cannot mask a later selected tunnel");
    iface.ifa_addr=NULL;check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"addressless interface ignored");
    iface.ifa_addr=(struct sockaddr *)&source;iface.ifa_name=NULL;
    check(!CJShortcutRouteUsesTunnel(source.sin_addr,&iface),@"nameless interface ignored");
    NSString *failure=nil;NSTimeInterval start=NSProcessInfo.processInfo.systemUptime;
    BOOL ready=CJShortcutProbeLocalRoute(&failure);
    check(ready?failure==nil:failure.length>0,@"actual host route result explains readiness without contacting the peer");
    check(NSProcessInfo.processInfo.systemUptime-start<1,@"route inspection does not wait on remote service timeout");
    printf("HOST_ROUTE %s\n",ready?"tunnel":failure.UTF8String);
}
int main(int argc,char **argv) {@autoreleasepool{
    if(argc!=2)return 2;root=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
    CJShortcutSession *s=session(@"cellular");NSMutableArray *commands=[NSMutableArray array];
    s.command=^(NSString *name,NSDictionary *fields){(void)fields;[commands addObject:name];};
    travelConnect(s);
    // The developer endpoint never answers while cellular is active. Only the
    // VPN route is present. The old implementation times out at this point.
    routeReady(s,2);
    check([s.phase isEqual:@"isolate"],@"cellular route reaches isolation without developer service");
    check(s.recoveryRequired && ![commands containsObject:@"jit"],@"route grants neither JIT nor cleared recovery");
    routeReady(s,2.5);[s tickAt:2.5 jitPassed:YES jitFailed:NO detached:YES];
    check([s.phase isEqual:@"isolate"],@"route or cached native result cannot skip isolate receipt");
    ack(s,3);NSString *offlineToken=s.token;
    routeReady(s,4);[s tickAt:4 jitPassed:YES jitFailed:NO detached:YES];
    check([s.phase isEqual:@"verify-offline"] && ![commands containsObject:@"jit"],@"route cannot replace offline Remote Pairing hello");
    [s tunnelReadyAt:5];check([s.phase isEqual:@"jit"] && ![s.token isEqual:offlineToken],@"actual offline service advances to a fresh JIT transaction");
    [s tickAt:6 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"jit"],@"service cannot grant native JIT");
    [s tickAt:7 jitPassed:YES jitFailed:NO detached:NO];check([s.phase isEqual:@"jit"],@"native success still waits for detach");
    [s tickAt:8 jitPassed:YES jitFailed:NO detached:YES];check([s.phase isEqual:@"restore"] && s.recoveryRequired,@"detached native success restores preset");
    ack(s,9);check([s.phase isEqual:@"ready"] && !s.recoveryRequired,@"matching restore receipt completes cellular launch");
    check([commands isEqual:@[@"prepare",@"connect-vpn",@"isolate",@"probe-offline",@"jit",@"restore"]],@"cellular command order preserves all gates");

    s=session(@"wifi");[s startTravel:NO restoreWiFi:NO restoreCellular:NO now:0];NSString *firstToken=s.token;
    routeReady(s,1);check([s.phase isEqual:@"connect"] && !s.recoveryRequired,@"route alone cannot advance Wi-Fi launch");
    [s tunnelReadyAt:2];check([s.phase isEqual:@"jit"],@"Wi-Fi still requires the developer service without radio changes");
    [s tickAt:3 jitPassed:YES jitFailed:NO detached:YES];
    [s startTravel:NO restoreWiFi:NO restoreCellular:NO now:4];
    check(![s.token isEqual:firstToken],@"fresh connect token rejects late probes from a prior launch");

    s=session(@"lost-offline-service");travelConnect(s);routeReady(s,2);ack(s,3);
    [s tickAt:29 jitPassed:YES jitFailed:NO detached:YES];
    check([s.phase isEqual:@"restore"] && ![s.snapshot[@"jitVerified"] boolValue],@"lost offline service restores without requesting JIT");
    ack(s,30);check([s.phase isEqual:@"failed"] && [s.snapshot[@"message"] containsString:@"Airplane Mode"],@"offline timeout names the failing stage");

    s=session(@"missing-route");travelConnect(s);[s tickAt:27 jitPassed:NO jitFailed:NO detached:YES];
    check([s.phase isEqual:@"restore"],@"absent route times out before isolation");ack(s,28);
    check([s.phase isEqual:@"failed"] && [s.snapshot[@"message"] containsString:@"VPN connection"],@"route timeout names the failing stage");

    s=session(@"cancel-isolation");travelConnect(s);routeReady(s,2);
    [s callback:callback(s,@"cancel") now:3];check([s.phase isEqual:@"restore"],@"cancelled isolation restores before helper launch");
    routeReady(s,4);check([s.phase isEqual:@"restore"],@"late route completion cannot restart isolation during restore");
    [s tickAt:40 jitPassed:NO jitFailed:NO detached:YES];check([s.phase isEqual:@"recovery"] && s.recoveryRequired,@"missing restoration receipt remains recoverable");
    CJShortcutSession *restarted=session(@"cancel-isolation");check([restarted.phase isEqual:@"recovery"],@"restart retains recovery from failed cellular launch");
    [restarted recoverAt:41 detached:YES];ack(restarted,42);check(!restarted.recoveryRequired,@"explicit recovery clears only after a matching receipt");
    routeControls();printf("PASS %lu cellular route and ordering controls\n",(unsigned long)checks);return 0;
}}
