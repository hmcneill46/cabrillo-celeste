#import "CJIntegratedJITCoordinator.h"
#import "CJShortcutPlatform.h"
#import <Security/Security.h>
#import <TargetConditionals.h>
#import <CommonCrypto/CommonDigest.h>
#include <dlfcn.h>
#include <notify.h>
#include <objc/message.h>
#include <unistd.h>

static const NSUInteger CJPairingLimit = 1024 * 1024;
static NSString *const CJRequestKey = @"org.cabrillo.integrated-jit.request.v1";
static NSString *const CJResponseKey = @"org.cabrillo.integrated-jit.response.v1";
static NSString *const CJForceKey = @"launcher.integratedJIT.forceScript";
static NSString *const CJToolPairingKey = @"launcher.integratedJIT.observedToolPairingDigest";

static NSError *CJIntegratedError(NSInteger code, NSString *message) {
    return [NSError errorWithDomain:@"CJIntegratedJIT" code:code userInfo:@{NSLocalizedDescriptionKey:message}];
}

BOOL CJIntegratedJITValidatePairingData(NSData *data, NSError **error) {
    if (error) *error = nil;
    if (![data isKindOfClass:NSData.class] || data.length == 0 || data.length > CJPairingLimit) {
        if (error) *error = CJIntegratedError(1, @"Choose a pairing plist smaller than 1 MiB.");
        return NO;
    }
    id object = [NSPropertyListSerialization propertyListWithData:data options:NSPropertyListImmutable format:NULL error:NULL];
    NSDictionary *row = [object isKindOfClass:NSDictionary.class] ? object : nil;
    NSData *publicKey = row[@"public_key"], *privateKey = row[@"private_key"];
    NSString *identifier = row[@"identifier"];
    BOOL valid = [publicKey isKindOfClass:NSData.class] && publicKey.length == 32 &&
        [privateKey isKindOfClass:NSData.class] && privateKey.length == 32 &&
        [identifier isKindOfClass:NSString.class] && identifier.length > 0 && identifier.length <= 4096;
    if (!valid && error) *error = CJIntegratedError(2, @"This is not a Remote Pairing plist. Import the pairing file exported for this device by iLoader or another compatible tool.");
    return valid;
}

static BOOL CJHasDebugEntitlement(void) {
    typedef CFTypeRef (*Create)(CFAllocatorRef);
    typedef CFTypeRef (*Copy)(CFTypeRef, CFStringRef, CFErrorRef *);
    Create create = (Create)dlsym(RTLD_DEFAULT, "SecTaskCreateFromSelf");
    Copy copy = (Copy)dlsym(RTLD_DEFAULT, "SecTaskCopyValueForEntitlement");
    if (!create || !copy) return NO;
    CFTypeRef task = create(kCFAllocatorDefault);
    if (!task) return NO;
    CFTypeRef value = copy(task, CFSTR("get-task-allow"), NULL);
    BOOL result = value == kCFBooleanTrue;
    if (value) CFRelease(value);
    CFRelease(task);
    return result;
}

@interface CJIntegratedJITCoordinator ()
@property(nonatomic, copy) void (^update)(NSDictionary *);
@property(nonatomic, readwrite) BOOL active;
@property(nonatomic, copy) NSString *phase;
@property(nonatomic, copy) NSString *message;
@property(nonatomic) BOOL ddiReady;
@property(nonatomic) BOOL serviceReady;
@property(nonatomic) BOOL serviceChecked;
@property(nonatomic) NSTimeInterval serviceCheckedAt;
@property(nonatomic) NSUInteger generation;
@property(nonatomic, strong) NSNumber *txm;
@property(nonatomic, strong) id extension;
@property(nonatomic, strong) NSUUID *extensionRequest;
@property(nonatomic, copy) NSString *operationID;
@property(nonatomic, copy) NSString *operation;
@property(nonatomic, copy) NSString *progressToken;
@property(nonatomic, strong) NSMutableArray<NSNumber *> *notificationTokens;
@property(nonatomic, copy) void (^completion)(NSDictionary *);
@property(nonatomic) BOOL timedOut;
@end

@implementation CJIntegratedJITCoordinator

