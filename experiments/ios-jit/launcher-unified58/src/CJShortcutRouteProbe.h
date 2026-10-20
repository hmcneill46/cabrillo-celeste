#import <Foundation/Foundation.h>
#include <ifaddrs.h>
#include <netinet/in.h>

// Inspect the route to LocalDevVPN's fixed peer without sending any packets.
// This proves a tunnel route exists, not VPN ownership or developer readiness.
BOOL CJShortcutProbeLocalRoute(NSString **failure);

// Shared with host controls for stale, inactive and unrelated interface cases.
BOOL CJShortcutRouteUsesTunnel(struct in_addr selected, const struct ifaddrs *interfaces);
