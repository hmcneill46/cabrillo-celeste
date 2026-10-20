#import "CJIntegratedJITLaunch.h"

BOOL CJIntegratedJITCanEnterRuntime(BOOL foreground, BOOL profileReady, BOOL profileRestartRequired) {
    return foreground && profileReady && !profileRestartRequired;
}

@interface CJIntegratedJITLaunch ()
@property(nonatomic,copy) NSString *requestID;
@property(nonatomic,copy) NSString *error;
@property(nonatomic) BOOL active;
@property(nonatomic) BOOL helperSucceeded;
@property(nonatomic) BOOL pendingRun;
@property(nonatomic) BOOL failed;
@property(nonatomic) BOOL launchConsumed;
@end

@implementation CJIntegratedJITLaunch
- (BOOL)beginRequest:(NSString *)requestID run:(BOOL)run {
    if (self.requestID || !requestID.length) return NO;
    self.requestID=requestID; self.active=YES; self.pendingRun=run;
    return YES;
}
- (BOOL)requestRun {
    if (!self.requestID || self.failed || self.launchConsumed) return NO;
    self.pendingRun=YES; return YES;
}
- (BOOL)completeRequest:(NSString *)requestID success:(BOOL)success error:(NSString *)error {
    if (!self.active || ![requestID isEqual:self.requestID]) return NO;
    self.active=NO;
    if (success) self.helperSucceeded=YES;
    else [self fail:error.length ? error : @"Built-in StikJIT did not complete. Restart Cabrillo before another request."];
    return YES;
}
- (void)fail:(NSString *)error {
    if (!self.requestID || self.launchConsumed) return;
    self.active=NO; self.failed=YES; self.helperSucceeded=NO; self.pendingRun=NO;
    self.error=error.length ? error : @"JIT could not be verified. Restart Cabrillo before another request.";
}
- (BOOL)consumeRunWithReadiness:(CJIntegratedJITReadiness)s {
    if (!self.requestID || self.active || self.failed || !self.helperSucceeded ||
        !self.pendingRun || self.launchConsumed || !s.nativePassed || !s.traceKnown ||
        s.traced || !s.debugged || !CJIntegratedJITCanEnterRuntime(s.foreground,s.profileReady,s.profileRestartRequired) ||
        !s.libraryReady || !s.contentReady || s.busy ||
        s.used || !s.selected) return NO;
    self.pendingRun=NO; self.launchConsumed=YES;
    return YES;
}
@end