- (instancetype)initWithUpdate:(void (^)(NSDictionary *))update {
    self = [super init];
    if (self) {
        _update = [update copy]; _phase = @"idle"; _message = @"Import a pairing file, then check the LocalDevVPN service or prepare JIT.";
        _notificationTokens = [NSMutableArray array];
        [self adoptPairingIfNeeded];
    }
    return self;
}

- (NSURL *)pairingURL {
    NSURL *documents = [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
    return [[documents URLByAppendingPathComponent:@"StikJIT" isDirectory:YES] URLByAppendingPathComponent:@"pairingFile.plist"];
}

- (NSData *)pairingData {
    return [self readPairingFile:self.pairingURL];
}

- (NSData *)readPairingFile:(NSURL *)url {
    NSNumber *regular = nil, *size = nil, *symlink = nil;
    if (![url getResourceValue:&regular forKey:NSURLIsRegularFileKey error:NULL] || !regular.boolValue ||
        ![url getResourceValue:&symlink forKey:NSURLIsSymbolicLinkKey error:NULL] || symlink.boolValue ||
        ![url getResourceValue:&size forKey:NSURLFileSizeKey error:NULL] || size.unsignedLongLongValue > CJPairingLimit) return nil;
    NSData *data = [NSData dataWithContentsOfURL:url options:NSDataReadingMappedIfSafe error:NULL];
    return CJIntegratedJITValidatePairingData(data, NULL) ? data : nil;
}

- (NSURL *)toolPairingURL { return [self.pairingURL.URLByDeletingLastPathComponent.URLByDeletingLastPathComponent URLByAppendingPathComponent:@"pairingFile.plist"]; }

- (NSString *)pairingDigest:(NSData *)data {
    if (!data) return nil;
    unsigned char bytes[CC_SHA256_DIGEST_LENGTH]; CC_SHA256(data.bytes,(CC_LONG)data.length,bytes);
    NSMutableString *digest = [NSMutableString stringWithCapacity:64];
    for (NSUInteger i=0;i<sizeof(bytes);i++) [digest appendFormat:@"%02x",bytes[i]];
    return digest;
}

- (void)adoptPairingIfNeeded {
    if (self.active) return;
    NSURL *root = self.toolPairingURL;
    if ([NSFileManager.defaultManager fileExistsAtPath:root.path]) [root setResourceValue:@YES forKey:NSURLIsExcludedFromBackupKey error:NULL];
    [self.pairingURL setResourceValue:@YES forKey:NSURLIsExcludedFromBackupKey error:NULL];
    NSData *incoming = [self readPairingFile:root], *current = self.pairingData;
    if (!incoming) return;
    NSString *digest = [self pairingDigest:incoming];
    NSString *observed = [NSUserDefaults.standardUserDefaults stringForKey:CJToolPairingKey];
    if (current && ([incoming isEqual:current] || [observed isEqual:digest])) {
        [NSUserDefaults.standardUserDefaults setObject:digest forKey:CJToolPairingKey]; return;
    }
    if (current && !observed) {
        NSDate *rootDate = nil, *currentDate = nil;
        [root getResourceValue:&rootDate forKey:NSURLContentModificationDateKey error:NULL];
        [self.pairingURL getResourceValue:&currentDate forKey:NSURLContentModificationDateKey error:NULL];
        if (rootDate && currentDate && [rootDate compare:currentDate] != NSOrderedDescending) {
            [NSUserDefaults.standardUserDefaults setObject:digest forKey:CJToolPairingKey]; return;
        }
    }
    [self importPairingURL:root error:NULL];
}

- (void)excludeOwnedPickerCopyFromBackup:(NSURL *)url {
    // Import-mode document pickers can leave an app-owned Inbox copy. Exclude
    // that copy without changing an external provider's original or following
    // an Inbox symlink out of this app's Documents directory.
    NSURL *documents = self.pairingURL.URLByDeletingLastPathComponent.URLByDeletingLastPathComponent.URLByResolvingSymlinksInPath.URLByStandardizingPath;
    NSURL *inbox = [documents URLByAppendingPathComponent:@"Inbox" isDirectory:YES].URLByResolvingSymlinksInPath.URLByStandardizingPath;
    NSURL *source = url.URLByResolvingSymlinksInPath.URLByStandardizingPath;
    NSString *documentPrefix = [documents.path stringByAppendingString:@"/"];
    NSString *inboxPrefix = [inbox.path stringByAppendingString:@"/"];
    if (url.isFileURL && [inbox.path hasPrefix:documentPrefix] && [source.path hasPrefix:inboxPrefix])
        [source setResourceValue:@YES forKey:NSURLIsExcludedFromBackupKey error:NULL];
}

- (BOOL)importPairingURL:(NSURL *)url error:(NSError **)error {
    if (error) *error = nil;
    if (self.active) { if (error) *error = CJIntegratedError(3, @"Wait for the current JIT operation before replacing its pairing file."); return NO; }
    BOOL scoped = [url startAccessingSecurityScopedResource];
    NSData *data = nil;
    @try {
        NSNumber *regular = nil, *size = nil;
        if (url.isFileURL && [url getResourceValue:&regular forKey:NSURLIsRegularFileKey error:NULL] && regular.boolValue &&
            [url getResourceValue:&size forKey:NSURLFileSizeKey error:NULL] && size.unsignedLongLongValue <= CJPairingLimit)
            data = [NSData dataWithContentsOfURL:url options:0 error:NULL];
    } @finally { if (scoped) [url stopAccessingSecurityScopedResource]; }
    [self excludeOwnedPickerCopyFromBackup:url];
    if (!CJIntegratedJITValidatePairingData(data, error)) return NO;
    NSURL *destination = self.pairingURL;
    NSError *failure = nil;
    BOOL made = [NSFileManager.defaultManager createDirectoryAtURL:destination.URLByDeletingLastPathComponent withIntermediateDirectories:YES attributes:@{NSFileProtectionKey:NSFileProtectionCompleteUntilFirstUserAuthentication} error:&failure];
    BOOL saved = made && [data writeToURL:destination options:NSDataWritingAtomic | NSDataWritingFileProtectionCompleteUntilFirstUserAuthentication error:&failure];
    if (!saved) { if (error) *error = CJIntegratedError(4, @"Cabrillo could not store the pairing file. Check available storage and try again."); return NO; }
    [destination setResourceValue:@YES forKey:NSURLIsExcludedFromBackupKey error:NULL];
    NSData *toolData = [self readPairingFile:self.toolPairingURL];
    if (toolData) [NSUserDefaults.standardUserDefaults setObject:[self pairingDigest:toolData] forKey:CJToolPairingKey];
    [self.toolPairingURL setResourceValue:@YES forKey:NSURLIsExcludedFromBackupKey error:NULL];
    self.ddiReady = NO; self.serviceReady = NO; self.serviceChecked = NO; self.txm = nil; self.generation++;
    self.phase = @"imported"; self.message = @"Pairing file imported. Connect LocalDevVPN, then prepare JIT.";
    [self publish]; return YES;
}

- (NSString *)helperIdentifier {
    NSURL *directory = [NSBundle.mainBundle.builtInPlugInsURL URLByAppendingPathComponent:@"CabrilloJITHelper.appex" isDirectory:YES];
    NSBundle *bundle = directory ? [NSBundle bundleWithURL:directory] : nil;
    NSString *identifier = bundle.bundleIdentifier;
    return identifier.length ? identifier : nil;
}

- (NSString *)availabilityError {
#if TARGET_OS_SIMULATOR
    return @"Built-in StikJIT requires a physical device.";
#else
    if (@available(iOS 17.4, *)) {} else return @"Built-in StikJIT requires iOS 17.4 or later. Choose another JIT method.";
    if (getenv("LC_HOME_PATH") != NULL) return @"Built-in StikJIT cannot launch its helper inside LiveContainer. Choose an existing JIT provider.";
    if (!self.helperIdentifier) return @"The JIT helper is missing. Reinstall while keeping app extensions, or choose another JIT method.";
    return nil;
#endif
}

- (NSString *)preflightError {
    NSString *availability = [self availabilityError];
    if (availability) return availability;
    if (!CJHasDebugEntitlement()) return @"This installation needs get-task-allow. Sign Cabrillo with a Development profile that retains debugging permission.";
    [self adoptPairingIfNeeded];
    if (!self.pairingData) return @"Import a Remote Pairing file for this device. iLoader can place pairingFile.plist in Cabrillo’s Documents folder.";
    return nil;
}

- (NSDictionary *)snapshot {
    NSTimeInterval age = self.serviceChecked ? MAX(0, NSProcessInfo.processInfo.systemUptime - self.serviceCheckedAt) : 0;
    BOOL fresh = self.serviceChecked && age <= 45;
    NSMutableDictionary *state = [@{@"phase":self.phase ?: @"idle", @"message":self.message ?: @"", @"active":@(self.active),
        @"pairingImported":@(self.pairingData != nil), @"ddiReady":@(self.ddiReady), @"serviceReady":@(self.serviceReady && fresh), @"serviceFresh":@(fresh),
        @"serviceChecked":@(self.serviceChecked), @"helperTimedOut":@(self.timedOut), @"forceScript":@([NSUserDefaults.standardUserDefaults boolForKey:CJForceKey]),
        @"needsTXM":self.txm ?: NSNull.null, @"tunnelAddress":@"10.7.0.1", @"tunnelPort":@49152} mutableCopy];
    if (self.serviceChecked) state[@"serviceCheckAgeSeconds"] = @(age);
    return state;
}

- (void)scheduleServiceExpiry {
    NSUInteger generation = self.generation;
    __weak typeof(self) weakSelf = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,46*NSEC_PER_SEC),dispatch_get_main_queue(),^{
        typeof(self) self = weakSelf;
        if (self && self.serviceChecked && self.generation == generation) [self publish];
    });
}

