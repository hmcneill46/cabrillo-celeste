#import <Foundation/Foundation.h>
NSDictionary *CJShortcutHostContext(BOOL container);
NSString *CJShortcutColdURL(void);
BOOL CJShortcutHasWiFiAddress(void);
// Run off the main thread. Bounded TCP + unauthenticated lockdown QueryType;
// no pairing material, debugger attachment, Internet request or port scan.
BOOL CJShortcutProbeLocalTunnel(void);
