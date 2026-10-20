#import "CJDocumentPickerCompatibility.h"
#import <CoreFoundation/CoreFoundation.h>
#import <dispatch/dispatch.h>
#import <objc/runtime.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>

// This narrow Documents UI adaptation leaves the bundle, process identity,
// signing entitlements, JIT acquisition and all other framework calls alone.
@interface CJDocumentPickerCompatibilityLock : NSObject @end
@implementation CJDocumentPickerCompatibilityLock @end

static IMP gPreviousSetter;
static NSString *gOriginalBundleIdentifier;
static NSString *gApplicationIdentifier;
static BOOL gInstalled;

#if defined(CJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING)
static BOOL gTestConfigured;
static NSString *gTestBundleIdentifier;
static id gTestApplicationIdentifier;
static NSString *gTestClassName;
static BOOL gTestLiveContainer;
void CJDocumentPickerCompatibilityTestEnvironment(NSString *bundleIdentifier, id applicationIdentifier,
                                                 NSString *className, BOOL liveContainer) {
    NSCAssert(!gInstalled && !gTestConfigured, @"Configure a fresh test process once");
    gTestBundleIdentifier = [bundleIdentifier copy];
    gTestApplicationIdentifier = applicationIdentifier;
    gTestClassName = [className copy];
    gTestLiveContainer = liveContainer;
    gTestConfigured = YES;
}
#endif

static BOOL CJIdentifierPartIsValid(NSString *part, BOOL prefix) {
    if (!part.length) return NO;
    for (NSUInteger index = 0; index < part.length; index++) {
        unichar c = [part characterAtIndex:index];
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) continue;
        if (!prefix && c == '-') continue;
        return NO;
    }
    return YES;
}

NSString *CJDocumentPickerSignedHostIdentifier(id applicationIdentifier) {
    if (![applicationIdentifier isKindOfClass:NSString.class]) return nil;
    NSString *identifier = applicationIdentifier;
    NSRange firstDot = [identifier rangeOfString:@"."];
    if (firstDot.location == NSNotFound || firstDot.location == 0 || firstDot.location == identifier.length - 1) return nil;
    if (!CJIdentifierPartIsValid([identifier substringToIndex:firstDot.location], YES)) return nil;
    NSString *suffix = [identifier substringFromIndex:firstDot.location + 1];
    for (NSString *part in [suffix componentsSeparatedByString:@"."]) {
        if (!CJIdentifierPartIsValid(part, NO)) return nil;
    }
    // App-ID prefixes need not equal a Team ID; strip exactly the first part.
    return [suffix copy];
}

NSString *CJDocumentPickerResolvedHostIdentifier(NSString *requestedIdentifier, NSString *bundleIdentifier,
                                                id applicationIdentifier) {
    if (![requestedIdentifier isKindOfClass:NSString.class] || ![bundleIdentifier isKindOfClass:NSString.class] ||
        !bundleIdentifier.length || ![requestedIdentifier isEqualToString:bundleIdentifier]) return requestedIdentifier;
    NSString *signedHost = CJDocumentPickerSignedHostIdentifier(applicationIdentifier);
    if (!signedHost || [signedHost isEqualToString:bundleIdentifier]) return requestedIdentifier;
    return signedHost;
}

static id CJOwnApplicationIdentifier(BOOL *apiAvailable) {
    typedef CFTypeRef (*CreateTaskFunction)(CFAllocatorRef);
    typedef CFTypeRef (*CopyEntitlementFunction)(CFTypeRef, CFStringRef, CFErrorRef *);
    static CreateTaskFunction createTask;
    static CopyEntitlementFunction copyEntitlement;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        // SPI lookup remains optional so older systems still load the app.
        void *security = dlopen("/System/Library/Frameworks/Security.framework/Security", RTLD_LAZY | RTLD_LOCAL);
        createTask = (CreateTaskFunction)dlsym(security ? security : RTLD_DEFAULT, "SecTaskCreateFromSelf");
        copyEntitlement = (CopyEntitlementFunction)dlsym(security ? security : RTLD_DEFAULT, "SecTaskCopyValueForEntitlement");
    });
    *apiAvailable = createTask && copyEntitlement;
    if (!*apiAvailable) return nil;
    CFTypeRef task = createTask(kCFAllocatorDefault);
    if (!task) return nil;
    CFErrorRef error = NULL;
    CFTypeRef value = copyEntitlement(task, CFSTR("application-identifier"), &error);
    CFRelease(task);
    if (error) CFRelease(error);
    // Transfer ownership before inspecting the object; no dangling CF bridge.
    return value ? CFBridgingRelease(value) : nil;
}