- (void)publish {
    if (!self.update) return;
    NSDictionary *state = self.snapshot;
    void (^callback)(NSDictionary *) = self.update;
    if (NSThread.isMainThread) callback(state); else dispatch_async(dispatch_get_main_queue(), ^{ callback(state); });
}

- (void)setForceScript:(BOOL)enabled {
    if (self.active) return;
    [NSUserDefaults.standardUserDefaults setBool:enabled forKey:CJForceKey]; [self publish];
}

- (void)refreshReadiness {
    if (self.active) return;
    [self adoptPairingIfNeeded];
    NSUInteger generation = ++self.generation;
    self.phase = @"checking"; self.message = @"Checking LocalDevVPN’s Remote Pairing service…"; [self publish];
    __weak typeof(self) weakSelf = self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        BOOL ready = CJShortcutProbeLocalTunnel(NULL);
        dispatch_async(dispatch_get_main_queue(), ^{
            typeof(self) self = weakSelf;
            if (!self || self.generation != generation || self.active) return;
            self.serviceChecked = YES; self.serviceReady = ready; self.serviceCheckedAt = NSProcessInfo.processInfo.systemUptime;
            [self scheduleServiceExpiry];
            self.phase = ready ? @"idle" : @"failed";
            self.message = ready ? @"LocalDevVPN’s Remote Pairing service replied. Prepare JIT to check pairing and the Developer Disk Image." : @"The Remote Pairing service did not reply. Connect LocalDevVPN and check the network setup.";
            [self publish];
        });
    });
}

