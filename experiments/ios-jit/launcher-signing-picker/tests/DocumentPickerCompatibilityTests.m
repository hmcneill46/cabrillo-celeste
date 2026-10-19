#import "CJDocumentPickerCompatibility.h"
#import <objc/runtime.h>
#import <objc/message.h>

static NSUInteger checks, rawCalls, previousHookCalls;
static char hostKey;
static void check(BOOL condition, NSString *name) {
    if (!condition) { fprintf(stderr, "FAIL %s\n", name.UTF8String); exit(1); }
    checks++;
}
static void RawSetter(id object, SEL selector, NSString *identifier) {
    (void)selector; rawCalls++;
    objc_setAssociatedObject(object, &hostKey, identifier, OBJC_ASSOCIATION_COPY_NONATOMIC);
}
static void ExistingHook(id object, SEL selector, NSString *identifier) {
    previousHookCalls++; RawSetter(object, selector, identifier);
}
static int WrongReturn(id object, SEL selector, NSString *identifier) {
    (void)object; (void)selector; (void)identifier; return 1;
}
static void SendHost(id object, NSString *identifier) {
    ((void (*)(id, SEL, id))objc_msgSend)(object, sel_registerName("setHostIdentifier:"), identifier);
}
static NSString *Host(id object) { return objc_getAssociatedObject(object, &hostKey); }
static Class Register(NSString *name, Class superclass, IMP setter, const char *encoding) {
    Class cls = objc_allocateClassPair(superclass, name.UTF8String, 0);
    check(cls != Nil, @"independent stub class created");
    if (setter) check(class_addMethod(cls, sel_registerName("setHostIdentifier:"), setter, encoding), @"stub setter added");
    objc_registerClassPair(cls); return cls;
}
static void Redacted(NSDictionary *status) {
    NSString *json = [[NSString alloc] initWithData:[NSJSONSerialization dataWithJSONObject:status options:0 error:NULL]
                                         encoding:NSUTF8StringEncoding];
    check(json.length > 0, @"status is JSON compatible");
    for (NSString *privateValue in @[@"OTHERPREFIX", @"com.cabrillo.original", @"com.signer.explicit"]) {
        check(![json containsString:privateValue], @"status omits signing identifiers");
    }
}
static void Policies(void) {
    for (id bad in @[@"", @"NODOT", @".com.test", @"PREFIX.", @"PREFIX.*", @"PREFIX.com.*", @"PREFIX.com..test",
                     @"PREFIX.com.test.", @"PREFIX.com/test", @"PREFIX. com.test", @"PREFIX.com.test\n", @"PRE-FIX.com.test",
                     @"PREFIX.com_tes", @"PREFIX.com.💾", NSNull.null, @YES, @123, @[], @{}]) {
        check(CJDocumentPickerSignedHostIdentifier(bad) == nil, @"malformed or nonstring entitlement rejected");
        check([CJDocumentPickerResolvedHostIdentifier(@"com.cabrillo.original", @"com.cabrillo.original", bad)
               isEqualToString:@"com.cabrillo.original"], @"invalid entitlement preserves requested host");
    }
    check(CJDocumentPickerSignedHostIdentifier(nil) == nil, @"missing entitlement rejected");
    check([CJDocumentPickerSignedHostIdentifier(@"OTHERPREFIX.com.signer.explicit") isEqualToString:@"com.signer.explicit"],
          @"App-ID prefix stripped independently of Team ID");
    check([CJDocumentPickerSignedHostIdentifier(@"P.single") isEqualToString:@"single"], @"nonempty single-component suffix supported");
    check([CJDocumentPickerSignedHostIdentifier(@"P.com.signer-name") isEqualToString:@"com.signer-name"], @"valid bundle hyphen supported");
    NSString *original = @"com.cabrillo.original";
    check([CJDocumentPickerResolvedHostIdentifier(original, original, @"OTHERPREFIX.com.signer.explicit")
           isEqualToString:@"com.signer.explicit"], @"only own original bundle request remapped");
    check(CJDocumentPickerResolvedHostIdentifier(original, original, @"P.com.cabrillo.original") == original,
          @"already matched identifier preserved");
    NSString *other = @"org.provider.existing-host";
    check(CJDocumentPickerResolvedHostIdentifier(other, original, @"P.com.signer.explicit") == other,
          @"another provider or earlier hook host preserved");
    check(CJDocumentPickerResolvedHostIdentifier(nil, original, @"P.com.signer.explicit") == nil, @"nil request preserved");
    check(CJDocumentPickerResolvedHostIdentifier(original, nil, @"P.com.signer.explicit") == original, @"missing bundle preserves host");
    check(CJDocumentPickerResolvedHostIdentifier(original, @"", @"P.com.signer.explicit") == original, @"empty bundle preserves host");
    check(CJDocumentPickerResolvedHostIdentifier((id)NSNull.null, original, @"P.com.signer.explicit") == (id)NSNull.null,
          @"nonstring runtime request preserved");
}
static void Runtime(NSString *scenario) {
    NSString *className = @"CJPickerConfigurationStub";
    NSString *bundle = @"com.cabrillo.original";
    id entitlement = @"OTHERPREFIX.com.signer.explicit";
    if ([scenario isEqual:@"real-entitlement"]) {
        NSDictionary *status = CJDocumentPickerCompatibilityPrepare();
        check([status[@"status"] isKindOfClass:NSString.class], @"optional real Security lookup returns status");
        Redacted(status); return;
    }
    if ([scenario isEqual:@"already-matched"]) entitlement = @"P.com.cabrillo.original";
    if ([scenario isEqual:@"invalid-entitlement"]) entitlement = @YES;
    if ([scenario isEqual:@"missing-bundle"]) bundle = nil;
    CJDocumentPickerCompatibilityTestEnvironment(bundle, entitlement, className, [scenario isEqual:@"livecontainer"]);
    if ([scenario isEqual:@"missing-class"]) {
        NSDictionary *missing = CJDocumentPickerCompatibilityPrepare();
        check([missing[@"status"] isEqual:@"configuration-class-unavailable"], @"missing runtime class leaves original path available");
        check(![missing[@"installed"] boolValue], @"missing class installs no hook"); Redacted(missing);
    }
    if ([scenario isEqual:@"inherited"]) {
        Class super = Register(@"CJPickerSuperclassStub", NSObject.class, (IMP)RawSetter, "v@:@");
        Class sub = Register(className, super, NULL, NULL);
        IMP before = method_getImplementation(class_getInstanceMethod(super, sel_registerName("setHostIdentifier:")));
        NSDictionary *status = CJDocumentPickerCompatibilityPrepare();
        check([status[@"installed"] boolValue], @"inherited setter supports local override");
        check(method_getImplementation(class_getInstanceMethod(super, sel_registerName("setHostIdentifier:"))) == before,
              @"superclass method remains untouched");
        id parent = [super new], child = [sub new]; SendHost(parent, bundle); SendHost(child, bundle);
        check([Host(parent) isEqual:bundle], @"superclass callers retain original behavior");
        check([Host(child) isEqual:@"com.signer.explicit"], @"subclass remaps its own host"); Redacted(status); return;
    }
    IMP implementation = (IMP)ExistingHook;
    const char *encoding = "v@:@";
    if ([scenario isEqual:@"missing-method"]) implementation = NULL;
    if ([scenario isEqual:@"bad-return"]) { implementation = (IMP)WrongReturn; encoding = "i@:@"; }
    if ([scenario isEqual:@"bad-argument"]) encoding = "v@:q";
    if ([scenario isEqual:@"bad-arity"]) encoding = "v@:";
    Class cls = Register(className, NSObject.class, implementation, encoding);
    NSDictionary *status = CJDocumentPickerCompatibilityPrepare(); Redacted(status);
    NSDictionary *expected = @{@"already-matched":@"already-matched", @"invalid-entitlement":@"entitlement-unavailable-or-invalid",
                               @"missing-bundle":@"bundle-identifier-unavailable", @"livecontainer":@"livecontainer-managed",
                               @"missing-method":@"configuration-setter-unavailable", @"bad-return":@"configuration-setter-incompatible",
                               @"bad-argument":@"configuration-setter-incompatible", @"bad-arity":@"configuration-setter-incompatible"};
    if (expected[scenario]) {
        check([status[@"status"] isEqual:expected[scenario]], @"fallback reports specific redacted reason");
        check(![status[@"installed"] boolValue], @"unsupported path installs no hook");
        if (![scenario isEqual:@"missing-method"]) {
            check(method_getImplementation(class_getInstanceMethod(cls, sel_registerName("setHostIdentifier:"))) == implementation,
                  @"fallback preserves existing IMP"); return;
        }
        check(class_addMethod(cls, sel_registerName("setHostIdentifier:"), (IMP)ExistingHook, "v@:@"), @"late runtime setter added");
        status = CJDocumentPickerCompatibilityPrepare();
        check([status[@"installed"] boolValue], @"setter availability can be retried");
    }
    check([status[@"installed"] boolValue], @"mismatched own identity installs compatibility");
    id object = [cls new];
    @autoreleasepool { SendHost(object, [NSString stringWithFormat:@"%@", bundle]); }
    check([Host(object) isEqual:@"com.signer.explicit"], @"runtime setter receives own signed host after autorelease drain");
    check(rawCalls == 1 && previousHookCalls == 1, @"existing hook and original each invoked exactly once");
    SendHost(object, @"org.provider.existing-host");
    check([Host(object) isEqual:@"org.provider.existing-host"], @"runtime leaves unrelated host requests alone");
    SendHost(object, nil); check(Host(object) == nil, @"runtime nil forwarded unchanged");
    IMP installed = method_getImplementation(class_getInstanceMethod(cls, sel_registerName("setHostIdentifier:")));
    for (NSUInteger i = 0; i < 100; i++) check([CJDocumentPickerCompatibilityPrepare()[@"installed"] boolValue], @"repeated prepare remains installed");
    check(method_getImplementation(class_getInstanceMethod(cls, sel_registerName("setHostIdentifier:"))) == installed,
          @"repeated preparation never chains to itself");
    SendHost(object, bundle);
    check(rawCalls == 4 && previousHookCalls == 4, @"repeat installation preserves nonrecursive original chain");
}
int main(int argc, char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
        Policies(); Runtime(@(argv[1])); printf("PASS %lu document picker controls (%s)\n", (unsigned long)checks, argv[1]);
    }
    return 0;
}
