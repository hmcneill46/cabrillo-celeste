#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <stdatomic.h>
#import "CJIntegratedJITCoordinator.h"

static NSMutableArray<NSString *> *checks;
static _Atomic int probeCount;
static _Atomic BOOL probeResult;
BOOL CJShortcutProbeLocalTunnel(NSString **error) { atomic_fetch_add(&probeCount,1); if (error) *error=nil; return atomic_load(&probeResult); }

@interface CJIntegratedJITCoordinator (FixtureMethods)
- (NSURL *)pairingURL;
- (void)finish:(NSDictionary *)response;
- (void)watchdogForRequest:(NSString *)requestID after:(NSTimeInterval)seconds;
@end

@interface MemoryPreferences : NSObject
@property(nonatomic,strong) NSMutableDictionary *values;
@end
@implementation MemoryPreferences
- (instancetype)init { self=[super init]; if(self)_values=[NSMutableDictionary dictionary]; return self; }
- (void)setObject:(id)value forKey:(NSString *)key { if(value)self.values[key]=value; else[self.values removeObjectForKey:key]; }
- (void)setBool:(BOOL)value forKey:(NSString *)key { self.values[key]=@(value); }
- (BOOL)boolForKey:(NSString *)key { return [self.values[key] boolValue]; }
- (NSString *)stringForKey:(NSString *)key { id value=self.values[key]; return[value isKindOfClass:NSString.class]?value:nil; }
@end

@interface FixtureCoordinator : CJIntegratedJITCoordinator
@property(nonatomic,strong) NSURL *fixtureRoot;
- (instancetype)initWithRoot:(NSURL *)root;
@end
@implementation FixtureCoordinator
- (instancetype)initWithRoot:(NSURL *)root { _fixtureRoot=root; return [super initWithUpdate:^(__unused NSDictionary *state) { NSCAssert(NSThread.isMainThread,@"Updates must be on the main thread"); }]; }
- (NSURL *)pairingURL { return [[self.fixtureRoot URLByAppendingPathComponent:@"StikJIT"] URLByAppendingPathComponent:@"pairingFile.plist"]; }
@end

static void Check(BOOL condition,NSString *message) {
    if(!condition)@throw[NSException exceptionWithName:@"FixtureFailure" reason:message userInfo:nil];
    [checks addObject:message];
}
static void Write(NSData *data,NSURL *url) {
    NSError *error=nil;
    if(![NSFileManager.defaultManager createDirectoryAtURL:url.URLByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:&error]||![data writeToURL:url options:NSDataWritingAtomic error:&error])
        @throw[NSException exceptionWithName:@"FixtureSetup" reason:@"Could not create a synthetic fixture" userInfo:nil];
}
static NSData *Pairing(unsigned char seed) {
    unsigned char bytes[32];for(NSUInteger i=0;i<sizeof(bytes);i++)bytes[i]=seed+(unsigned char)i;
    return [NSPropertyListSerialization dataWithPropertyList:@{@"public_key":[NSData dataWithBytes:bytes length:32],@"private_key":[NSData dataWithBytes:bytes length:32],@"identifier":@"synthetic-fixture",@"HostCertificate":[NSData dataWithBytes:bytes length:16],@"futureExtra":@{ @"preserved":@YES }} format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];
}
static void Spin(BOOL(^done)(void)) {
    NSDate *deadline=[NSDate dateWithTimeIntervalSinceNow:3];
    while(!done()&&deadline.timeIntervalSinceNow>0)[NSRunLoop.currentRunLoop runUntilDate:[NSDate dateWithTimeIntervalSinceNow:0.005]];
    Check(done(),@"Asynchronous operation completed within fixture deadline");
}
static void Arm(FixtureCoordinator *coordinator,NSString *operation,NSString *request,void(^completion)(NSDictionary *)) {
    [coordinator setValue:@YES forKey:@"active"];[coordinator setValue:operation forKey:@"operation"];
    [coordinator setValue:@NO forKey:@"timedOut"];
    [coordinator setValue:request forKey:@"operationID"];[coordinator setValue:NSUUID.UUID.UUIDString forKey:@"progressToken"];
    [coordinator setValue:[NSObject new] forKey:@"extension"];[coordinator setValue:[completion copy] forKey:@"completion"];
}