- (void)prepare { [self begin:@"prepare" pid:0 requestID:NSUUID.UUID.UUIDString script:@"" requiresScript:NO completion:nil]; }
- (void)resetDDI { [self begin:@"reset" pid:0 requestID:NSUUID.UUID.UUIDString script:@"" requiresScript:NO completion:nil]; }

- (void)startForPID:(pid_t)pid requestID:(NSString *)requestID script:(NSString *)script requiresScript:(BOOL)requiresScript completion:(void (^)(NSDictionary *))completion {
    [self begin:@"enable" pid:pid requestID:requestID script:script requiresScript:requiresScript completion:completion];
}

- (void)stopNotifications {
    for (NSNumber *token in self.notificationTokens) notify_cancel(token.intValue);
    [self.notificationTokens removeAllObjects];
}

- (void)watchdogForRequest:(NSString *)requestID after:(NSTimeInterval)seconds {
    NSString *progressToken = [self.progressToken copy];
    __weak typeof(self) weakSelf = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(seconds*NSEC_PER_SEC)),dispatch_get_main_queue(),^{
        typeof(self) self = weakSelf;
        if (!self.active || self.timedOut || ![self.operationID isEqual:requestID] || ![self.progressToken isEqual:progressToken]) return;
        self.timedOut = YES; self.phase = @"failed";
        self.message = @"The JIT helper has not completed. Its connection is retained; reopen Cabrillo before retrying.";
        void (^callback)(NSDictionary *) = self.completion; self.completion = nil;
        [self publish];
        if (callback) callback(@{@"success":@NO,@"error":self.message,@"code":@"timeout",@"requestID":requestID});
        // Keep the possibly attached helper alive until its genuine terminal
        // callback. Timing out never proves detach and never cancels the helper.
    });
}