static Class CJDocumentConfigurationClass(void) {
#if defined(CJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING)
    // Synthetic host tests use their own classes. A UIKit fixture naming the
    // real class must exercise the same first-picker discovery path as iOS.
    if (gTestConfigured && ![gTestClassName isEqualToString:@"DOCConfiguration"]) return NSClassFromString(gTestClassName);
#endif
    Class configuration = NSClassFromString(@"DOCConfiguration");
    if (configuration) return configuration;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        // Framework placement varies by iOS release. Keep loaded images alive;
        // a missing image/class simply leaves Apple's original path in use.
        (void)dlopen("/System/Library/PrivateFrameworks/DocumentManagerCore.framework/DocumentManagerCore", RTLD_LAZY | RTLD_LOCAL);
        (void)dlopen("/System/Library/PrivateFrameworks/DocumentManager.framework/DocumentManager", RTLD_LAZY | RTLD_LOCAL);
    });
    return NSClassFromString(@"DOCConfiguration");
}

static NSDictionary *CJPickerStatus(NSString *status, BOOL needed, BOOL valid, BOOL available) {
    return @{@"status":status, @"installed":@(gInstalled), @"needed":@(needed),
             @"entitlement_valid":@(valid), @"runtime_available":@(available)};
}

static void CJSetDocumentHostIdentifier(id object, SEL selector, NSString *requestedIdentifier) {
    NSString *resolved = CJDocumentPickerResolvedHostIdentifier(requestedIdentifier, gOriginalBundleIdentifier,
                                                               gApplicationIdentifier);
    ((void (*)(id, SEL, NSString *))gPreviousSetter)(object, selector, resolved);
}

NSDictionary<NSString *, id> *CJDocumentPickerCompatibilityPrepare(void) {
    @synchronized(CJDocumentPickerCompatibilityLock.class) {
        if (gInstalled) return CJPickerStatus(@"installed", YES, YES, YES);
        BOOL liveContainer = getenv("LC_HOME_PATH") != NULL;
        NSString *bundle = NSBundle.mainBundle.bundleIdentifier;
        id applicationIdentifier = nil;
        BOOL apiAvailable = NO;
#if defined(CJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING)
        if (gTestConfigured) {
            liveContainer = gTestLiveContainer;
            bundle = gTestBundleIdentifier;
            applicationIdentifier = gTestApplicationIdentifier;
            apiAvailable = YES;
        } else
#endif
        if (!liveContainer) applicationIdentifier = CJOwnApplicationIdentifier(&apiAvailable);
        // LiveContainer supplies its own host-aware adaptation. Do not layer a
        // standalone guest hook over its accepted file-picker implementation.
        if (liveContainer) return CJPickerStatus(@"livecontainer-managed", NO, NO, NO);
        NSString *signedHost = CJDocumentPickerSignedHostIdentifier(applicationIdentifier);
        if (!apiAvailable) return CJPickerStatus(@"entitlement-api-unavailable", NO, NO, NO);
        if (!signedHost) return CJPickerStatus(@"entitlement-unavailable-or-invalid", NO, NO, NO);
        if (!bundle.length) return CJPickerStatus(@"bundle-identifier-unavailable", NO, YES, NO);
        if ([signedHost isEqualToString:bundle]) return CJPickerStatus(@"already-matched", NO, YES, NO);

        Class configuration = CJDocumentConfigurationClass();
        if (!configuration) return CJPickerStatus(@"configuration-class-unavailable", YES, YES, NO);
        SEL setter = sel_registerName("setHostIdentifier:");
        Method method = class_getInstanceMethod(configuration, setter);
        if (!method) return CJPickerStatus(@"configuration-setter-unavailable", YES, YES, NO);
        char *returnType = method_copyReturnType(method);
        char *argumentType = method_getNumberOfArguments(method) == 3 ? method_copyArgumentType(method, 2) : NULL;
        BOOL compatible = returnType && strcmp(returnType, @encode(void)) == 0 && argumentType && argumentType[0] == '@';
        free(returnType); free(argumentType);
        if (!compatible) return CJPickerStatus(@"configuration-setter-incompatible", YES, YES, NO);

        gPreviousSetter = method_getImplementation(method);
        if (!gPreviousSetter) return CJPickerStatus(@"configuration-setter-unavailable", YES, YES, NO);
        gOriginalBundleIdentifier = [bundle copy];
        gApplicationIdentifier = [applicationIdentifier copy];
        // Add a local override for inherited methods instead of changing their
        // superclass. Existing local hooks are chained through their saved IMP.
        if (!class_addMethod(configuration, setter, (IMP)CJSetDocumentHostIdentifier, method_getTypeEncoding(method))) {
            gPreviousSetter = method_setImplementation(method, (IMP)CJSetDocumentHostIdentifier);
        }
        gInstalled = YES;
        return CJPickerStatus(@"installed", YES, YES, YES);
    }
}
