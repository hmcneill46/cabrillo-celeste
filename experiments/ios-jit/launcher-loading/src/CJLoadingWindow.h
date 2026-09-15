#import <UIKit/UIKit.h>
NS_ASSUME_NONNULL_BEGIN
@interface CJLoadingWindow : UIWindow
// Touches still reach the native loading screen; SDL retains keyboard/focus.
@property(nonatomic) BOOL preservesGameFocus;
@end
NS_ASSUME_NONNULL_END
