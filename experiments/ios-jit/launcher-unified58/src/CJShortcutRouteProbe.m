#import "CJShortcutRouteProbe.h"
#include <arpa/inet.h>
#include <net/if.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string.h>

BOOL CJShortcutRouteUsesTunnel(struct in_addr selected, const struct ifaddrs *interfaces) {
    uint32_t address=ntohl(selected.s_addr);
    if(!address || (address>>24)==127 || (address>>16)==0xa9fe)return NO;
    for(const struct ifaddrs *p=interfaces;p;p=p->ifa_next) {
        if(!p->ifa_name || !p->ifa_addr || p->ifa_addr->sa_family!=AF_INET ||
           strncmp(p->ifa_name,"utun",4) || !p->ifa_name[4])continue;
        unsigned required=IFF_UP|IFF_RUNNING|IFF_POINTOPOINT;
        if((p->ifa_flags&required)!=required || (p->ifa_flags&IFF_LOOPBACK))continue;
        if(((const struct sockaddr_in *)p->ifa_addr)->sin_addr.s_addr==selected.s_addr)return YES;
    }
    return NO;
}
static BOOL CJRouteFailure(NSString **failure,NSString *reason) {
    if(failure)*failure=reason;return NO;
}
BOOL CJShortcutProbeLocalRoute(NSString **failure) {
    if(failure)*failure=nil;
    int fd=socket(AF_INET,SOCK_DGRAM,0);
    if(fd<0)return CJRouteFailure(failure,@"route_socket_unavailable");
    struct sockaddr_in peer={0},local={0};
    peer.sin_len=sizeof(peer);peer.sin_family=AF_INET;peer.sin_port=htons(49152);
    inet_pton(AF_INET,"10.7.0.1",&peer.sin_addr);
    socklen_t length=sizeof(local);
    // UDP connect chooses a route/source locally. It neither sends a datagram
    // nor waits for the developer service (which may require Airplane Mode).
    BOOL resolved=connect(fd,(struct sockaddr *)&peer,sizeof(peer))==0 &&
        getsockname(fd,(struct sockaddr *)&local,&length)==0 &&
        length>=sizeof(local) && local.sin_family==AF_INET;
    close(fd);
    if(!resolved)return CJRouteFailure(failure,@"local_route_unavailable");
    struct ifaddrs *interfaces=NULL;
    if(getifaddrs(&interfaces)!=0)return CJRouteFailure(failure,@"route_interfaces_unavailable");
    BOOL ready=CJShortcutRouteUsesTunnel(local.sin_addr,interfaces);
    freeifaddrs(interfaces);
    if(!ready)return CJRouteFailure(failure,@"local_route_not_tunnel");
    return YES;
}
