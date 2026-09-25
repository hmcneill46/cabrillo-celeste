#import <Foundation/Foundation.h>
NS_ASSUME_NONNULL_BEGIN
// Calls are serialized by the owning logger. Journals and in-memory samples are
// bounded; counters cover every event and allocation records have their own file.
@interface CJEventStore : NSObject
@property(nonatomic,readonly) NSUInteger totalCount;
@property(nonatomic,readonly,nullable) NSString *error;
- (instancetype)initWithURL:(NSURL *)url;
- (BOOL)append:(NSDictionary *)event;
- (NSArray *)snapshot;
- (NSDictionary *)summary;
- (void)sync;
@end
FOUNDATION_EXPORT NSDictionary *CJReadBoundedJournal(NSURL *url);
NS_ASSUME_NONNULL_END