int main(int argc,char *argv[]) {
    @autoreleasepool {
        if(argc!=2)return 2;
        NSURL *work=[NSURL fileURLWithPath:@(argv[1]) isDirectory:YES];
        checks=[NSMutableArray array];MemoryPreferences *preferences=[MemoryPreferences new];
        Method method=class_getClassMethod(NSUserDefaults.class,@selector(standardUserDefaults));
        IMP original=method_getImplementation(method);
        IMP replacement=imp_implementationWithBlock(^id{ return preferences; });method_setImplementation(method,replacement);
        @try {
            NSData *first=Pairing(1),*second=Pairing(2),*manual=Pairing(3),*later=Pairing(4);
            NSError *error=nil;
            Check(CJIntegratedJITValidatePairingData(first,&error)&&error==nil,@"Combined RemotePairing and Lockdown dictionary accepted");
            Check(!CJIntegratedJITValidatePairingData([NSData data],&error),@"Empty pairing data rejected");
            Check(!CJIntegratedJITValidatePairingData([NSMutableData dataWithLength:1024*1024+1],&error),@"Oversized pairing data rejected");
            for(id bad in @[@[],@{@"identifier":@"synthetic"},@{@"identifier":@1,@"public_key":[NSMutableData dataWithLength:32],@"private_key":[NSMutableData dataWithLength:32]},@{@"identifier":@"synthetic",@"public_key":[NSMutableData dataWithLength:31],@"private_key":[NSMutableData dataWithLength:32]}]) {
                NSData *data=[NSPropertyListSerialization dataWithPropertyList:bad format:NSPropertyListXMLFormat_v1_0 options:0 error:NULL];
                Check(!CJIntegratedJITValidatePairingData(data,&error),@"Malformed required pairing field rejected");
            }
            NSURL *root=[work URLByAppendingPathComponent:@"adoption" isDirectory:YES],*tool=[root URLByAppendingPathComponent:@"pairingFile.plist"];
            Write(first,tool);FixtureCoordinator *coordinator=[[FixtureCoordinator alloc]initWithRoot:root];
            Check([[NSData dataWithContentsOfURL:coordinator.pairingURL]isEqual:first],@"First tool-placed root pairing adopted exactly");
            Check([[NSData dataWithContentsOfURL:tool]isEqual:first],@"Tool original retained after adoption");
            Check([coordinator.snapshot[@"pairingImported"]boolValue],@"Imported status reflects validated canonical file");
            NSNumber *excluded=nil;[tool getResourceValue:&excluded forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check(excluded.boolValue,@"Tool-placed credential excluded from backups");
            [coordinator.pairingURL getResourceValue:&excluded forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check(excluded.boolValue,@"Canonical credential excluded from backups");
            [coordinator setValue:@YES forKey:@"ddiReady"];[coordinator setValue:@YES forKey:@"serviceChecked"];
            Write(second,tool);atomic_store(&probeResult,NO);[coordinator refreshReadiness];
            Check([[NSData dataWithContentsOfURL:coordinator.pairingURL]isEqual:second],@"Changed root pairing replaces existing canonical file");
            Check(![coordinator.snapshot[@"ddiReady"]boolValue],@"New tool pairing invalidates prepared DDI readiness");
            Spin(^BOOL{return[coordinator.snapshot[@"serviceChecked"]boolValue];});
            NSURL *manualFile=[work URLByAppendingPathComponent:@"manual.plist"];Write(manual,manualFile);
            NSNumber *outsideBackupBefore=nil;[manualFile getResourceValue:&outsideBackupBefore forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check([coordinator importPairingURL:manualFile error:&error],@"Manual pairing import succeeds");
            [manualFile removeCachedResourceValueForKey:NSURLIsExcludedFromBackupKey];
            NSNumber *outsideBackupAfter=nil;[manualFile getResourceValue:&outsideBackupAfter forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check(outsideBackupBefore.boolValue==outsideBackupAfter.boolValue,@"Manual import does not change an external original’s backup attributes");
            NSURL *inboxCopy=[[root URLByAppendingPathComponent:@"Inbox"]URLByAppendingPathComponent:@"imported-pairing.plist"];
            Write(manual,inboxCopy);[inboxCopy setResourceValue:@NO forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check([coordinator importPairingURL:inboxCopy error:&error],@"App-owned picker Inbox credential imports successfully");
            [inboxCopy removeCachedResourceValueForKey:NSURLIsExcludedFromBackupKey];
            NSNumber *copyExcluded=nil;[inboxCopy getResourceValue:&copyExcluded forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check(copyExcluded.boolValue&&[[NSData dataWithContentsOfURL:inboxCopy]isEqual:manual],@"App-owned picker credential copy is excluded from backup without deletion or byte changes");
            NSURL *linkedCopy=[[root URLByAppendingPathComponent:@"Inbox"]URLByAppendingPathComponent:@"external-link.plist"];
            if(![NSFileManager.defaultManager createSymbolicLinkAtURL:linkedCopy withDestinationURL:manualFile error:&error])@throw[NSException exceptionWithName:@"FixtureSetup" reason:@"Could not create synthetic Inbox link" userInfo:nil];
            (void)[coordinator importPairingURL:linkedCopy error:&error];
            [manualFile removeCachedResourceValueForKey:NSURLIsExcludedFromBackupKey];
            [manualFile getResourceValue:&outsideBackupAfter forKey:NSURLIsExcludedFromBackupKey error:NULL];
            Check(outsideBackupBefore.boolValue==outsideBackupAfter.boolValue&&[[NSData dataWithContentsOfURL:manualFile]isEqual:manual],@"Resolving an Inbox link outside Documents never changes or deletes the external original");
            [coordinator refreshReadiness];
            Check([[NSData dataWithContentsOfURL:coordinator.pairingURL]isEqual:manual],@"Unchanged older tool file cannot overwrite a manual import");
            Check([[NSData dataWithContentsOfURL:manualFile]isEqual:manual]&&[[NSData dataWithContentsOfURL:tool]isEqual:second],@"Manual import preserves both user originals");
            Write(later,tool);[NSFileManager.defaultManager setAttributes:@{NSFileModificationDate:[NSDate dateWithTimeIntervalSince1970:1]}ofItemAtPath:tool.path error:NULL];
            [coordinator refreshReadiness];
            Check([[NSData dataWithContentsOfURL:coordinator.pairingURL]isEqual:later],@"Changed tool bytes detected even when source timestamp is preserved or older");
            Write([@"invalid synthetic plist" dataUsingEncoding:NSUTF8StringEncoding],tool);
            [coordinator refreshReadiness];
            Check([[NSData dataWithContentsOfURL:coordinator.pairingURL]isEqual:later],@"Invalid tool replacement cannot damage the last valid pairing");
            [coordinator setValue:@YES forKey:@"active"];
            Check(![coordinator importPairingURL:manualFile error:&error]&&[[NSData dataWithContentsOfURL:coordinator.pairingURL]isEqual:later],@"Active operation prevents credential replacement");
            [coordinator setValue:@NO forKey:@"active"];
            atomic_store(&probeResult,YES);[coordinator refreshReadiness];
            Spin(^BOOL{return[coordinator.snapshot[@"serviceChecked"]boolValue]&&[coordinator.snapshot[@"serviceReady"]boolValue];});
            Check(atomic_load(&probeCount)>0,@"Refresh invokes the production RemotePairing service-probe boundary");
            [coordinator setValue:@(NSProcessInfo.processInfo.systemUptime-46)forKey:@"serviceCheckedAt"];
            Check(![coordinator.snapshot[@"serviceReady"]boolValue]&&![coordinator.snapshot[@"serviceFresh"]boolValue],@"Service result expires after45 seconds");
            NSURL *olderRoot=[work URLByAppendingPathComponent:@"older-root" isDirectory:YES];
            NSURL *olderTool=[olderRoot URLByAppendingPathComponent:@"pairingFile.plist"];
            NSURL *existing=[[olderRoot URLByAppendingPathComponent:@"StikJIT"]URLByAppendingPathComponent:@"pairingFile.plist"];
            Write(manual,existing);Write(first,olderTool);
            [NSFileManager.defaultManager setAttributes:@{NSFileModificationDate:[NSDate dateWithTimeIntervalSince1970:1]}ofItemAtPath:olderTool.path error:NULL];
            [preferences.values removeObjectForKey:@"launcher.integratedJIT.observedToolPairingDigest"];
            FixtureCoordinator *older=[[FixtureCoordinator alloc]initWithRoot:olderRoot];
            Check([[NSData dataWithContentsOfURL:older.pairingURL]isEqual:manual],@"First observation preserves a newer preexisting manual canonical file");
            Check([[NSData dataWithContentsOfURL:olderTool]isEqual:first],@"Older tool original remains present after first-observation comparison");
            for(NSString *operation in @[@"enable",@"prepare",@"reset"]) {
                NSString *expected=@{@"enable":@"enabled",@"prepare":@"ready",@"reset":@"reset"}[operation];
                for(NSDictionary *response in @[@{@"success":@YES},@{@"schema":@1,@"success":@YES,@"code":@"unknown"},@{@"schema":@1,@"success":@YES,@"code":[expected isEqual:@"ready"]?@"enabled":@"ready"},@{@"schema":@1,@"success":@2,@"code":expected},@{@"schema":@2,@"success":@YES,@"code":expected}]) {
                    __block NSDictionary *returned=nil;Arm(coordinator,operation,NSUUID.UUID.UUIDString,^(NSDictionary *value){returned=value;});
                    [coordinator finish:response];
                    Check(returned&&![returned[@"success"]boolValue]&&!coordinator.active,@"Malformed or wrong-operation success response fails closed");
                }
                __block NSDictionary *returned=nil;NSString *request=NSUUID.UUID.UUIDString;
                Arm(coordinator,operation,request,^(NSDictionary *value){returned=value;});
                [coordinator finish:@{@"schema":@1,@"success":@YES,@"code":expected,@"txmPresent":@YES}];
                Check([returned[@"success"]boolValue]&&[returned[@"requestID"]isEqual:request]&&!coordinator.active,@"Correct operation-specific helper response accepted exactly once");
            }
            __block NSUInteger completions=0;__block NSDictionary *last=nil;NSString *request=NSUUID.UUID.UUIDString;
            Arm(coordinator,@"enable",request,^(NSDictionary *value){completions++;last=value;});
            [coordinator watchdogForRequest:request after:0.01];
            Spin(^BOOL{return[coordinator.snapshot[@"helperTimedOut"]boolValue];});
            Check(completions==1&&![last[@"success"]boolValue]&&coordinator.active&&[coordinator valueForKey:@"extension"]!=nil,@"Timeout fails once while retaining active possibly attached helper");
            [coordinator finish:@{@"schema":@1,@"success":@YES,@"code":@"enabled"}];
            Check(completions==1&&!coordinator.active&&[coordinator.snapshot[@"phase"]isEqual:@"failed"]&&![coordinator.snapshot[@"ddiReady"]boolValue],@"Late helper success releases connection without overriding timeout or launching");
            __block NSUInteger freshCompletions=0;
            Arm(coordinator,@"enable",request,^(NSDictionary *value){freshCompletions++;last=value;});
            [coordinator watchdogForRequest:request after:0.01];
            Arm(coordinator,@"enable",request,^(NSDictionary *value){freshCompletions++;last=value;});
            __block BOOL elapsed=NO;dispatch_after(dispatch_time(DISPATCH_TIME_NOW,30*NSEC_PER_MSEC),dispatch_get_main_queue(),^{elapsed=YES;});
            Spin(^BOOL{return elapsed;});
            Check(coordinator.active&&freshCompletions==0&&![coordinator.snapshot[@"helperTimedOut"]boolValue],@"Old watchdog cannot time out a different operation nonce even if request ID repeats");
            [coordinator setValue:nil forKey:@"txm"];
            [coordinator finish:@{@"schema":@1,@"success":@YES,@"code":@"enabled",@"txmPresent":@2}];
            Check(freshCompletions==1&&coordinator.snapshot[@"needsTXM"]==NSNull.null,@"Nonboolean TXM response cannot become a confirmed security state");
            __block NSDictionary *redacted=nil;Arm(coordinator,@"enable",NSUUID.UUID.UUIDString,^(NSDictionary *value){redacted=value;});
            [coordinator finish:@{@"schema":@1,@"success":@NO,@"code":@"untrusted-private-marker"}];
            Check(![redacted[@"code"]containsString:@"untrusted"]&&![redacted[@"error"]containsString:@"untrusted"],@"Unknown helper error text is replaced with a redacted fixed diagnostic");
            NSDictionary *report=@{@"status":@"PASS_INTEGRATED_JIT_COORDINATOR_CONTROLS",@"checks":checks,@"actualHelperLaunched":@NO,@"actualNetworkProbeExecuted":@NO,@"probeBoundaryStubbed":@YES,@"privateCredentialsUsed":@NO,@"gameOrJITExecuted":@NO,@"physicalDeviceTested":@NO};
            NSData *data=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:NULL];
            if(![data writeToURL:[work URLByAppendingPathComponent:@"results.json"]atomically:YES])@throw[NSException exceptionWithName:@"FixtureOutput" reason:@"Could not save results" userInfo:nil];
            printf("PASS_INTEGRATED_JIT_COORDINATOR_CONTROLS %lu\n",(unsigned long)checks.count);
        } @catch(NSException *exception) { fprintf(stderr,"FAIL coordinator fixture: %s\n",exception.reason.UTF8String);return 1; }
        @finally { method_setImplementation(method,original);imp_removeBlock(replacement); }
    }
    return 0;
}
