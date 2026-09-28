#import <Foundation/Foundation.h>
NS_ASSUME_NONNULL_BEGIN
FOUNDATION_EXPORT NSArray<NSString *> *CJVerifiedMods(NSURL *directory, NSDictionary *manifest);
FOUNDATION_EXPORT BOOL CJInstallMod(NSURL *source, NSURL *directory, NSString *name, NSDictionary *expected, NSError **error);
// All callbacks arrive on the main queue. Existing verified ZIPs are retained.
@interface CJModDownloader : NSObject <NSURLSessionDownloadDelegate>
- (instancetype)initWithDirectory:(NSURL *)directory manifest:(NSDictionary *)manifest;
- (void)startWithProgress:(void (^)(NSString *, NSUInteger, NSUInteger, int64_t, int64_t))progress completion:(void (^)(NSError * _Nullable))completion;
- (void)cancel;
@end
NS_ASSUME_NONNULL_END
