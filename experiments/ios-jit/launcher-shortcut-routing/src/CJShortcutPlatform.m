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
BOOL CJShortcutProbeLocalTunnel(void) {
    int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return NO;
    int flags=fcntl(fd,F_GETFL);if(flags<0 || fcntl(fd,F_SETFL,flags|O_NONBLOCK)<0){close(fd);return NO;}
    int yes=1;setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&yes,sizeof(yes));
    struct sockaddr_in peer={0};peer.sin_len=sizeof(peer);peer.sin_family=AF_INET;peer.sin_port=htons(62078);inet_pton(AF_INET,"10.7.0.1",&peer.sin_addr);
    NSTimeInterval deadline=NSProcessInfo.processInfo.systemUptime+1.5;
    BOOL ok=connect(fd,(struct sockaddr*)&peer,sizeof(peer))==0;
    if(!ok && errno==EINPROGRESS) {
        struct pollfd p={fd,POLLOUT,0};int result=poll(&p,1,700),error=0;socklen_t size=sizeof(error);
        ok=result>0 && getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&size)==0 && error==0;
    }
    if(ok) {
        NSData *request=[NSPropertyListSerialization dataWithPropertyList:@{@"Label":@"Cabrillo",@"Request":@"QueryType"} format:NSPropertyListXMLFormat_v1_0 options:0 error:NULL];
        uint32_t length=htonl((uint32_t)request.length);
        ok=CJTransfer(fd,&length,4,NO,deadline) && CJTransfer(fd,(void*)request.bytes,request.length,NO,deadline) && CJTransfer(fd,&length,4,YES,deadline);
        length=ntohl(length);
        if(ok && length>0 && length<=16384) {
            NSMutableData *reply=[NSMutableData dataWithLength:length];ok=CJTransfer(fd,reply.mutableBytes,length,YES,deadline);
            id plist=ok?[NSPropertyListSerialization propertyListWithData:reply options:0 format:NULL error:NULL]:nil;
            ok=[plist isKindOfClass:NSDictionary.class] && [plist[@"Type"] isEqual:@"com.apple.mobile.lockdown"];
        } else ok=NO;
    }
    close(fd);return ok;
}