- (void)finish:(NSDictionary *)response {
    if (!self.active) return;
    NSString *requestID = self.operationID;
    NSString *code = [response[@"code"] isKindOfClass:NSString.class] ? response[@"code"] : @"helper-response";
    NSString *expected = @{@"enable":@"enabled",@"prepare":@"ready",@"reset":@"reset"}[self.operation ?: @""];
    BOOL reportedSuccess = [response[@"success"] isEqual:@YES];
    BOOL success = !self.timedOut && reportedSuccess && [response[@"schema"] isEqual:@1] && [code isEqual:expected];
    if (reportedSuccess && !success) code = @"helper-response";
    if (!success && [@[@"enabled",@"ready",@"reset"] containsObject:code]) code = @"helper-response";
    if (self.timedOut) code = @"timeout";
    NSDictionary *messages = @{@"ready":@"Developer Disk Image prepared. Enable JIT when you are ready to play.",
        @"enabled":@"The built-in helper finished. Cabrillo is checking native JIT and debugger detach.", @"reset":@"Developer Disk Image cache reset.",
        @"unreachable":@"The Remote Pairing service is unreachable. Reconnect LocalDevVPN and try again.",
        @"pairing":@"The pairing file was rejected. Import a fresh pairing file for this device.",
        @"ddi-download":@"The Developer Disk Image download failed. Check the connection and try again.",
        @"ddi-mount":@"The Developer Disk Image could not be mounted. Restart the device or reset its cached image.",
        @"pairing-connection":@"The device connection or pairing was rejected. Reconnect LocalDevVPN and import a fresh pairing file if needed.",
        @"preparation":@"Device preparation failed. Check Developer Mode, pairing and LocalDevVPN; reset the Developer Disk Image if its cache is stale.",
        @"debugger":@"The debugger connection failed. Check Developer Mode and pairing, then reopen Cabrillo before retrying.",
        @"txm":@"TXM status could not be determined. Enable Force JIT Script and reopen Cabrillo before retrying.",
        @"storage":@"The helper could not use its local files. Check free storage and retry preparation.",
        @"timeout":@"The JIT helper exceeded its time limit. Reopen Cabrillo before retrying.",
        @"script":@"The JIT script failed. Reopen Cabrillo before retrying.", @"interrupted":@"The JIT helper stopped unexpectedly. Reopen Cabrillo before retrying.",
        @"launch":@"iOS could not launch the JIT helper. Keep and sign app extensions when installing, or choose another JIT provider."};
    if (!messages[code]) code = @"helper-response";
    NSString *message = messages[code] ?: @"Built-in StikJIT could not finish. Check pairing, Developer Mode, LocalDevVPN and extension signing; reopen Cabrillo before retrying.";
    NSNumber *deviceCode = response[@"deviceCode"], *subCode = response[@"deviceSubCode"];
    if (!success && [deviceCode isKindOfClass:NSNumber.class] && [subCode isKindOfClass:NSNumber.class] &&
        deviceCode.longLongValue >= INT32_MIN && deviceCode.longLongValue <= INT32_MAX && subCode.longLongValue >= INT32_MIN && subCode.longLongValue <= INT32_MAX)
        message = [message stringByAppendingFormat:@" Device error %@/%@.",deviceCode,subCode];
    if ([self.operation isEqual:@"reset"]) self.ddiReady = NO;
    if (success && ![self.operation isEqual:@"reset"]) { self.ddiReady = YES; self.serviceReady = YES; self.serviceChecked = YES; self.serviceCheckedAt = NSProcessInfo.processInfo.systemUptime; }
    if (success && ![self.operation isEqual:@"reset"]) [self scheduleServiceExpiry];
    if (!success) { self.ddiReady = NO; self.serviceReady = NO; }
    id txm = response[@"txmPresent"];
    if ([txm isKindOfClass:NSNumber.class] && CFGetTypeID((__bridge CFTypeRef)txm) == CFBooleanGetTypeID()) self.txm = @([txm boolValue]);
    void (^callback)(NSDictionary *) = self.completion;
    self.completion = nil; self.active = NO; self.phase = success ? @"ready" : @"failed"; self.message = message;
    [self stopNotifications]; self.extension = nil; self.extensionRequest = nil; self.operationID = nil; self.progressToken = nil;
    [self publish];
    if (callback) callback(@{@"success":@(success), @"error":success ? @"" : message, @"code":code, @"requestID":requestID ?: @""});
}

