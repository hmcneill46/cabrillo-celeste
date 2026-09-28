#import <Foundation/Foundation.h>

// The reducer owns launch ordering and recovery. UIKit, the helper and network
// probes cannot grant JIT readiness: only the existing native checks can do that.
@interface CJShortcutSession : NSObject
@property(nonatomic, readonly) NSString *phase;
@property(nonatomic, readonly) NSString *token;
@property(nonatomic, readonly) BOOL active;
@property(nonatomic, readonly) BOOL recoveryRequired;
@property(nonatomic, readonly) NSDictionary *snapshot;
@property(nonatomic, copy) void (^command)(NSString *, NSDictionary *);
@property(nonatomic, copy) void (^changed)(NSDictionary *);
- (instancetype)initWithJournal:(NSURL *)journal process:(NSString *)process;
- (void)startTravel:(BOOL)travel restoreWiFi:(BOOL)wifi restoreCellular:(BOOL)cellular now:(NSTimeInterval)now;
- (void)tunnelReadyAt:(NSTimeInterval)now;
- (BOOL)callback:(NSURL *)url now:(NSTimeInterval)now;
- (void)tickAt:(NSTimeInterval)now jitPassed:(BOOL)passed jitFailed:(BOOL)failed detached:(BOOL)detached;
- (void)fail:(NSString *)reason now:(NSTimeInterval)now;
- (void)recoverAt:(NSTimeInterval)now detached:(BOOL)detached;
- (void)cancelAt:(NSTimeInterval)now detached:(BOOL)detached;
@end

NSURL *CJShortcutGuestURL(NSString *host, NSDictionary<NSString *, NSString *> *query);
NSURL *CJShortcutRoute(NSURL *guestURL, NSString *containerScheme);
NSURL *CJShortcutRunURL(NSString *stage, NSString *token, NSDictionary *fields, NSString *containerScheme);
