#import "CJLoadingWindow.h"
@implementation CJLoadingWindow
- (BOOL)canBecomeKeyWindow { return !self.preservesGameFocus && [super canBecomeKeyWindow]; }
- (UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event {
    if(self.preservesGameFocus && !self.hidden && self.alpha>0.01 && self.userInteractionEnabled && [self pointInside:point withEvent:event])return self;
    return [super hitTest:point withEvent:event];
}
- (BOOL)revealGameWindow:(UIWindow *)game restoringLevel:(UIWindowLevel)level frameSucceeded:(BOOL)frameSucceeded graphics:(NSDictionary *)graphics loading:(NSDictionary *)loading {
    if(!NSThread.isMainThread || UIApplication.sharedApplication.applicationState!=UIApplicationStateActive ||
       !game || game==self || !game.windowScene || game.windowScene!=self.windowScene || !game.rootViewController ||
       !frameSucceeded || ![loading[@"active"] boolValue] || [loading[@"failed"] boolValue] ||
       ![graphics[@"metal_layer"] boolValue] || ![graphics[@"gpu_readback_passed"] boolValue] ||
       ![graphics[@"first_frame_drawn"] boolValue] || ![graphics[@"first_frame_readback_passed"] boolValue] ||
       [graphics[@"failed_checks"] unsignedIntegerValue]!=0)return NO;
    self.preservesGameFocus=NO;
    self.windowLevel=level;
    self.hidden=YES;
    [game makeKeyAndVisible];
    return YES;
}
@end
