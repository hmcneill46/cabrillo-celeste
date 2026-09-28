#import "CJShortcutPlatform.h"
#import <objc/message.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <poll.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

static id CJLCValue(NSString *selectorName) {
    Class cls=NSUserDefaults.class;SEL sel=NSSelectorFromString(selectorName);
    return [cls respondsToSelector:sel]?((id(*)(id,SEL))objc_msgSend)(cls,sel):nil;
}
NSDictionary *CJShortcutHostContext(BOOL container) {
    if(!container)return @{@"bundleID":NSBundle.mainBundle.bundleIdentifier?:@"",@"scheme":@"",@"resumeScheme":@"cabrillo"};
    id bundle=CJLCValue(@"lcMainBundle"),scheme=CJLCValue(@"lcAppUrlScheme");
    NSString *identifier=[bundle isKindOfClass:NSBundle.class]?[bundle objectForInfoDictionaryKey:@"CFBundleIdentifier"]:nil;
    if(![identifier isKindOfClass:NSString.class] || !identifier.length ||
       ![scheme isKindOfClass:NSString.class] || ![@[@"livecontainer",@"livecontainer2",@"liveprocess"] containsObject:scheme])return nil;
    return @{@"bundleID":identifier,@"scheme":scheme,@"resumeScheme":scheme};
}
NSString *CJShortcutColdURL(void) {
    id value=CJLCValue(@"lcLaunchURL");return [value isKindOfClass:NSString.class]?value:nil;
}
NSString *CJShortcutSetupProblem(BOOL container, NSString *provider, NSDictionary *host,
                                BOOL (^canOpen)(NSURL *url)) {
    if(![@[@"stikdebug",@"livecontainer2"] containsObject:provider])
        return @"Select your StikDebug installation in Settings. On jailbroken devices, use Check JIT for this launch.";
    if(!host)
        return @"Cabrillo could not identify this app's return route. Reopen Cabrillo from LiveContainer and try again.";
    // canOpenURL uses the installed host's LSApplicationQueriesSchemes. A guest
    // declaration cannot extend that list, and a denied query does not mean the
    // helper is absent. openURL's completion remains authoritative for opening.
    if(container)return nil;
    NSArray *schemes=@[@"shortcuts",@"localdevvpn",provider];
    NSArray *names=@[@"Shortcuts",@"LocalDevVPN",[provider isEqual:@"livecontainer2"]?@"LiveContainer 2":@"StikDebug"];
    for(NSUInteger i=0;i<schemes.count;i++) {
        NSURL *url=[NSURL URLWithString:[schemes[i] stringByAppendingString:@"://"]];
        if(!canOpen || !canOpen(url))return [NSString stringWithFormat:@"%@ is unavailable. Check its installation before using the Home Screen shortcut.",names[i]];
    }
    return nil;
}
BOOL CJShortcutHasWiFiAddress(void) {
    struct ifaddrs *list=NULL;if(getifaddrs(&list)!=0)return NO;BOOL ready=NO;
    for(struct ifaddrs *p=list;p;p=p->ifa_next) {
        if(!p->ifa_addr || strcmp(p->ifa_name,"en0") || !(p->ifa_flags&IFF_UP) || !(p->ifa_flags&IFF_RUNNING))continue;
        if(p->ifa_addr->sa_family==AF_INET) {
            uint32_t a=ntohl(((struct sockaddr_in *)p->ifa_addr)->sin_addr.s_addr);
            ready=a!=0 && (a>>16)!=0xa9fe;
        } else if(p->ifa_addr->sa_family==AF_INET6) {
            struct in6_addr a=((struct sockaddr_in6 *)p->ifa_addr)->sin6_addr;
            ready=!IN6_IS_ADDR_LINKLOCAL(&a) && !IN6_IS_ADDR_UNSPECIFIED(&a);
        }
        if(ready)break;
    }
    freeifaddrs(list);return ready;
}
static BOOL CJTransfer(int fd, void *bytes, size_t length, BOOL reading, NSTimeInterval deadline) {
    size_t offset=0;
    while(offset<length) {
        int remaining=(int)((deadline-NSProcessInfo.processInfo.systemUptime)*1000);
        if(remaining<=0)return NO;
        struct pollfd p={fd,reading?POLLIN:POLLOUT,0};int result=poll(&p,1,remaining);
        if(result<0 && errno==EINTR)continue;
        if(result<=0 || (p.revents&(POLLERR|POLLNVAL)))return NO;
        ssize_t n=reading?recv(fd,(char*)bytes+offset,length-offset,0):send(fd,(char*)bytes+offset,length-offset,0);
        if(n<0 && (errno==EINTR || errno==EAGAIN))continue;
        if(n<=0)return NO;offset+=(size_t)n;
    }return YES;
}
static BOOL CJProbeFailure(NSString **failure,NSString *message) {
    if(failure)*failure=message;return NO;
}
static id CJDictionaryValue(id value,NSString *key) {
    return [value isKindOfClass:NSDictionary.class]?value[key]:nil;
}
BOOL CJShortcutProbeConnectedSocket(int fd,NSTimeInterval deadline,NSString **failure) {
    if(failure)*failure=nil;
    // This is only the unauthenticated hello. Closing here cannot pair a host,
    // verify a pairing file, establish an encrypted tunnel or attach a debugger.
    NSDictionary *hello=@{@"message":@{@"plain":@{@"_0":@{@"request":@{@"_0":@{@"handshake":@{@"_0":@{
        @"hostOptions":@{@"attemptPairVerify":@YES},@"wireProtocolVersion":@19}}}}}}},
        @"originatedBy":@"host",@"sequenceNumber":@0};
    NSData *body=[NSJSONSerialization dataWithJSONObject:hello options:0 error:NULL];
    const char magic[]="RPPairing";
    NSMutableData *request=[NSMutableData dataWithBytes:magic length:sizeof(magic)-1];
    uint16_t length=htons((uint16_t)body.length);[request appendBytes:&length length:sizeof(length)];[request appendData:body];
    if(!CJTransfer(fd,(void *)request.bytes,request.length,NO,deadline))return CJProbeFailure(failure,@"hello_send_failed");
    char responseMagic[sizeof(magic)-1];
    if(!CJTransfer(fd,responseMagic,sizeof(responseMagic),YES,deadline))return CJProbeFailure(failure,@"hello_reply_unavailable");
    if(memcmp(responseMagic,magic,sizeof(responseMagic)))return CJProbeFailure(failure,@"unexpected_service");
    if(!CJTransfer(fd,&length,sizeof(length),YES,deadline))return CJProbeFailure(failure,@"hello_length_unavailable");
    NSUInteger count=ntohs(length);
    if(count==0 || count>16384)return CJProbeFailure(failure,@"hello_reply_size_invalid");
    NSMutableData *reply=[NSMutableData dataWithLength:count];
    if(!CJTransfer(fd,reply.mutableBytes,count,YES,deadline))return CJProbeFailure(failure,@"hello_body_unavailable");
    id envelope=[NSJSONSerialization JSONObjectWithData:reply options:NSJSONReadingFragmentsAllowed error:NULL];
    id handshake=envelope;
    for(NSString *key in @[@"message",@"plain",@"_0",@"response",@"_1",@"handshake",@"_0"])handshake=CJDictionaryValue(handshake,key);
    id version=CJDictionaryValue(handshake,@"wireProtocolVersion");
    id minimum=CJDictionaryValue(handshake,@"minimumSupportedWireProtocolVersion");
    id incoming=CJDictionaryValue(CJDictionaryValue(handshake,@"deviceOptions"),@"allowsIncomingTunnelConnections");
    id sequence=CJDictionaryValue(envelope,@"sequenceNumber");
    if(![CJDictionaryValue(envelope,@"originatedBy") isEqual:@"device"] ||
       ![sequence isKindOfClass:NSNumber.class] || [sequence integerValue]!=0 ||
       ![version isKindOfClass:NSNumber.class] || [version integerValue]<19 ||
       ![minimum isKindOfClass:NSNumber.class] || [minimum integerValue]<1 || [minimum integerValue]>19 ||
       ![incoming isKindOfClass:NSNumber.class] || ![incoming boolValue])
        return CJProbeFailure(failure,@"hello_service_not_ready");
    return YES;
}
BOOL CJShortcutProbeLocalTunnel(NSString **failure) {
    if(failure)*failure=nil;
    int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return CJProbeFailure(failure,@"socket_unavailable");
    int flags=fcntl(fd,F_GETFL);if(flags<0 || fcntl(fd,F_SETFL,flags|O_NONBLOCK)<0){close(fd);return CJProbeFailure(failure,@"socket_configuration_failed");}
    int yes=1;setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&yes,sizeof(yes));
    struct sockaddr_in peer={0};peer.sin_len=sizeof(peer);peer.sin_family=AF_INET;peer.sin_port=htons(49152);inet_pton(AF_INET,"10.7.0.1",&peer.sin_addr);
    NSTimeInterval deadline=NSProcessInfo.processInfo.systemUptime+1.5;
    BOOL ok=connect(fd,(struct sockaddr*)&peer,sizeof(peer))==0;
    if(!ok && errno==EINPROGRESS) {
        struct pollfd p={fd,POLLOUT,0};int result=poll(&p,1,700),error=0;socklen_t size=sizeof(error);
        ok=result>0 && getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&size)==0 && error==0;
    }
    if(ok)ok=CJShortcutProbeConnectedSocket(fd,deadline,failure);
    else CJProbeFailure(failure,@"endpoint_unreachable");
    close(fd);return ok;
}
