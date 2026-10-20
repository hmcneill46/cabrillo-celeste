#import <Foundation/Foundation.h>
#include <sys/types.h>

NS_ASSUME_NONNULL_BEGIN

// Pairing validation never returns or logs credential contents. Unknown keys are
// preserved so combined RemotePairing/Lockdown files remain usable.
FOUNDATION_EXPORT BOOL CJIntegratedJITValidatePairingData(NSData * _Nullable data, NSError * _Nullable * _Nullable error);

@interface CJIntegratedJITCoordinator : NSObject
- (instancetype)initWithUpdate:(void (^)(NSDictionary *state))update;
@property(nonatomic, readonly) NSDictionary *snapshot;
@property(nonatomic, readonly) BOOL active;
- (nullable NSString *)preflightError;
- (void)prepare;
- (void)resetDDI;
- (BOOL)importPairingURL:(NSURL *)url error:(NSError * _Nullable * _Nullable)error;
- (void)setForceScript:(BOOL)enabled;
- (void)refreshReadiness;
- (void)startForPID:(pid_t)pid
          requestID:(NSString *)requestID
             script:(NSString *)script
     requiresScript:(BOOL)requiresScript
         completion:(void (^)(NSDictionary *result))completion;
@end

NS_ASSUME_NONNULL_END
