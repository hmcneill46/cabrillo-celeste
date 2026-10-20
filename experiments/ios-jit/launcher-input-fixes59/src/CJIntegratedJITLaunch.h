#import <Foundation/Foundation.h>

typedef struct {
    BOOL nativePassed, traceKnown, traced, debugged, foreground;
    BOOL profileReady, profileRestartRequired, libraryReady, contentReady;
    BOOL busy, used, selected;
} CJIntegratedJITReadiness;
BOOL CJIntegratedJITCanEnterRuntime(BOOL foreground, BOOL profileReady, BOOL profileRestartRequired);

// Acquisition and native execution are independent evidence. This process-local
// reducer never promotes either one into the other and consumes a Run only once.
@interface CJIntegratedJITLaunch : NSObject
@property(nonatomic,copy,readonly) NSString *requestID;
@property(nonatomic,copy,readonly) NSString *error;
@property(nonatomic,readonly) BOOL active;
@property(nonatomic,readonly) BOOL helperSucceeded;
@property(nonatomic,readonly) BOOL pendingRun;
@property(nonatomic,readonly) BOOL failed;
@property(nonatomic,readonly) BOOL launchConsumed;
- (BOOL)beginRequest:(NSString *)requestID run:(BOOL)run;
- (BOOL)requestRun;
- (BOOL)completeRequest:(NSString *)requestID success:(BOOL)success error:(NSString *)error;
- (void)fail:(NSString *)error;
- (BOOL)consumeRunWithReadiness:(CJIntegratedJITReadiness)readiness;
@end
