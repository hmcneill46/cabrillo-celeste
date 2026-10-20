#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

// These helpers never consult a profile or trust identifiers supplied by a file.
// Only Prepare reads the running process's own signed entitlement.
FOUNDATION_EXPORT NSString * _Nullable CJDocumentPickerSignedHostIdentifier(id _Nullable applicationIdentifier);
FOUNDATION_EXPORT NSString * _Nullable CJDocumentPickerResolvedHostIdentifier(NSString * _Nullable requestedIdentifier,
                                                                            NSString * _Nullable bundleIdentifier,
                                                                            id _Nullable applicationIdentifier);

// Call immediately before constructing a document picker. Retrying is safe if
// the private configuration class was not available on the first attempt.
// The result contains status codes/booleans only, never signing identifiers.
FOUNDATION_EXPORT NSDictionary<NSString *, id> *CJDocumentPickerCompatibilityPrepare(void);

#if defined(CJ_DOCUMENT_PICKER_COMPATIBILITY_TESTING)
// Host-test seam; absent from device builds. Configure once before Prepare.
FOUNDATION_EXPORT void CJDocumentPickerCompatibilityTestEnvironment(NSString * _Nullable bundleIdentifier,
                                                                   id _Nullable applicationIdentifier,
                                                                   NSString *className,
                                                                   BOOL liveContainer);
#endif

NS_ASSUME_NONNULL_END