- (void)begin:(NSString *)operation pid:(pid_t)pid requestID:(NSString *)requestID script:(NSString *)script requiresScript:(BOOL)requiresScript completion:(void (^)(NSDictionary *))completion {
    if (!NSThread.isMainThread) { dispatch_async(dispatch_get_main_queue(), ^{ [self begin:operation pid:pid requestID:requestID script:script requiresScript:requiresScript completion:completion]; }); return; }
    NSString *problem = self.active ? @"A built-in JIT operation is already running." : [operation isEqual:@"reset"] ? [self availabilityError] : [self preflightError];
    if ([operation isEqual:@"enable"] && (pid != getpid() || requestID.length == 0 || requestID.length > 128 || (requiresScript && (script.length == 0 || [script lengthOfBytesUsingEncoding:NSUTF8StringEncoding] > 262144))))
        problem = @"The current-process JIT request is incomplete. Reopen Cabrillo and try again.";
    if (problem) {
        self.phase = @"failed"; self.message = problem; [self publish];
        if (completion) completion(@{@"success":@NO,@"error":problem,@"requestID":requestID ?: @"",@"code":@"preflight"});
        return;
    }
    if (!NSClassFromString(@"NSExtension")) dlopen("/System/Library/Frameworks/ExtensionFoundation.framework/ExtensionFoundation", RTLD_NOW | RTLD_LOCAL);
    Class extensionClass = NSClassFromString(@"NSExtension");
    SEL factory = NSSelectorFromString(@"extensionWithIdentifier:error:");
    id extension = nil;
    NSError *lookupError = nil;
    @try { if ([extensionClass respondsToSelector:factory]) extension = ((id(*)(id,SEL,id,NSError **))objc_msgSend)(extensionClass,factory,self.helperIdentifier,&lookupError); } @catch (__unused NSException *exception) {}
    NSArray<NSString *> *methods = @[@"beginExtensionRequestWithInputItems:completion:", @"setRequestCompletionBlock:", @"setRequestCancellationBlock:", @"setRequestInterruptionBlock:"];
    for (NSString *method in methods) if (![extension respondsToSelector:NSSelectorFromString(method)]) extension = nil;
    self.active = YES; self.timedOut = NO; self.operation = operation; self.operationID = requestID; self.completion = completion; self.generation++;
    self.phase = [operation isEqual:@"enable"] ? @"enabling" : [operation isEqual:@"reset"] ? @"resetting" : @"preparing";
    self.message = @"Starting Cabrillo’s JIT helper…"; self.progressToken = NSUUID.UUID.UUIDString;
    if (!extension) { [self finish:@{@"success":@NO,@"code":@"launch"}]; return; }
    self.extension = extension;
    [self watchdogForRequest:requestID after:1800];
    NSDictionary *stages = @{@"reachability":@"Checking the Remote Pairing endpoint…", @"ddi":@"Checking the Developer Disk Image…", @"download":@"Downloading the Developer Disk Image…", @"mount":@"Mounting the Developer Disk Image…", @"verify":@"Verifying the mounted Developer Disk Image…", @"prepared":@"Developer Disk Image ready…", @"debugging":@"Preparing Cabrillo’s JIT memory and waiting for detach…"};
    __weak typeof(self) weakSelf = self;
    NSString *progressToken = [self.progressToken copy];
    NSString *progressRequestID = [requestID copy];
    for (NSString *stage in stages) {
        NSString *name = [NSString stringWithFormat:@"org.cabrillo.jit.%@.%@",self.progressToken,stage]; int token = 0;
        if (notify_register_dispatch(name.UTF8String,&token,dispatch_get_main_queue(),^(__unused int value) {
            typeof(self) self = weakSelf;
            if (self.active && !self.timedOut && [self.progressToken isEqual:progressToken]) {
                self.message = stages[stage]; [self publish];
                if ([stage isEqual:@"debugging"]) [self watchdogForRequest:progressRequestID after:120];
            }
        }) == NOTIFY_STATUS_OK) [self.notificationTokens addObject:@(token)];
    }
    NSString *expectedID = [requestID copy];
    void (^returned)(NSUUID *,NSArray *) = ^(__unused NSUUID *identifier,NSArray *items) {
        dispatch_async(dispatch_get_main_queue(), ^{
            typeof(self) self = weakSelf; if (!self.active || ![self.operationID isEqual:expectedID]) return;
            id first = [items isKindOfClass:NSArray.class] ? items.firstObject : nil; id data = [first isKindOfClass:NSExtensionItem.class] ? ((NSExtensionItem *)first).userInfo[CJResponseKey] : nil;
            NSDictionary *response = [data isKindOfClass:NSData.class] && [data length] <= 4096 ? [NSJSONSerialization JSONObjectWithData:data options:0 error:NULL] : nil;
            if (![response isKindOfClass:NSDictionary.class] || ![response[@"requestID"] isEqual:expectedID]) response = @{@"success":@NO,@"code":@"helper-response"};
            [self finish:response];
        });
    };
    void (^cancelled)(NSUUID *,NSError *) = ^(__unused NSUUID *identifier,__unused NSError *error) { dispatch_async(dispatch_get_main_queue(), ^{ typeof(self) self = weakSelf; if ([self.operationID isEqual:expectedID]) [self finish:@{@"success":@NO,@"code":@"interrupted"}]; }); };
    void (^interrupted)(NSUUID *) = ^(NSUUID *identifier) { cancelled(identifier,nil); };
    ((void(*)(id,SEL,id))objc_msgSend)(extension,NSSelectorFromString(@"setRequestCompletionBlock:"),returned);
    ((void(*)(id,SEL,id))objc_msgSend)(extension,NSSelectorFromString(@"setRequestCancellationBlock:"),cancelled);
    ((void(*)(id,SEL,id))objc_msgSend)(extension,NSSelectorFromString(@"setRequestInterruptionBlock:"),interrupted);
    NSDictionary *payload = @{@"schema":@1,@"operation":operation,@"requestID":requestID,@"targetPID":@(pid),
        @"pairingBase64":[self.pairingData base64EncodedStringWithOptions:0] ?: @"", @"scriptBase64":[[script dataUsingEncoding:NSUTF8StringEncoding] base64EncodedStringWithOptions:0] ?: @"",
        @"requiresScript":@(requiresScript),@"progressToken":self.progressToken};
    NSData *data = [NSJSONSerialization dataWithJSONObject:payload options:0 error:NULL];
    if (!data || data.length > 2 * 1024 * 1024) { [self finish:@{@"success":@NO,@"code":@"helper-response"}]; return; }
    NSExtensionItem *item = [NSExtensionItem new]; item.userInfo = @{CJRequestKey:data};
    void (^started)(NSUUID *) = ^(NSUUID *identifier) { dispatch_async(dispatch_get_main_queue(), ^{ typeof(self) self = weakSelf; if (![self.operationID isEqual:expectedID]) return; if (!identifier) [self finish:@{@"success":@NO,@"code":@"launch"}]; else self.extensionRequest = identifier; }); };
    @try { ((void(*)(id,SEL,id,id))objc_msgSend)(extension,NSSelectorFromString(@"beginExtensionRequestWithInputItems:completion:"),@[item],started); }
    @catch (__unused NSException *exception) { [self finish:@{@"success":@NO,@"code":@"launch"}]; }
    [self publish];
}

- (void)dealloc { [self stopNotifications]; }
@end
