#import <UIKit/UIKit.h>
NS_ASSUME_NONNULL_BEGIN
@interface CJLoadingWindow : UIWindow
// The passive startup cover absorbs touches while SDL retains keyboard/focus.
@property(nonatomic) BOOL preservesGameFocus;
// Reveal only after a successful callback containing a real draw and readback
// after Present. A successful Start or a skipped-draw callback is insufficient.
- (BOOL)revealGameWindow:(nullable UIWindow *)game
         restoringLevel:(UIWindowLevel)level
         frameSucceeded:(BOOL)frameSucceeded
               graphics:(NSDictionary *)graphics
                loading:(NSDictionary *)loading;
@end
NS_ASSUME_NONNULL_END
