#import "CJLoadingWindow.h"
@implementation CJLoadingWindow
- (BOOL)canBecomeKeyWindow { return !self.preservesGameFocus && [super canBecomeKeyWindow]; }
@end
