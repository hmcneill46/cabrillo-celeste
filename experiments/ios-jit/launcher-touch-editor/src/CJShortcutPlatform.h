#import <Foundation/Foundation.h>
NSDictionary *CJShortcutHostContext(BOOL container);
// LiveContainer's host whitelist can deny queries for installed guest helpers.
// In that environment, actual open completions and service replies decide readiness.
NSString *CJShortcutSetupProblem(BOOL container, NSString *provider, NSDictionary *host,
                                BOOL (^canOpen)(NSURL *url));
NSString *CJShortcutColdURL(void);
// Discover the actual shared StikDebug guest through LiveContainer's entitled
// app group. Never guess its folder or redirect a fresh request to another app.
NSDictionary *CJShortcutStikGuest(NSString **failure);
NSDictionary *CJShortcutFindStikGuest(NSURL *applications, NSString **failure);
NSURL *CJShortcutStikGuestURL(NSDictionary *guest, NSURL *jitURL);
BOOL CJShortcutHasWiFiAddress(void);
// Run off the main thread. Bounded Remote Pairing hello at StikDebug's endpoint;
// no pairing material, pair-setup/verify, debugger attachment or Internet request.
BOOL CJShortcutProbeLocalTunnel(NSString **failure);
// Connected nonblocking socket, also used by the protocol/timeout host controls.
// The caller retains ownership of the socket. No pairing/device metadata is retained.
BOOL CJShortcutProbeConnectedSocket(int fd, NSTimeInterval deadline, NSString **failure);
