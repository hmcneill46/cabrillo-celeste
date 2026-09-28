#import <Foundation/Foundation.h>
NSDictionary *CJShortcutHostContext(BOOL container);
// LiveContainer's host whitelist can deny queries for installed guest helpers.
// In that environment, actual open completions and service replies decide readiness.
NSString *CJShortcutSetupProblem(BOOL container, NSString *provider, NSDictionary *host,
                                BOOL (^canOpen)(NSURL *url));
NSString *CJShortcutColdURL(void);
BOOL CJShortcutHasWiFiAddress(void);
// Run off the main thread. Bounded TCP + unauthenticated lockdown QueryType;
// no pairing material, debugger attachment, Internet request or port scan.
BOOL CJShortcutProbeLocalTunnel(void);
