
#import <UIKit/UIKit.h>
#import "CJIntegratedJITCoordinator.h"
@interface FixtureCoordinator : CJIntegratedJITCoordinator @end
@implementation FixtureCoordinator
- (NSString *)preflightError { return nil; }
@end
@interface FixtureDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic,strong) UIWindow *window;
@property(nonatomic,strong) FixtureCoordinator *coordinator;
@property(nonatomic,strong) NSMutableArray *events;
@end
@implementation FixtureDelegate
- (void)write:(NSString *)status state:(NSDictionary *)state {
 NSDictionary *result=@{@"status":status,@"host_pid":@(getpid()),@"state":state?:@{},@"events":self.events?:@[],@"jit_attempted":@NO};
 NSURL *doc=[NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
 [[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingPrettyPrinted error:NULL] writeToURL:[doc URLByAppendingPathComponent:@"ipc-result.json"] atomically:YES];
 NSLog(@"FIXTURE_IPC %@ %@",status,state?:@{});
}
- (BOOL)application:(UIApplication *)app didFinishLaunchingWithOptions:(NSDictionary *)options {
 (void)app;(void)options;
 self.window=[[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];self.window.rootViewController=[UIViewController new];[self.window makeKeyAndVisible];
 self.events=[NSMutableArray array];__weak FixtureDelegate *weak=self;
 self.coordinator=[[FixtureCoordinator alloc] initWithUpdate:^(NSDictionary *state){
  FixtureDelegate *s=weak;if(!s)return;[s.events addObject:state];
  NSString *phase=state[@"phase"];
  [s write:[phase isEqual:@"ready"]?@"PASS_AUTHORITATIVE_PREPARE_RESPONSE":[phase isEqual:@"failed"]?@"FAIL_EXTENSION_PATH":@"RUNNING" state:state];
 }];
 NSURL *doc=[NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
 NSURL *synthetic=[doc URLByAppendingPathComponent:@"synthetic.plist"];
 NSDictionary *pair=@{@"public_key":[NSData dataWithBytes:(uint8_t[32]){1} length:32],@"private_key":[NSData dataWithBytes:(uint8_t[32]){2} length:32],@"identifier":@"SYNTHETIC-SIMULATOR-ONLY"};
 [[NSPropertyListSerialization dataWithPropertyList:pair format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL] writeToURL:synthetic atomically:YES];
 NSError *error=nil;BOOL imported=[self.coordinator importPairingURL:synthetic error:&error];
 [self write:imported?@"STARTING":@"FAIL_SYNTHETIC_PAIRING" state:self.coordinator.snapshot];
 if(imported)dispatch_after(dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC),dispatch_get_main_queue(),^{[self.coordinator prepare];});
 return YES;
}
@end
int main(int argc,char **argv){@autoreleasepool{return UIApplicationMain(argc,argv,nil,NSStringFromClass(FixtureDelegate.class));}}
